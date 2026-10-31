import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import PlainTextResponse, Response

from app.config import settings
from app.models.schemas import (
    AnalysisRunRecord,
    AnalysisStatus,
    AskQuestionRequest,
    AskQuestionResponse,
    Case,
    CaseCreateRequest,
    CaseGraph,
    CaseUpdateRequest,
    ContradictionItem,
    ContradictionReviewRequest,
    DocumentMetadata,
    DocumentType,
    Entity,
    Event,
    EvidenceItem,
    EvidenceSearchRequest,
    Hypothesis,
    HypothesisInput,
    InvestigationReport,
    ReviewStatus,
    TimelineEntry,
)
from app.services.ingestion.preprocessor import process_uploaded_file
from app.services.llm_provider import get_llm_provider
from app.services.orchestration.controller import controller
from app.services.provenance.provenance_validator import ProvenanceValidationReport, ProvenanceValidator
from app.services.reporting.reporter import export_report_to_json, export_report_to_markdown
from app.services.retrieval.retriever import retriever
from app.storage.case_store import case_store

logger = logging.getLogger(__name__)

api_router = APIRouter()

MAX_FILES_PER_UPLOAD = 20
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB per file
MAX_BATCH_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB per batch
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx", ".log", ".csv", ".json"}


# ==========================================
# SYSTEM HEALTH & PROVIDER STATUS
# ==========================================

@api_router.get("/health")
def get_health() -> Dict[str, Any]:
    provider = get_llm_provider()
    return {
        "status": "healthy",
        "service": "Text Detective Framework",
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": provider.model_name(),
        "is_mock": getattr(provider, "is_mock", False) or provider.model_name().startswith("mock"),
        "demo_mode": settings.DEMO_MODE,
        "storage_dir": str(settings.storage_path),
    }


# ==========================================
# CASE ENDPOINTS
# ==========================================

@api_router.get("/cases", response_model=List[Case])
def list_cases() -> List[Case]:
    return case_store.list_cases()


@api_router.post("/cases", response_model=Case, status_code=status.HTTP_201_CREATED)
def create_case(req: CaseCreateRequest) -> Case:
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Case name cannot be empty.")
    return case_store.create_case(name=req.name.strip(), description=req.description, is_demo=req.is_demo)


@api_router.get("/cases/{case_id}", response_model=Case)
def get_case(case_id: str) -> Case:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return c


@api_router.patch("/cases/{case_id}", response_model=Case)
def update_case(case_id: str, req: CaseUpdateRequest) -> Case:
    c = case_store.update_case(case_id, name=req.name, description=req.description)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return c


