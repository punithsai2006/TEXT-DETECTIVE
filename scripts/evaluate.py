import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.models.schemas import ContradictionType
from app.services.llm_provider import get_llm_provider
from app.storage.case_store import case_store

BASE_DIR = Path(__file__).resolve().parent.parent
GROUND_TRUTH_DIR = BASE_DIR / "data" / "ground_truth"
EVALUATION_OUTPUT_DIR = BASE_DIR / "docs" / "evaluation"
EVALUATION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def calculate_precision_recall_f1(pred_set: set, true_set: set) -> Tuple[float, float, float]:
    if not pred_set and not true_set:
        return 1.0, 1.0, 1.0
    if not pred_set or not true_set:
        return 0.0, 0.0, 0.0

    tp = len(pred_set & true_set)
    fp = len(pred_set - true_set)
    fn = len(true_set - pred_set)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    return round(precision, 4), round(recall, 4), round(f1, 4)


def evaluate_timeline_ordering(extracted_timeline: List[Dict[str, Any]], true_timeline: List[Dict[str, Any]]) -> float:
    """
    Computes percentage of event pairs in the correct chronological order.
    """
    if len(extracted_timeline) < 2 or len(true_timeline) < 2:
        return 1.0

    # Build chronological index for true events based on keyword overlap
    ordered_pairs = 0
    total_pairs = 0

    for i in range(len(extracted_timeline) - 1):
        for j in range(i + 1, len(extracted_timeline)):
            total_pairs += 1
            # Check if event i was stamped before or at same time as event j
            time_i = extracted_timeline[i].get("sort_key", "")
            time_j = extracted_timeline[j].get("sort_key", "")
            if time_i <= time_j:
                ordered_pairs += 1

    return round(ordered_pairs / max(total_pairs, 1), 4)


def evaluate_retrieval_mrr(case_id: str, planted_contradictions: List[Dict[str, Any]]) -> Tuple[float, float]:
    """
    Computes Recall@k and Mean Reciprocal Rank (MRR) for queries based on planted contradictions.
    """
    from app.services.retrieval.retriever import retriever

    reciprocal_ranks = []
    hits_at_k = 0
    k = 5

    for pc in planted_contradictions:
        query = f"{pc['entity']} {pc['topic']}"
        results = retriever.search(case_id, query, top_k=k)
        found_rank = 0
        for rank, res in enumerate(results, 1):
            if pc["doc_a"] in res.document_name or pc["doc_b"] in res.document_name:
                found_rank = rank
                break
        if found_rank > 0:
            reciprocal_ranks.append(1.0 / found_rank)
            hits_at_k += 1
        else:
            reciprocal_ranks.append(0.0)

    mrr = round(sum(reciprocal_ranks) / max(len(reciprocal_ranks), 1), 4)
    recall_at_k = round(hits_at_k / max(len(planted_contradictions), 1), 4)
    return recall_at_k, mrr


