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
    ForensicSummaryMilestone,
    Hypothesis,
    InvestigationReport,
    MultiAgentDeliberation,
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

MAX_FILES_PER_UPLOAD = 30
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


def _rollback_batch_uploads(written_paths: List[Path], uploaded_docs: List[DocumentMetadata], case_id: str) -> None:
    for p in written_paths:
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass
    for d in uploaded_docs:
        try:
            case_store.delete_document(case_id, d.document_id)
        except Exception:
            pass


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
    written_paths: List[Path] = []
    case_uploads_dir = case_store.uploads_dir / case_id
    case_uploads_dir.mkdir(parents=True, exist_ok=True)

    override_type = None
    if isinstance(document_type, str) and document_type.strip():
        try:
            override_type = DocumentType(document_type.lower().strip())
        except ValueError:
            pass

    speaker_val = speaker if isinstance(speaker, str) and speaker.strip() else None
    author_val = author if isinstance(author, str) and author.strip() else None
    timestamp_val = timestamp if isinstance(timestamp, str) and timestamp.strip() else None
    desc_val = description if isinstance(description, str) and description.strip() else None

    total_batch_size = 0

    for file in files:
        if not file.filename:
            continue

        raw_filename = file.filename

        # Filename sanitization & path traversal defense (Task 3)
        if "\x00" in raw_filename or ".." in raw_filename:
            _rollback_batch_uploads(written_paths, uploaded_docs, case_id)
            raise HTTPException(status_code=400, detail="Invalid filename: illegal path traversal characters detected.")

        safe_name = Path(raw_filename).name.strip()
        safe_name = re.sub(r'[\/\\:*?"<>|]', '_', safe_name)
        if not safe_name:
            continue

        ext = Path(safe_name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            _rollback_batch_uploads(written_paths, uploaded_docs, case_id)
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file extension '{ext}'. Allowed extensions are: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        dest_path = (case_uploads_dir / safe_name).resolve()
        # Verify resolved destination path stays strictly inside case_uploads_dir
        if not dest_path.is_relative_to(case_uploads_dir.resolve()):
            _rollback_batch_uploads(written_paths, uploaded_docs, case_id)
            raise HTTPException(status_code=400, detail="Security violation: Path traversal detected.")

        file_bytes = file.file.read()
        file_size = len(file_bytes)
        total_batch_size += file_size

        if file_size == 0:
            _rollback_batch_uploads(written_paths, uploaded_docs, case_id)
            raise HTTPException(
                status_code=400,
                detail=f"File '{safe_name}' is empty (0 bytes). Empty documents cannot be processed."
            )

        if file_size > MAX_FILE_SIZE_BYTES:
            _rollback_batch_uploads(written_paths, uploaded_docs, case_id)
            raise HTTPException(
                status_code=413,
                detail=f"File '{safe_name}' ({file_size} bytes) exceeds maximum limit of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB."
            )

        if total_batch_size > MAX_BATCH_SIZE_BYTES:
            _rollback_batch_uploads(written_paths, uploaded_docs, case_id)
            raise HTTPException(
                status_code=413,
                detail=f"Batch size exceeds maximum limit of {MAX_BATCH_SIZE_BYTES // (1024*1024)}MB."
            )

        # Ground-truth contamination defense (Issue 9)
        content_preview = file_bytes[:8192].decode("utf-8", errors="ignore").lower()
        gt_markers = ["correct_hypothesis", "planted_contradictions", "true_entities", "true_timeline", "decoy_hypotheses"]
        if any(marker in content_preview for marker in gt_markers):
            _rollback_batch_uploads(written_paths, uploaded_docs, case_id)
            raise HTTPException(
                status_code=400,
                detail=(
                    f"File '{safe_name}' appears to be a benchmark ground-truth key, not a primary evidence document. "
                    "Ground-truth files cannot be ingested into case evidence repository."
                )
            )

        try:
            with open(dest_path, "wb") as f_out:
                f_out.write(file_bytes)
            written_paths.append(dest_path)

            doc_meta = process_uploaded_file(
                case_id=case_id,
                file_path=dest_path,
                original_filename=safe_name,
                override_doc_type=override_type,
                override_speaker=speaker_val,
                override_author=author_val,
                override_timestamp=timestamp_val,
                override_description=desc_val,
            )
            case_store.add_document(case_id, doc_meta)
            uploaded_docs.append(doc_meta)
        except Exception as e:
            logger.error(f"Failed to process file '{safe_name}': {e}")
            _rollback_batch_uploads(written_paths, uploaded_docs, case_id)
            if isinstance(e, HTTPException):
                raise e
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
        report = controller.run_investigation(case_id=case_id)
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


@api_router.get("/cases/{case_id}/timeline/ground-truth", response_model=List[List[str]])
def get_case_timeline_ground_truth(case_id: str) -> List[List[str]]:
    """
    Returns the timeline formatted exactly in the ground-truth benchmark style:
    [ [ "YYYY-MM-DD HH:MM", "Concise active-voice event summary" ], ... ]
    """
    ext = case_store.get_extraction(case_id)
    raw_entries = [TimelineEntry(**t) for t in ext.get("timeline", [])]
    from app.services.extraction.event_summarizer import summarize_event_to_ground_truth
    
    result = []
    for t in raw_entries:
        t_str = t.timestamp_display
        if t.parsed_date and t.parsed_time:
            time_part = t.parsed_time[:5] if len(t.parsed_time) >= 5 else t.parsed_time
            t_str = f"{t.parsed_date} {time_part}"
        elif " " in t_str and len(t_str) > 16:
            t_str = t_str[:16]
            
        desc = t.clean_summary or t.event_description
        if not desc or len(desc) > 80 or any(p in desc for p in ["ACCESS_GRANTED", "UNLOCKED - KEY", "ENTRY - STAFF"]):
            desc = summarize_event_to_ground_truth(
                sentence=t.source_sentence,
                participants=t.participants,
                location=t.location,
                time_str=t.timestamp_display,
                document_name=t.document_name,
            )
        result.append([t_str, desc])
    return result


@api_router.get("/cases/{case_id}/summary-timeline", response_model=List[ForensicSummaryMilestone])
def get_case_summary_timeline(case_id: str) -> List[ForensicSummaryMilestone]:
    """
    Retrieves the executive Forensic Summary Timeline derived from the Case Graph
    and clustered into 5 strategic crime phases by the ForensicTimelineAgent.
    """
    milestones = case_store.get_summary_timeline(case_id)
    if milestones:
        return milestones
    
    # On-demand synthesis if case has already undergone extraction
    ext = case_store.get_extraction(case_id)
    raw_entries = [TimelineEntry(**t) for t in ext.get("timeline", [])]
    if not raw_entries:
        return []
    case_graph = CaseGraph(**ext.get("case_graph", {})) if ext.get("case_graph") else CaseGraph()
    entities = [Entity(**e) for e in ext.get("entities", [])]
    events = [Event(**ev) for ev in ext.get("events", [])]
    contradictions = case_store.get_contradictions(case_id)

    from app.services.agents.timeline_agent import forensic_timeline_agent
    synthesized = forensic_timeline_agent.synthesize_summary_timeline(
        case_graph=case_graph,
        raw_timeline=raw_entries,
        events=events,
        entities=entities,
        contradictions=contradictions,
    )
    if synthesized:
        case_store.save_summary_timeline(case_id, synthesized)
    return synthesized


@api_router.get("/cases/{case_id}/agents/deliberation", response_model=Optional[MultiAgentDeliberation])
def get_case_agent_deliberation(case_id: str) -> Optional[MultiAgentDeliberation]:
    """
    Retrieves the complete Multi-Agent System (MAS) deliberation record,
    inter-agent communication transcripts, and prosecution vs. defense debate.
    """
    delib = case_store.get_agent_deliberations(case_id)
    if delib:
        return delib
    
    hypotheses = case_store.get_hypotheses(case_id)
    if not hypotheses:
        return None
    case = case_store.get_case(case_id)
    ext = case_store.get_extraction(case_id)
    raw_entries = [TimelineEntry(**t) for t in ext.get("timeline", [])]
    case_graph = CaseGraph(**ext.get("case_graph", {})) if ext.get("case_graph") else CaseGraph()
    entities = [Entity(**e) for e in ext.get("entities", [])]
    events = [Event(**ev) for ev in ext.get("events", [])]
    contradictions = case_store.get_contradictions(case_id)

    from app.services.agents.orchestrator import agent_swarm_orchestrator
    _, delib = agent_swarm_orchestrator.run_multi_agent_investigation(
        case_id=case_id,
        case_name=case.name if case else case_id,
        case_graph=case_graph,
        raw_timeline=raw_entries,
        events=events,
        entities=entities,
        contradictions=contradictions,
        hypotheses=hypotheses,
    )
    case_store.save_agent_deliberations(case_id, delib)
    return delib


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
@api_router.post("/cases/{case_id}/contradictions/{contradiction_id}/review", response_model=ContradictionItem)
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
        raise HTTPException(
            status_code=404,
            detail=f"Contradiction '{contradiction_id}' not found in case '{case_id}'."
        )
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
