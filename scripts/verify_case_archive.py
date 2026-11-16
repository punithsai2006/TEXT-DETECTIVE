"""Reproduce archive ingestion/search and optional analysis without answer leakage.

Default mode is deterministic inspection. --offline-preview explicitly exercises
the full UI contracts with quotations only, not semantic reasoning accuracy.
--real uses configured credentials; unavailable providers produce blocked metrics.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from app.models.schemas import EvidenceSearchRequest
from app.services.ingestion.preprocessor import process_uploaded_file
from app.services.llm_provider import get_llm_provider
from app.services.offline_preview import OfflinePreviewProvider
from app.services.orchestration.evidence_review import EvidenceReviewService
from app.services.orchestration.integrated_pipeline import run_pipeline
from app.services.provider_readiness import provider_readiness
from app.services.retrieval.case_search import search_case
from app.services.retrieval.retriever import HybridRetriever
from app.services.reporting.evidence_report import markdown_report, pdf_report
from app.storage.case_store import CaseStore
from app.config import settings


def evidence_members(archive):
    total = 0
    names = []
    for item in archive.infolist():
        path = PurePosixPath(item.filename.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Archive contains an unsafe path")
        if item.is_dir() or "documents" not in path.parts:
            continue
        if path.suffix.lower() not in {".txt", ".pdf", ".docx", ".log", ".csv"}:
            raise ValueError("Unsupported evidence member: " + item.filename)
        total += item.file_size
        if item.file_size > 10 * 1024 * 1024 or total > 50 * 1024 * 1024 or len(names) >= 30:
            raise ValueError("Archive exceeds upload limits")
        names.append(item.filename)
    if len({PurePosixPath(n).name for n in names}) != len(names):
        raise ValueError("Duplicate evidence filenames in archive")
    return sorted(names)


def verify_archive(path, output, mode="inspect"):
    output.mkdir(parents=True, exist_ok=True)
    store = CaseStore(output / "storage")
    retriever = HybridRetriever(output / "index")
    retriever._model_load_attempted = True  # Reproducible lexical mechanics; no downloads.
    provider = OfflinePreviewProvider() if mode == "offline-preview" else get_llm_provider()
    service = EvidenceReviewService(store, retriever, lambda: provider)
    cid = store.create_case("Archive verification — " + path.stem,
        description="Isolated uploaded-evidence verification; answer keys are excluded.").case_id
    started = time.monotonic()
    with zipfile.ZipFile(path) as archive:
        names = evidence_members(archive)
        for name in names:
            target = store.uploads_dir / cid / PurePosixPath(name).name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
            store.add_document(cid, process_uploaded_file(cid, target, target.name))
        docs = service.documents(cid)
        service._index(cid, docs)
        sources = service.sources(cid)
        citations = [service.cite(cid, s) for s in sources]
        result = {"archive_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "case_id": cid,
            "mode": mode, "document_count": len(docs), "source_spans": len(sources),
            "ground_truth_indexed": any("ground_truth" in d.filename.lower() for d in docs),
            "citation_locator_checks": {"passed": sum(c["locator_valid"] for c in citations), "total": len(citations)},
            "quotation_checks": {"passed": sum(c["quotation_accurate"] for c in citations), "total": len(citations)},
            "files": [{"filename": d.filename, "status": d.status, "warning": d.warning} for d in docs],
            "model": provider.model_name(), "is_mock": bool(provider.is_mock), "analysis_status": "not_requested"}
        if mode == "real" and settings.LLM_PROVIDER.strip().lower() != "openai":
            result.update(analysis_status="blocked", blocked_reason="Only OpenAI is authorized for this archive. Configure LLM_PROVIDER=openai, LLM_MODEL and OPENAI_API_KEY.")
        elif mode == "real" and (provider.is_mock or not provider.is_available()):
            result.update(analysis_status="blocked", blocked_reason=provider_readiness()["message"])
        elif mode in {"real", "offline-preview"}:
            try:
                report = run_pipeline(service, cid, allow_fixture=mode == "offline-preview")
                (output / "report.md").write_text(markdown_report(report), encoding="utf-8")
                (output / "report.pdf").write_bytes(pdf_report(report))
                (output / "report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
                result.update(analysis_status="completed", analysis_run_id=report.analysis_run_id,
                    timeline_events=len(report.chronological_timeline),
                    comparisons=len(report.contradictions), hypotheses=len(report.candidate_hypotheses),
                    leading_hypothesis=report.case_summary.leading_hypothesis.model_dump() if report.case_summary.leading_hypothesis else None,
                    agent_status=report.agent_deliberations.processing_status)
                answer = service.answer(cid, "Which explanation is supported, and what is missing?")
                result["answer_status"] = answer["status"]
                # Review a source record without accepting it as truth; then verify persistence.
                run = service.load(cid)
                from app.models.evidence_review import ReviewRequest
                if run["claims"]:
                    claim = run["claims"][0]
                    from app.models.evidence_review import Claim
                    service.review(cid, run["run_id"], claim["claim_id"], ReviewRequest(action="correct_claim",
                        notes="Verification-only round-trip: attribution retained; no factual acceptance.", correction=Claim(**claim)))
                    result["correction_marks_stale"] = service.load(cid)["stale"]
                result["report_survives_restart"] = CaseStore(output / "storage").get_report(cid) is not None
            except Exception as exc:
                result.update(analysis_status="failed", error_type=type(exc).__name__, error=str(exc))
        # Only now read evaluation references. They were never supplied to the model/index.
        keys = [n for n in archive.namelist() if "/ground_truth/" in n and n.endswith(".json")]
        truth = json.loads(archive.read(keys[0])) if len(keys) == 1 else None
        result["reference_document_count"] = truth.get("document_count") if truth else None
        result["reference_timeline_items"] = len(truth.get("timeline", [])) if truth else None
        result["reference_conflicts"] = truth.get("planted_contradictions", []) if truth else []
    # Human-defined retrieval probes for the supplied Lakeview benchmark; not model prompts or expected outputs.
    probes = [("did not return", "03_interview_tom_reyes.txt"),
              ("18:02:19 TOM_REYES STAFF_DOOR ENTRY", "06_badge_access_log.txt"),
              ("18:16:33 CASE_LOCK KEY_02", "07_alarm_and_case_lock_log.txt"),
              ("06:29 PM long tube", "05_interview_greg_hall.txt"),
              ("buyer original 1824 survey map provenance", "09_dealer_email.txt"),
              ("about 04:30 PM", "04_interview_nina_patel.txt")]
    result["retrieval_probes"] = []
    for query, expected in probes:
        matches = search_case(service, cid, EvidenceSearchRequest(query=query, top_k=5))
        rank = next((i + 1 for i, m in enumerate(matches) if m.document_name == expected), None)
        result["retrieval_probes"].append({"query": query, "expected_document": expected, "rank": rank})
    ranks = [p["rank"] for p in result["retrieval_probes"]]
    result["retrieval_recall_at_5"] = sum(r is not None for r in ranks) / len(ranks)
    result["retrieval_mrr_at_5"] = sum(1 / r if r else 0 for r in ranks) / len(ranks)
    result["semantic_accuracy"] = {k: None for k in ["contradiction_precision", "contradiction_recall", "hypothesis_ranking_accuracy", "citation_semantic_support"]}
    result["limitations"] = ["Lexical retrieval probes and exact citation checks do not measure semantic accuracy.",
        "The answer-key reconstruction is an evaluation reference, not evidence or proof of personal credential use, map removal or tube contents.",
        "The reference opening time 09:00 is not explicitly stated in the supplied documents; discovery and reporting times should remain separate.",
        "Offline preview abstains from hypotheses and case answers; no hidden dates or answer-key conclusions are inserted."]
    result["elapsed_seconds"] = round(time.monotonic() - started, 3)
    (output / "verification.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "output" / "lakeview-verification")
    parser.add_argument("--mode", choices=["inspect", "real", "offline-preview"], default="inspect")
    args = parser.parse_args()
    print(json.dumps(verify_archive(args.archive, args.output, args.mode), indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