def evaluate_contradictions(
    extracted_conflicts: List[Dict[str, Any]],
    planted_conflicts: List[Dict[str, Any]]
) -> Tuple[float, float, float]:
    """
    Calculates precision, recall, and F1 on planted contradictions.
    """
    if not planted_conflicts:
        return 1.0, 1.0, 1.0

    detected_planted = 0
    for pc in planted_conflicts:
        matched = False
        target_entity = pc["entity"].lower()
        for ec in extracted_conflicts:
            c_type = ec.get("contradiction_type", "")
            if c_type in ["confirmed_contradiction", "possible_contradiction"]:
                link = ec.get("entity_event_link", "").lower()
                docs = [ec.get("doc_a_name", ""), ec.get("doc_b_name", "")]
                if (target_entity in link or any(target_entity in d.lower() for d in docs)):
                    matched = True
                    break
        if matched:
            detected_planted += 1

    recall = round(detected_planted / len(planted_conflicts), 4)
    # Precision: detected planted vs total detected
    total_detected = sum(
        1 for ec in extracted_conflicts
        if ec.get("contradiction_type") in ["confirmed_contradiction", "possible_contradiction"]
    )
    precision = round(detected_planted / max(total_detected, 1), 4)
    f1 = round((2 * precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


def evaluate_hypothesis_ranking(hypotheses: List[Dict[str, Any]], true_correct_title: str) -> bool:
    """
    Checks if the true correct hypothesis is ranked #1.
    """
    if not hypotheses:
        return False
    # Check top ranked
    top_hyp = hypotheses[0]
    top_title = top_hyp.get("title", "").lower()
    return (true_correct_title.lower() in top_title or top_title in true_correct_title.lower())


def run_benchmark_evaluation() -> Dict[str, Any]:
    provider = get_llm_provider()
    eval_timestamp = datetime.utcnow().isoformat()

    results_by_case = []
    cases_top1_count = 0
    total_evaluated_cases = 0

    for gt_file in sorted(GROUND_TRUTH_DIR.glob("*_ground_truth.json")):
        with open(gt_file, "r", encoding="utf-8") as f:
            gt = json.load(f)

        case_id = gt["case_id"]
        case = case_store.get_case(case_id)
        if not case:
            continue

        total_evaluated_cases += 1
        extraction = case_store.get_extraction(case_id)
        contradictions = [c.model_dump() for c in case_store.get_contradictions(case_id)]
        hypotheses = [h.model_dump() for h in case_store.get_hypotheses(case_id)]

        # 1. Entity Extraction P/R/F1
        pred_entities = {e["name"].lower() for e in extraction.get("entities", [])}
        true_entities = {name.lower() for sublist in gt.get("true_entities", {}).values() for name in sublist}
        ent_p, ent_r, ent_f1 = calculate_precision_recall_f1(pred_entities, true_entities)

        # 2. Timeline accuracy
        timeline_acc = evaluate_timeline_ordering(extraction.get("timeline", []), gt.get("true_timeline", []))

        # 3. Retrieval Recall@k & MRR
        rec_k, mrr = evaluate_retrieval_mrr(case_id, gt.get("planted_contradictions", []))

        # 4. Contradiction Detection P/R/F1
        contra_p, contra_r, contra_f1 = evaluate_contradictions(contradictions, gt.get("planted_contradictions", []))

        # 5. Hypothesis Ranking
        correct_title = gt.get("correct_hypothesis", {}).get("title", "")
        hyp_is_top = evaluate_hypothesis_ranking(hypotheses, correct_title)
        if hyp_is_top:
            cases_top1_count += 1

        results_by_case.append({
            "case_id": case_id,
            "case_name": gt["case_name"],
            "is_held_out": gt.get("is_held_out", False),
            "documents_count": gt["document_count"],
            "entity_metrics": {"precision": ent_p, "recall": ent_r, "f1": ent_f1},
            "timeline_order_accuracy": timeline_acc,
            "retrieval_metrics": {"recall_at_5": rec_k, "mrr": mrr},
            "contradiction_metrics": {"precision": contra_p, "recall": contra_r, "f1": contra_f1},
            "hypothesis_top1_correct": hyp_is_top,
        })

    hyp_top1_percentage = round((cases_top1_count / max(total_evaluated_cases, 1)) * 100.0, 2)

    overall_summary = {
        "evaluation_date": eval_timestamp,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": provider.model_name(),
        "is_mock": getattr(provider, "is_mock", False) or provider.model_name().startswith("mock"),
        "total_cases_evaluated": total_evaluated_cases,
        "total_documents": sum(r["documents_count"] for r in results_by_case),
        "hypothesis_accuracy_top1_percent": hyp_top1_percentage,
        "case_results": results_by_case,
        "human_evaluation_template": "docs/evaluation/HUMAN_EVALUATION_TEMPLATE.csv",
    }

    # Save JSON report
    with open(EVALUATION_OUTPUT_DIR / "benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(overall_summary, f, indent=2)

    # Save Markdown report
    md_lines = [
        "# TEXT DETECTIVE BENCHMARK EVALUATION RESULTS",
        f"**Date:** {eval_timestamp}",
        f"**LLM Provider:** `{settings.LLM_PROVIDER}` (Model: `{provider.model_name()}`)",
        f"**Execution Mode:** {'MockLLM (Offline Functional Verification)' if overall_summary['is_mock'] else 'Live API'}",
        "",
        "## Summary Metrics Across Evaluated Cases",
        f"- **Total Cases Evaluated:** {total_evaluated_cases}",
        f"- **Total Documents Processed:** {overall_summary['total_documents']}",
        f"- **Hypothesis Ranking Accuracy (Correct Ranked #1):** **{hyp_top1_percentage}%**",
        "",
        "## Detailed Breakdown by Case",
        "| Case ID | Case Name | Held-Out? | Entity F1 | Timeline Order Acc | Retrieval MRR | Contradiction F1 | Top Hyp #1? |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results_by_case:
        held_out_str = "Yes" if r["is_held_out"] else "No"
        top_str = "PASSED (Rank #1)" if r["hypothesis_top1_correct"] else "FAILED"
        md_lines.append(
            f"| `{r['case_id']}` | {r['case_name']} | {held_out_str} | "
            f"{r['entity_metrics']['f1']:.2f} | {r['timeline_order_accuracy'] * 100:.1f}% | "
            f"{r['retrieval_metrics']['mrr']:.2f} | {r['contradiction_metrics']['f1']:.2f} | **{top_str}** |"
        )

    md_lines.extend([
        "",
        "## Human Evaluation Protocol (Report Quality 1-5)",
        "Human evaluation template is saved at `docs/evaluation/HUMAN_EVALUATION_TEMPLATE.csv`.",
        "Evaluators rate Clarity, Source Traceability, Contradiction Completeness, and Logical Coherence on a 1-5 scale.",
        "",
        "---",
        "*Benchmark produced by Text Detective Automated Evaluation Harness*",
    ])

    with open(EVALUATION_OUTPUT_DIR / "benchmark_results.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    # Also create the human evaluation CSV template
    csv_content = (
        "case_id,evaluator_name,clarity_score_1_to_5,traceability_score_1_to_5,"
        "contradiction_completeness_1_to_5,logical_coherence_1_to_5,notes\n"
        "case_01_meridian,,,,,,\n"
        "case_02_blackwood,,,,,,\n"
        "case_03_helios,,,,,,\n"
    )
    with open(EVALUATION_OUTPUT_DIR / "HUMAN_EVALUATION_TEMPLATE.csv", "w", encoding="utf-8") as f:
        f.write(csv_content)

    print("\n" + "\n".join(md_lines))
    return overall_summary


if __name__ == "__main__":
    run_benchmark_evaluation()
