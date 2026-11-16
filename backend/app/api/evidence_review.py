"""Case-scoped v2 endpoints. No public fixture execution switch."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from app.models.evidence_review import QuestionRequest, ReviewRequest
from app.services.llm_provider import get_llm_provider
from app.services.orchestration.evidence_review import EvidenceReviewService, WorkflowError, valid_id
from app.services.retrieval.retriever import retriever
from app.storage.case_store import case_store

router = APIRouter()
service = EvidenceReviewService(case_store, retriever, get_llm_provider)


def execute(operation):
    try:
        return operation()
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    except WorkflowError as exc:
        raise HTTPException(503, str(exc)) from exc


@router.get("/cases/{case_id}/evidence-review")
def latest(case_id: str):
    return execute(lambda: {"run": service.load(case_id), "sources": list(service.sources(case_id).values()),
                            "ingestion": [{"filename": d.filename, "status": d.status, "warning": d.warning,
                                           "spans": len(d.source_spans)} for d in service.documents(case_id)]})


@router.post("/cases/{case_id}/evidence-review/runs")
def analyze(case_id: str):
    return execute(lambda: service.run(case_id))


@router.get("/cases/{case_id}/evidence-review/runs/{run_id}")
def run(case_id: str, run_id: str):
    return execute(lambda: service.load(case_id, run_id))


@router.get("/cases/{case_id}/evidence-review/sources/{span_id}")
def source(case_id: str, span_id: str):
    return execute(lambda: service.cite(case_id, span_id))


@router.get("/cases/{case_id}/evidence-review/documents/{document_id}/original")
def original(case_id: str, document_id: str):
    def get():
        valid_id(document_id)
        docs = service.documents(case_id)
        doc = next((d for d in docs if d.document_id == document_id), None)
        if not doc:
            raise KeyError("Document not in case")
        path = (case_store.uploads_dir / case_id / (doc.original_storage_name or doc.filename)).resolve()
        if not path.is_relative_to((case_store.uploads_dir / case_id).resolve()) or not path.is_file():
            raise KeyError("Original unavailable")
        import hashlib
        if doc.sha256_hash and hashlib.sha256(path.read_bytes()).hexdigest() != doc.sha256_hash:
            raise WorkflowError("Original file differs from analyzed document hash; re-upload required")
        return FileResponse(path, filename=doc.filename, content_disposition_type="attachment",
                            headers={"X-Content-Type-Options": "nosniff"})
    return execute(get)


@router.post("/cases/{case_id}/evidence-review/runs/{run_id}/reviews/{target_id}")
def review(case_id: str, run_id: str, target_id: str, request: ReviewRequest):
    return execute(lambda: service.review(case_id, run_id, target_id, request))


@router.post("/cases/{case_id}/evidence-review/questions")
def ask(case_id: str, request: QuestionRequest):
    return execute(lambda: service.answer(case_id, request.question, request.top_k))


@router.get("/cases/{case_id}/evidence-review/report", response_class=PlainTextResponse)
def report(case_id: str):
    return execute(lambda: PlainTextResponse(service.report(case_id), media_type="text/markdown",
                    headers={"Content-Disposition": 'attachment; filename="evidence-review.md"'}))
