"""Explicit synthetic FIXTURE server for UI verification; never real inference."""
import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "tests"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="store_true", required=True,
                        help="Acknowledge scripted fixture output; no real-model inference")
    parser.add_argument("--port", type=int, default=8004)
    parser.add_argument("--export", type=Path, help="Write a labelled fixture PDF and Markdown to this path")
    parser.add_argument("--no-serve", action="store_true", help="Run/export the fixture without opening a server")
    args = parser.parse_args()
    os.environ["STORAGE_DIR"] = str(ROOT / "storage" / "review-fixture-demo")
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ["DEMO_MODE"] = "true"
    from app.main import app
    from app.api import evidence_review as routes
    from app.storage.case_store import case_store
    from app.services.ingestion.preprocessor import process_uploaded_file
    from app.services.retrieval.retriever import retriever
    from app.services.orchestration.evidence_review import EvidenceReviewService
    from app.services.orchestration.integrated_pipeline import run_pipeline
    from evidence_fixtures import DOOR_A, DOOR_B, door_provider
    import uvicorn

    class ExplicitFixtureService(EvidenceReviewService):
        def run(self, case_id):
            return super().run(case_id, allow_fixture=True)

    retriever._model_load_attempted = True  # No automatic model downloads for fixtures.
    routes.service = ExplicitFixtureService(case_store, retriever, door_provider)
    cid = "case_review_fixture"
    if not case_store.get_case(cid):
        case_store.create_case("FIXTURE ONLY — Archive door review", is_demo=True, custom_id=cid)
        folder = case_store.uploads_dir / cid
        folder.mkdir(parents=True, exist_ok=True)
        for name, text in [("guard.txt", DOOR_A), ("maintenance.txt", DOOR_B)]:
            path = folder / name
            path.write_text(text, encoding="utf-8")
            case_store.add_document(cid, process_uploaded_file(cid, path, name))
    report = run_pipeline(routes.service, cid)
    if args.export:
        from app.services.reporting.evidence_report import pdf_report, markdown_report
        args.export.parent.mkdir(parents=True, exist_ok=True)
        args.export.write_bytes(pdf_report(report))
        args.export.with_suffix(".md").write_text(markdown_report(report), encoding="utf-8")
        print(f"Exported FIXTURE ONLY PDF and Markdown: {args.export}")
    if args.no_serve:
        return
    print(f"FIXTURE ONLY: scripted outputs, isolated storage, no real LLM. Open http://127.0.0.1:{args.port}/new")
    uvicorn.run(app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
