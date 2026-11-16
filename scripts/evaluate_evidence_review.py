"""Small labelled alignment pilot plus optional actual-model end-to-end evaluation.

Gold labels stay in this script, outside every ingestion/retrieval path. The
default checks deterministic safeguards only; it does NOT score scripted LLMs.
"""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from app.models.evidence_review import Claim
from app.services.orchestration.evidence_review import EvidenceReviewService, precheck
from app.services.ingestion.preprocessor import process_uploaded_file
from app.services.llm_provider import get_llm_provider
from app.services.retrieval.retriever import HybridRetriever
from app.storage.case_store import CaseStore


def claim(obj="locked", **changes):
    return {"subject": "archive door", "predicate": "state", "object": obj,
            "polarity": "positive", "entity_identity": "explicit", "source_span_ids": ["gold_only"],
            "event_scope": "door observation", "event_start": "2026-11-01T20:00:00+00:00",
            "timezone": "UTC", "precision": "minute", **changes}


# Frozen pilot cases; held-out marks reserve cases for checking, not evidence of
# independence from development in this session. A genuinely unseen corpus is still needed.
CASES = [
    {"id": "direct", "split": "development", "texts": ["At 20:00 UTC on 1 November 2026 the archive door was locked.", "At 20:00 UTC on 1 November 2026 the archive door was open."],
     "claims": [claim(), claim("open")], "outcome": "POTENTIAL_CONTRADICTION", "rule": None},
    {"id": "compatible", "split": "development", "texts": ["The archive door was locked at 20:00 UTC on 1 November 2026.", "The archive door was locked at 20:00 UTC on 1 November 2026."],
     "claims": [claim(), claim()], "outcome": "COMPATIBLE", "rule": None},
    {"id": "approximate", "split": "development", "texts": ["The archive door was locked around 20:00 UTC on 1 November 2026.", "The archive door was locked at 20:04 UTC on 1 November 2026."],
     "claims": [claim(approximate=True, precision="approximate"), claim(event_start="2026-11-01T20:04:00+00:00")], "outcome": "COMPATIBLE", "rule": None},
    {"id": "identity", "split": "development", "texts": ["A. Rao says the archive door was locked.", "Anita Rao says the archive door was open."],
     "claims": [claim(subject="A. Rao", entity_identity="ambiguous"), claim("open", subject="Anita Rao")], "outcome": "INSUFFICIENT_EVIDENCE", "rule": "INSUFFICIENT_EVIDENCE"},
    {"id": "hearsay", "split": "development", "texts": ["Meera was told that the archive door was locked.", "Ravi reported that the archive door was open."],
     "claims": [claim(attribution="hearsay", event_start=None), claim("open", event_start=None)], "outcome": "INSUFFICIENT_EVIDENCE", "rule": None},
    {"id": "units", "split": "development", "texts": ["The sample mass was 1 kg.", "The sample mass was 1000 g."],
     "claims": [claim(subject="sample", predicate="mass", obj="1 kg", quantity=1, unit="kg"), claim(subject="sample", predicate="mass", obj="1000 g", quantity=1000, unit="g")], "outcome": "COMPATIBLE", "rule": "COMPATIBLE"},
    {"id": "missing", "split": "development", "texts": ["The archive door was locked.", "The room lights were on."],
     "claims": [claim(event_start=None), claim("on", subject="room lights", event_start=None)], "outcome": "INSUFFICIENT_EVIDENCE", "rule": "INSUFFICIENT_EVIDENCE"},
    {"id": "within_document", "split": "development", "within": True, "texts": ["At 20:00 UTC on 1 November 2026 the archive door was locked.", "At 20:00 UTC on 1 November 2026 the archive door was not locked."],
     "claims": [claim(), claim(polarity="negative")], "outcome": "POTENTIAL_CONTRADICTION", "rule": None},
    {"id": "separate_events", "split": "reserved_pilot", "texts": ["The van arrived at 09:00.", "The van departed at 09:20."],
     "claims": [claim(subject="van", event_scope="arrival"), claim(subject="van", event_scope="departure")], "outcome": "EXPLAINABLE_VARIANCE", "rule": "EXPLAINABLE_VARIANCE"},
    {"id": "unknown_timezone", "split": "reserved_pilot", "texts": ["The archive door was locked at 20:00 local time.", "The archive door was open at 20:00 UTC."],
     "claims": [claim(timezone=None), claim("open")], "outcome": "INSUFFICIENT_EVIDENCE", "rule": "INSUFFICIENT_EVIDENCE"},
    {"id": "non_observation", "split": "reserved_pilot", "texts": ["I did not see Ravi enter the archive.", "Ravi entered the archive."],
     "claims": [claim(subject="witness", predicate="observe", obj="Ravi entering", polarity="negative"), claim(subject="Ravi", predicate="enter", obj="archive")], "outcome": "COMPATIBLE", "rule": "INSUFFICIENT_EVIDENCE"},
    {"id": "question", "split": "reserved_pilot", "texts": ["Was the archive door locked?", "The archive door was open."],
     "claims": [claim(attribution="question"), claim("open")], "outcome": "INSUFFICIENT_EVIDENCE", "rule": "INSUFFICIENT_EVIDENCE"},
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real", action="store_true", help="Run actual configured provider; may incur provider usage")
    parser.add_argument("--output", default=str(ROOT / "docs/evaluation/evidence_review_results.json"))
    args = parser.parse_args()
    report = {"dataset": "12 manually labelled pilot pairs; development/reserved pilot only, not an unseen benchmark",
              "matching_policy": "Rule checks: exact expected safeguard outcome or defer. Real run: any potential contradiction for the one labelled pair per case; missing comparison counts as not flagged.",
              "mode": "real" if args.real else "deterministic_safeguards_only", "cases": []}
    for case in CASES:
        result = precheck(*(Claim(**c) for c in case["claims"]))
        predicted = result.outcome.value if result else None
        report["cases"].append({"case_id": case["id"], "split": case["split"], "rule_outcome": predicted,
                                 "expected_safeguard": case["rule"], "safeguard_correct": predicted == case["rule"],
                                 "gold_contextual_outcome": case["outcome"]})
    report["safeguards"] = {"passed": sum(c["safeguard_correct"] for c in report["cases"]),
                             "total": len(CASES), "deferred_to_contextual_judge": sum(c["rule_outcome"] is None for c in report["cases"])}
    report["model_metrics"] = None
    if args.real:
        provider = get_llm_provider()
        report["provider_model"] = provider.model_name()
        if provider.is_mock or not provider.is_available():
            report["real_model_status"] = "blocked: configure an available non-mock provider; no fixture metrics substituted"
        else:
            tp = fp = fn = 0
            with tempfile.TemporaryDirectory(prefix="text-detective-real-evaluation-") as folder:
                store = CaseStore(Path(folder) / "storage")
                retrieval = HybridRetriever(Path(folder) / "index")
                # Reproducible lexical baseline; dense/graph ablations require a separate controlled study.
                retrieval._model_load_attempted = True
                service = EvidenceReviewService(store, retrieval, lambda: provider)
                for case, record in zip(CASES, report["cases"]):
                    cid = store.create_case(case["id"]).case_id
                    texts = ["\n\n".join(case["texts"])] if case.get("within") else case["texts"]
                    for i, text in enumerate(texts):
                        path = Path(folder) / f"source_{case['id']}_{i}.txt"
                        path.write_text(text, encoding="utf-8")
                        store.add_document(cid, process_uploaded_file(cid, path, path.name))
                    run = service.run(cid)
                    predicted = any(c["outcome"] == "POTENTIAL_CONTRADICTION" for c in run["comparisons"])
                    expected = case["outcome"] == "POTENTIAL_CONTRADICTION"
                    tp += predicted and expected
                    fp += predicted and not expected
                    fn += not predicted and expected
                    record.update({"status": run["status"], "failures": run["failures"],
                                   "flagged": predicted, "claim_count": len(run["claims"]),
                                   "model_calls": run["model_calls"], "latency_seconds": run["elapsed_seconds"],
                                   "usage": run["usage"], "cost": None})
            precision = tp / (tp + fp) if tp + fp else None
            recall = tp / (tp + fn) if tp + fn else None
            report["real_model_status"] = "executed"
            report["model_metrics"] = {"tp": tp, "fp": fp, "fn": fn,
                                       "precision": precision, "recall": recall,
                                       "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
                                       "case_pairs": len(CASES)}
    report["not_measured"] = ["real extraction/entity F1", "human-labelled answer support", "retrieval Recall@k",
                              "timeline comparable-pair accuracy", "real-model injection resilience", "controlled ablations"]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"safeguards": report["safeguards"], "real_model_status": report.get("real_model_status", "not requested"),
                      "model_metrics": report["model_metrics"], "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
