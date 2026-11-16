"""Measure actual retrieval/citation mechanics with isolated labelled fixtures.

This intentionally does NOT report scripted model decisions as model accuracy.
Use evaluate_evidence_review.py --real for configured real-model contradiction
evaluation; missing credentials produce blocked/null metrics, never substitutions.
"""
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "tests"))
from app.models.schemas import EvidenceSearchRequest
from app.services.ingestion.preprocessor import process_uploaded_file
from app.services.orchestration.evidence_review import EvidenceReviewService
from app.services.orchestration.integrated_pipeline import run_pipeline
from app.services.retrieval.retriever import HybridRetriever
from app.services.retrieval.case_search import search_case
from app.storage.case_store import CaseStore
from evidence_fixtures import DOOR_A, DOOR_B, door_provider


def main():
    with tempfile.TemporaryDirectory(prefix="text-detective-workflow-eval-") as temp:
        store = CaseStore(Path(temp) / "storage")
        retriever = HybridRetriever(Path(temp) / "index")
        retriever._model_load_attempted = True
        provider = door_provider()
        class FixtureService(EvidenceReviewService):
            def run(self, cid): return super().run(cid, allow_fixture=True)
        service = FixtureService(store, retriever, lambda: provider)
        cid = store.create_case("Isolated fixture mechanics evaluation").case_id
        for name, text in [("guard.txt", DOOR_A), ("maintenance.txt", DOOR_B)]:
            folder = store.uploads_dir / cid
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / name
            path.write_text(text, encoding="utf-8")
            store.add_document(cid, process_uploaded_file(cid, path, name))
        started = time.monotonic()
        report = run_pipeline(service, cid)
        duration = time.monotonic() - started
        results = []
        # These relevance labels never enter uploaded files or the retrieval index.
        for query, relevant in [("archive door locked", DOOR_A), ("archive door open", DOOR_B)]:
            matches = search_case(service, cid, EvidenceSearchRequest(query=query, top_k=1))
            results.append({"query": query, "relevant_count": 1,
                            "retrieved_relevant_at_1": int(any(m.text == relevant for m in matches))})
        checks = [service.cite(cid, ref["chunk_id"]) for ref in report.source_references]
        output = {"mode": "fixture_mechanics_only", "case_count": 1, "document_count": 2,
                  "retrieval": {"method": "lexical_tfidf_bm25", "queries": results,
                    "recall_at_1_numerator": sum(r["retrieved_relevant_at_1"] for r in results),
                    "recall_at_1_denominator": len(results),
                    "recall_at_1": sum(r["retrieved_relevant_at_1"] for r in results) / len(results)},
                  "citation_locator_validity": {"passed": sum(c["locator_valid"] for c in checks), "total": len(checks)},
                  "quotation_accuracy": {"passed": sum(c["quotation_accurate"] for c in checks), "total": len(checks)},
                  "fixture_pipeline_latency_seconds": round(duration, 3),
                  "fixture_provider_calls": len(provider.prompts), "real_model_usage": None, "cost": None,
                  "real_contradiction_precision": None, "real_contradiction_recall": None,
                  "real_semantic_support_accuracy": None,
                  "limitations": ["One tiny synthetic mechanics case, not an unseen model benchmark.",
                                  "Scripted hypothesis/verification results are not accuracy measurements.",
                                  "No real-model latency, semantic support or cost was measured."]}
        path = ROOT / "docs" / "evaluation" / "case_workflow_results.json"
        path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