@api_router.delete("/cases/{case_id}")
def delete_case(case_id: str) -> Dict[str, Any]:
    deleted = case_store.delete_case(case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return {"message": f"Case '{case_id}' deleted successfully.", "case_id": case_id}


# ==========================================
# DOCUMENT ENDPOINTS
# ==========================================

@api_router.get("/cases/{case_id}/documents", response_model=List[DocumentMetadata])
def get_case_documents(case_id: str) -> List[DocumentMetadata]:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return case_store.get_documents(case_id)


@api_router.post("/cases/{case_id}/documents", response_model=List[DocumentMetadata])
def upload_documents(
    case_id: str,
    files: List[UploadFile] = File(...),
    document_type: Optional[str] = Form(None),
    speaker: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    timestamp: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
) -> List[DocumentMetadata]:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    if len(files) > MAX_FILES_PER_UPLOAD:
        raise HTTPException(
            status_code=400,
            detail=f"Exceeded maximum batch limit of {MAX_FILES_PER_UPLOAD} files per upload request."
        )

    uploaded_docs: List[DocumentMetadata] = []
    case_uploads_dir = case_store.uploads_dir / case_id
    case_uploads_dir.mkdir(parents=True, exist_ok=True)

    override_type = None
    if document_type:
        try:
            override_type = DocumentType(document_type.lower().strip())
        except ValueError:
            pass

    total_batch_size = 0

    for file in files:
        if not file.filename:
            continue

        raw_filename = file.filename

        # Filename sanitization & path traversal defense (Task 3)
        if "\x00" in raw_filename or ".." in raw_filename:
            raise HTTPException(status_code=400, detail="Invalid filename: illegal path traversal characters detected.")

        safe_name = Path(raw_filename).name.strip()
        safe_name = re.sub(r'[\/\\:*?"<>|]', '_', safe_name)
        if not safe_name:
            continue

        ext = Path(safe_name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file extension '{ext}'. Allowed extensions are: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        dest_path = (case_uploads_dir / safe_name).resolve()
        # Verify resolved destination path stays strictly inside case_uploads_dir
        if not dest_path.is_relative_to(case_uploads_dir.resolve()):
            raise HTTPException(status_code=400, detail="Security violation: Path traversal detected.")

        file_bytes = file.file.read()
        file_size = len(file_bytes)
        total_batch_size += file_size

        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File '{safe_name}' ({file_size} bytes) exceeds maximum limit of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB."
            )

        if total_batch_size > MAX_BATCH_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Batch size exceeds maximum limit of {MAX_BATCH_SIZE_BYTES // (1024*1024)}MB."
            )

        try:
            with open(dest_path, "wb") as f_out:
                f_out.write(file_bytes)

            doc_meta = process_uploaded_file(
                case_id=case_id,
                file_path=dest_path,
                original_filename=safe_name,
                override_doc_type=override_type,
                override_speaker=speaker,
                override_author=author,
                override_timestamp=timestamp,
                override_description=description,
            )
            case_store.add_document(case_id, doc_meta)
            uploaded_docs.append(doc_meta)
        except Exception as e:
            logger.error(f"Failed to process file '{safe_name}': {e}")
            raise HTTPException(status_code=400, detail=f"Failed to process '{safe_name}': {str(e)}")

    return uploaded_docs


@api_router.get("/documents/{document_id}", response_model=DocumentMetadata)
def get_document_details(document_id: str) -> DocumentMetadata:
    doc = case_store.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")
    return doc


@api_router.delete("/cases/{case_id}/documents/{document_id}")
def delete_case_document(case_id: str, document_id: str) -> Dict[str, Any]:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    deleted = case_store.delete_document(case_id, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found in case '{case_id}'.")
    return {"message": f"Document '{document_id}' deleted.", "case_id": case_id, "remaining_count": c.document_count}


@api_router.delete("/documents/{document_id}")
def delete_document(document_id: str) -> Dict[str, Any]:
    for c in case_store.list_cases():
        if case_store.delete_document(c.case_id, document_id):
            return {"message": f"Document '{document_id}' deleted.", "case_id": c.case_id}
    raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")


# ==========================================
# ANALYSIS & CONTROLLER WORKFLOW
# ==========================================

@api_router.post("/cases/{case_id}/analyze", response_model=InvestigationReport)
def run_case_analysis(
    case_id: str,
    hypotheses: Optional[List[HypothesisInput]] = None
) -> InvestigationReport:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    docs = case_store.get_documents(case_id)
    if not docs:
        raise HTTPException(
            status_code=400,
            detail="Cannot analyze case: no documents have been uploaded yet. Please upload files first."
        )

    try:
        report = controller.run_investigation(case_id=case_id, custom_hypotheses=hypotheses)
        return report
    except Exception as e:
        logger.error(f"Investigation analysis failed for case {case_id}: {e}")
        case_store.update_case_status(
            case_id=case_id,
            status=CaseStatus.FAILED,
            current_module="Error",
            progress_percentage=0,
            message=f"Analysis failed: {str(e)}",
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Analysis pipeline failed: {str(e)}")


@api_router.get("/cases/{case_id}/analysis-status", response_model=AnalysisStatus)
def get_analysis_status(case_id: str) -> AnalysisStatus:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return case_store.get_analysis_status(case_id)


@api_router.get("/cases/{case_id}/analysis-results")
def get_analysis_results(case_id: str) -> Dict[str, Any]:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    extraction = case_store.get_extraction(case_id)
    contradictions = case_store.get_contradictions(case_id)
    hypotheses = case_store.get_hypotheses(case_id)
    report = case_store.get_report(case_id)

    return {
        "case": c,
        "extraction": extraction,
        "contradictions": [item.model_dump() for item in contradictions],
        "hypotheses": [h.model_dump() for h in hypotheses],
        "report_id": report.report_id if report else None,
        "status": case_store.get_analysis_status(case_id),
    }


# ==========================================
# EXTRACTION & GRAPH ENDPOINTS
# ==========================================

@api_router.get("/cases/{case_id}/entities", response_model=List[Entity])
def get_case_entities(case_id: str) -> List[Entity]:
    ext = case_store.get_extraction(case_id)
    return [Entity(**e) for e in ext.get("entities", [])]


@api_router.get("/cases/{case_id}/events", response_model=List[Event])
def get_case_events(case_id: str) -> List[Event]:
    ext = case_store.get_extraction(case_id)
    return [Event(**ev) for ev in ext.get("events", [])]


@api_router.get("/cases/{case_id}/timeline", response_model=List[TimelineEntry])
def get_case_timeline(case_id: str) -> List[TimelineEntry]:
    ext = case_store.get_extraction(case_id)
    return [TimelineEntry(**t) for t in ext.get("timeline", [])]


@api_router.get("/cases/{case_id}/case-graph", response_model=CaseGraph)
def get_case_graph(case_id: str) -> CaseGraph:
    ext = case_store.get_extraction(case_id)
    g = ext.get("case_graph")
    return CaseGraph(**g) if g else CaseGraph()


# ==========================================
# EVIDENCE RETRIEVAL ENDPOINTS
# ==========================================

@api_router.post("/cases/{case_id}/evidence/search", response_model=List[EvidenceItem])
def search_evidence(case_id: str, req: EvidenceSearchRequest) -> List[EvidenceItem]:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return retriever.search(
        case_id=case_id,
        query=req.query,
        top_k=req.top_k,
        filter_doc_ids=req.document_ids,
        threshold=req.threshold or 0.0,
    )


@api_router.get("/cases/{case_id}/evidence", response_model=List[EvidenceItem])
def list_key_evidence(case_id: str, top_k: int = 15) -> List[EvidenceItem]:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    rep = case_store.get_report(case_id)
    if rep and rep.key_evidence:
        return rep.key_evidence[:top_k]
    # Otherwise fallback to baseline search
    return retriever.search(case_id=case_id, query=f"{c.name} {c.description}", top_k=top_k)


# ==========================================
# CONTRADICTIONS ENDPOINTS
# ==========================================

@api_router.get("/cases/{case_id}/contradictions", response_model=List[ContradictionItem])
def get_case_contradictions(case_id: str) -> List[ContradictionItem]:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return case_store.get_contradictions(case_id)


# ==========================================
# HYPOTHESES ENDPOINTS
# ==========================================

@api_router.get("/cases/{case_id}/hypotheses", response_model=List[Hypothesis])
def get_case_hypotheses(case_id: str) -> List[Hypothesis]:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return case_store.get_hypotheses(case_id)


@api_router.post("/cases/{case_id}/hypotheses", response_model=List[Hypothesis])
def add_case_hypotheses(case_id: str, new_hypotheses: List[HypothesisInput]) -> List[Hypothesis]:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    stored = case_store.get_hypotheses(case_id)
    from app.services.hypothesis.scorer import hypothesis_engine
    contradictions = case_store.get_contradictions(case_id)

    for item in new_hypotheses:
        h_id = f"hyp_user_{len(stored) + 1}"
        evaluated = hypothesis_engine.score_hypothesis(
            case_id=case_id,
            hypothesis_id=h_id,
            title=item.title,
            description=item.description,
            origin="user",
            case_contradictions=contradictions,
        )
        stored.append(evaluated)

    ranked = hypothesis_engine.rank_hypotheses(stored)
    case_store.save_hypotheses(case_id, ranked)
    return ranked


@api_router.post("/cases/{case_id}/hypotheses/score", response_model=List[Hypothesis])
def rescore_case_hypotheses(case_id: str) -> List[Hypothesis]:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    stored = case_store.get_hypotheses(case_id)
    if not stored:
        raise HTTPException(status_code=400, detail="No hypotheses found to rescore.")

    from app.services.hypothesis.scorer import hypothesis_engine
    contradictions = case_store.get_contradictions(case_id)
    rescored = []
    for h in stored:
        ev = hypothesis_engine.score_hypothesis(
            case_id=case_id,
            hypothesis_id=h.hypothesis_id,
            title=h.title,
            description=h.description,
            origin=h.origin,
            case_contradictions=contradictions,
        )
        rescored.append(ev)

    ranked = hypothesis_engine.rank_hypotheses(rescored)
    case_store.save_hypotheses(case_id, ranked)
    return ranked


# ==========================================
# QUESTION ANSWERING
# ==========================================

@api_router.post("/cases/{case_id}/ask", response_model=AskQuestionResponse)
def ask_question(case_id: str, req: AskQuestionRequest) -> AskQuestionResponse:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    return controller.ask_case_question(case_id=case_id, question=req.question.strip(), top_k=req.top_k)


# ==========================================
# CONTRADICTION REVIEW (TASK 5)
# ==========================================

@api_router.patch("/cases/{case_id}/contradictions/{contradiction_id}/review", response_model=ContradictionItem)
def review_contradiction(
    case_id: str,
    contradiction_id: str,
    req: ContradictionReviewRequest,
) -> ContradictionItem:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    updated = case_store.update_contradiction_review(
        case_id=case_id,
        contradiction_id=contradiction_id,
        review_status=req.review_status,
        reviewer_id=req.reviewer_id,
        review_notes=req.review_notes,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Contradiction '{contradiction_id}' not found in case '{case_id}'.")
    return updated


# ==========================================
# EVIDENCE PROVENANCE VALIDATION (TASK 2)
# ==========================================

@api_router.get("/cases/{case_id}/provenance", response_model=ProvenanceValidationReport)
def validate_case_provenance(case_id: str) -> ProvenanceValidationReport:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    docs = case_store.get_documents(case_id)
    extraction = case_store.get_extraction(case_id)
    contradictions = case_store.get_contradictions(case_id)
    hypotheses = case_store.get_hypotheses(case_id)
    report = case_store.get_report(case_id)

    events = [Event(**e) for e in extraction.get("events", [])]
    timeline = [TimelineEntry(**t) for t in extraction.get("timeline", [])]
    key_evidence = report.key_evidence if report else []

    val_report = ProvenanceValidator.validate_case(
        case_id=case_id,
        documents=docs,
        events=events,
        timeline=timeline,
        contradictions=contradictions,
        hypotheses=hypotheses,
        evidence_items=key_evidence,
        report=report,
    )
    return val_report


# ==========================================
# REPRODUCIBLE ANALYSIS RUNS (TASK 6)
# ==========================================

@api_router.get("/cases/{case_id}/runs", response_model=List[AnalysisRunRecord])
def list_analysis_runs(case_id: str) -> List[AnalysisRunRecord]:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return case_store.list_run_records(case_id)


@api_router.get("/cases/{case_id}/runs/{run_id}", response_model=AnalysisRunRecord)
def get_analysis_run(case_id: str, run_id: str) -> AnalysisRunRecord:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    record = case_store.get_run_record(case_id, run_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Run record '{run_id}' not found.")
    return record


# ==========================================
# REPORT ENDPOINTS
# ==========================================

@api_router.get("/cases/{case_id}/report", response_model=InvestigationReport)
def get_report(case_id: str) -> InvestigationReport:
    c = case_store.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    report = case_store.get_report(case_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"Report has not been generated yet for case '{case_id}'. Run analysis first."
        )
    return report


@api_router.get("/cases/{case_id}/report/download")
def download_report(case_id: str, format: str = Query("markdown", pattern="^(markdown|json|html)$")):
    rep = case_store.get_report(case_id)
    if not rep:
        raise HTTPException(status_code=404, detail="No report available for download. Run analysis first.")

    safe_name = rep.case_name.replace(" ", "_").lower()

    if format == "markdown":
        md = export_report_to_markdown(rep)
        return Response(
            content=md,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=report_{safe_name}.md"}
        )
    elif format == "json":
        js = export_report_to_json(rep)
        return Response(
            content=js,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=report_{safe_name}.json"}
        )
    else:
        # HTML preview
        md = export_report_to_markdown(rep)
        html_content = f"<!DOCTYPE html><html><head><title>Report: {rep.case_name}</title><style>body{{font-family:sans-serif;max-width:900px;margin:2rem auto;line-height:1.6;color:#131A2E;background:#FDFBF7;padding:1rem;}}pre{{background:#EEE;padding:1rem;overflow-x:auto;}}table{{border-collapse:collapse;width:100%;margin:1rem 0;}}th,td{{border:1px solid #CCC;padding:8px;text-align:left;}}th{{background:#EAE4D3;}}</style></head><body><pre>{md}</pre></body></html>"
        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": f"inline; filename=report_{safe_name}.html"}
        )
