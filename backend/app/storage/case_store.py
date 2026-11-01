import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings
from app.models.schemas import (
    AnalysisRunRecord,
    AnalysisStatus,
    Case,
    CaseGraph,
    CaseStatus,
    ContradictionItem,
    ContradictionType,
    ControllerFeedbackLoopEvent,
    DocumentMetadata,
    Entity,
    Event,
    Hypothesis,
    InvestigationReport,
    ReviewStatus,
    TimelineEntry,
    get_utc_now_iso,
)


class CaseStore:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_storage = base_dir or settings.storage_path
        self.cases_dir = self.base_storage / "cases"
        self.uploads_dir = self.base_storage / "uploads"
        self.chroma_dir = self.base_storage / "chroma"

        self.cases_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)

    def _case_dir(self, case_id: str) -> Path:
        d = self.cases_dir / case_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _case_file(self, case_id: str) -> Path:
        return self._case_dir(case_id) / "case.json"

    def _docs_file(self, case_id: str) -> Path:
        return self._case_dir(case_id) / "documents.json"

    def _extraction_file(self, case_id: str) -> Path:
        return self._case_dir(case_id) / "extraction.json"

    def _contradictions_file(self, case_id: str) -> Path:
        return self._case_dir(case_id) / "contradictions.json"

    def _hypotheses_file(self, case_id: str) -> Path:
        return self._case_dir(case_id) / "hypotheses.json"

    def _report_file(self, case_id: str) -> Path:
        return self._case_dir(case_id) / "report.json"

    def _audit_file(self, case_id: str) -> Path:
        return self._case_dir(case_id) / "audit_log.json"

    def _status_file(self, case_id: str) -> Path:
        return self._case_dir(case_id) / "status.json"

    def _runs_dir(self, case_id: str) -> Path:
        d = self._case_dir(case_id) / "runs"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _atomic_write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(f".tmp_{uuid.uuid4().hex[:6]}")
        with open(tmp_path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2, ensure_ascii=False)
        tmp_path.replace(path)

    # ==========================================
    # CASES CRUD
    # ==========================================

    def create_case(self, name: str, description: str = "", is_demo: bool = False, custom_id: Optional[str] = None) -> Case:
        case_id = custom_id or f"case_{uuid.uuid4().hex[:8]}"
        now = get_utc_now_iso()
        case = Case(
            case_id=case_id,
            name=name,
            description=description,
            is_demo=is_demo,
            created_at=now,
            updated_at=now,
            status=CaseStatus.CREATED,
            document_count=0,
            entity_count=0,
            event_count=0,
            contradiction_count=0,
            hypothesis_count=0,
        )
        self.save_case(case)
        # Initialize status
        self.update_case_status(
            case_id=case_id,
            status=CaseStatus.CREATED,
            current_module="None",
            progress_percentage=0,
            message="Case created. Ready for document upload."
        )
        return case

    def save_case(self, case: Case) -> None:
        case.updated_at = get_utc_now_iso()
        f = self._case_file(case.case_id)
        self._atomic_write_json(f, case.model_dump())

    def get_case(self, case_id: str) -> Optional[Case]:
        f = self._case_file(case_id)
        if not f.exists():
            return None
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            return Case(**data)

    def list_cases(self) -> List[Case]:
        cases = []
        for case_folder in self.cases_dir.iterdir():
            if case_folder.is_dir():
                c = self.get_case(case_folder.name)
                if c:
                    cases.append(c)
        cases.sort(key=lambda x: x.created_at, reverse=True)
        return cases

    def update_case(self, case_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Optional[Case]:
        case = self.get_case(case_id)
        if not case:
            return None
        if name is not None:
            case.name = name
        if description is not None:
            case.description = description
        self.save_case(case)
        return case

    def delete_case(self, case_id: str) -> bool:
        case_folder = self.cases_dir / case_id
        upload_folder = self.uploads_dir / case_id
        deleted = False
        if case_folder.exists():
            shutil.rmtree(case_folder, ignore_errors=True)
            deleted = True
        if upload_folder.exists():
            shutil.rmtree(upload_folder, ignore_errors=True)
        return deleted

    # ==========================================
    # DOCUMENTS
    # ==========================================

    def save_documents(self, case_id: str, documents: List[DocumentMetadata]) -> None:
        f = self._docs_file(case_id)
        self._atomic_write_json(f, [doc.model_dump() for doc in documents])

        # Update case doc count
        case = self.get_case(case_id)
        if case:
            case.document_count = len(documents)
            case.single_document_warning = (len(documents) == 1)
            self.save_case(case)

    def get_documents(self, case_id: str) -> List[DocumentMetadata]:
        f = self._docs_file(case_id)
        if not f.exists():
            return []
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            return [DocumentMetadata(**item) for item in data]

    def add_document(self, case_id: str, doc: DocumentMetadata) -> None:
        docs = self.get_documents(case_id)
        # Avoid duplicate doc IDs or identical filenames
        docs = [d for d in docs if d.document_id != doc.document_id and d.filename != doc.filename]
        docs.append(doc)
        self.save_documents(case_id, docs)

    def delete_document(self, case_id: str, document_id: str) -> bool:
        docs = self.get_documents(case_id)
        target_doc = next((d for d in docs if d.document_id == document_id), None)
        if not target_doc:
            return False

        # 1. Remove physical file from uploads folder if it exists
        uploaded_path = self.uploads_dir / case_id / target_doc.filename
        if uploaded_path.exists() and uploaded_path.is_file():
            try:
                uploaded_path.unlink()
            except Exception:
                pass

        # 2. Filter document list and save
        remaining_docs = [d for d in docs if d.document_id != document_id]
        self.save_documents(case_id, remaining_docs)

        # 3. Update case metadata and mark status as OUTDATED
        case = self.get_case(case_id)
        if case:
            case.document_count = len(remaining_docs)
            case.status = CaseStatus.OUTDATED
            self.save_case(case)

        # 4. Mark all past runs as outdated
        self.mark_runs_outdated(case_id)
        return True

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        for case in self.list_cases():
            for doc in self.get_documents(case.case_id):
                if doc.document_id == document_id:
                    return doc
        return None

    # ==========================================
    # EXTRACTION (ENTITIES, EVENTS, CASE GRAPH, TIMELINE)
    # ==========================================

    def save_extraction(
        self,
        case_id: str,
        entities: List[Entity],
        events: List[Event],
        timeline: List[TimelineEntry],
        case_graph: CaseGraph,
    ) -> None:
        data = {
            "entities": [e.model_dump() for e in entities],
            "events": [ev.model_dump() for ev in events],
            "timeline": [t.model_dump() for t in timeline],
            "case_graph": case_graph.model_dump(),
        }
        self._atomic_write_json(self._extraction_file(case_id), data)

        case = self.get_case(case_id)
        if case:
            case.entity_count = len(entities)
            case.event_count = len(events)
            self.save_case(case)

    def get_extraction(self, case_id: str) -> Dict[str, Any]:
        f = self._extraction_file(case_id)
        if not f.exists():
            return {
                "entities": [],
                "events": [],
                "timeline": [],
                "case_graph": CaseGraph().model_dump(),
            }
        with open(f, "r", encoding="utf-8") as fp:
            return json.load(fp)

    # ==========================================
    # CONTRADICTIONS
    # ==========================================

    def save_contradictions(self, case_id: str, contradictions: List[ContradictionItem]) -> None:
        data = [c.model_dump() for c in contradictions]
        self._atomic_write_json(self._contradictions_file(case_id), data)

        case = self.get_case(case_id)
        if case:
            conflict_count = sum(
                1 for c in contradictions
                if c.contradiction_type in [ContradictionType.CONFIRMED_CONTRADICTION, ContradictionType.POSSIBLE_CONTRADICTION]
            )
            case.contradiction_count = conflict_count
            self.save_case(case)

    def get_contradictions(self, case_id: str) -> List[ContradictionItem]:
        f = self._contradictions_file(case_id)
        if not f.exists():
            return []
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            return [ContradictionItem(**item) for item in data]

    def update_contradiction_review(
        self,
        case_id: str,
        contradiction_id: str,
        review_status: ReviewStatus,
        reviewer_id: Optional[str] = "analyst_1",
        review_notes: Optional[str] = None,
    ) -> Optional[ContradictionItem]:
        """Updates the human review status for a detected contradiction."""
        contradictions = self.get_contradictions(case_id)
        target = None
        for c in contradictions:
            if c.id == contradiction_id:
                c.previous_review_status = c.review_status.value if hasattr(c.review_status, "value") else str(c.review_status)
                c.review_status = review_status
                c.reviewer_id = reviewer_id
                c.review_timestamp = get_utc_now_iso()
                c.review_notes = review_notes
                target = c
                break

        if target:
            self.save_contradictions(case_id, contradictions)
        return target

    # ==========================================
    # HYPOTHESES
    # ==========================================

    def save_hypotheses(self, case_id: str, hypotheses: List[Hypothesis]) -> None:
        data = [h.model_dump() for h in hypotheses]
        self._atomic_write_json(self._hypotheses_file(case_id), data)

        case = self.get_case(case_id)
        if case:
            case.hypothesis_count = len(hypotheses)
            self.save_case(case)

    def get_hypotheses(self, case_id: str) -> List[Hypothesis]:
        f = self._hypotheses_file(case_id)
        if not f.exists():
            return []
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            return [Hypothesis(**item) for item in data]

    # ==========================================
    # INVESTIGATION REPORT
    # ==========================================

    def save_report(self, case_id: str, report: InvestigationReport) -> None:
        self._atomic_write_json(self._report_file(case_id), report.model_dump())

    def get_report(self, case_id: str) -> Optional[InvestigationReport]:
        f = self._report_file(case_id)
        if not f.exists():
            return None
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            return InvestigationReport(**data)

    # ==========================================
    # REPRODUCIBLE ANALYSIS RUN RECORDS (TASK 6)
    # ==========================================

    def save_run_record(self, case_id: str, record: AnalysisRunRecord) -> None:
        """Persists an immutable analysis run record."""
        runs_dir = self._runs_dir(case_id)
        record_file = runs_dir / f"{record.run_id}.json"
        self._atomic_write_json(record_file, record.model_dump())

    def list_run_records(self, case_id: str) -> List[AnalysisRunRecord]:
        """Lists all historical analysis runs for a case."""
        runs_dir = self._runs_dir(case_id)
        records = []
        for f in sorted(runs_dir.glob("*.json"), reverse=True):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    records.append(AnalysisRunRecord(**json.load(fp)))
            except Exception:
                continue
        return records

    def get_run_record(self, case_id: str, run_id: str) -> Optional[AnalysisRunRecord]:
        f = self._runs_dir(case_id) / f"{run_id}.json"
        if not f.exists():
            return None
        with open(f, "r", encoding="utf-8") as fp:
            return AnalysisRunRecord(**json.load(fp))

    def mark_runs_outdated(self, case_id: str) -> None:
        """Marks past run records as outdated when case documents change."""
        runs_dir = self._runs_dir(case_id)
        for f in runs_dir.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                data["is_outdated"] = True
                self._atomic_write_json(f, data)
            except Exception:
                continue

    # ==========================================
    # AUDIT LOG & STATUS TRACKING
    # ==========================================

    def log_controller_event(
        self,
        case_id: str,
        loop_name: str,
        iteration: int,
        trigger_reason: str,
        action_taken: str,
        result_summary: str,
    ) -> ControllerFeedbackLoopEvent:
        event = ControllerFeedbackLoopEvent(
            loop_name=loop_name,
            iteration=iteration,
            trigger_reason=trigger_reason,
            action_taken=action_taken,
            result_summary=result_summary,
            timestamp=get_utc_now_iso(),
        )
        logs = self.get_audit_log(case_id)
        logs.append(event)
        self._atomic_write_json(self._audit_file(case_id), [l.model_dump() for l in logs])

        # Update status feedback loops as well
        status = self.get_analysis_status(case_id)
        status.feedback_loops = logs
        self._save_status(status)
        return event

    def get_audit_log(self, case_id: str) -> List[ControllerFeedbackLoopEvent]:
        f = self._audit_file(case_id)
        if not f.exists():
            return []
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            return [ControllerFeedbackLoopEvent(**item) for item in data]

    def update_case_status(
        self,
        case_id: str,
        status: CaseStatus,
        current_module: str,
        progress_percentage: int,
        message: str,
        error: Optional[str] = None,
    ) -> AnalysisStatus:
        existing = self.get_analysis_status(case_id)
        updated = AnalysisStatus(
            case_id=case_id,
            status=status,
            current_module=current_module,
            progress_percentage=progress_percentage,
            message=message,
            feedback_loops=existing.feedback_loops,
            updated_at=get_utc_now_iso(),
            error=error,
        )
        self._save_status(updated)

        case = self.get_case(case_id)
        if case:
            case.status = status
            self.save_case(case)
        return updated

    def _save_status(self, status: AnalysisStatus) -> None:
        f = self._status_file(status.case_id)
        self._atomic_write_json(f, status.model_dump())

    def get_analysis_status(self, case_id: str) -> AnalysisStatus:
        f = self._status_file(case_id)
        if not f.exists():
            return AnalysisStatus(
                case_id=case_id,
                status=CaseStatus.CREATED,
                current_module="None",
                progress_percentage=0,
                message="Case created.",
            )
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            return AnalysisStatus(**data)


# Global singleton instance
case_store = CaseStore()
