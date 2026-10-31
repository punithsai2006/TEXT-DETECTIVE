import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings
from app.models.schemas import (
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
    TimelineEntry,
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

    # ==========================================
    # CASES CRUD
    # ==========================================

    def create_case(self, name: str, description: str = "", is_demo: bool = False, custom_id: Optional[str] = None) -> Case:
        case_id = custom_id or f"case_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
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
        case.updated_at = datetime.utcnow().isoformat()
        f = self._case_file(case.case_id)
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(case.model_dump(), fp, indent=2)

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
        with open(f, "w", encoding="utf-8") as fp:
            json.dump([doc.model_dump() for doc in documents], fp, indent=2)

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
        initial_len = len(docs)
        docs = [d for d in docs if d.document_id != document_id]
        if len(docs) < initial_len:
            self.save_documents(case_id, docs)
            # Mark case status as outdated since document set changed
            case = self.get_case(case_id)
            if case and case.status == CaseStatus.COMPLETED:
                case.status = CaseStatus.OUTDATED
                self.save_case(case)
            return True
        return False

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
        with open(self._extraction_file(case_id), "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)

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
        with open(self._contradictions_file(case_id), "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)

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

    # ==========================================
    # HYPOTHESES
    # ==========================================

    def save_hypotheses(self, case_id: str, hypotheses: List[Hypothesis]) -> None:
        data = [h.model_dump() for h in hypotheses]
        with open(self._hypotheses_file(case_id), "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)

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
        with open(self._report_file(case_id), "w", encoding="utf-8") as fp:
            json.dump(report.model_dump(), fp, indent=2)

    def get_report(self, case_id: str) -> Optional[InvestigationReport]:
        f = self._report_file(case_id)
        if not f.exists():
            return None
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            return InvestigationReport(**data)

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
            timestamp=datetime.utcnow().isoformat(),
        )
        logs = self.get_audit_log(case_id)
        logs.append(event)
        with open(self._audit_file(case_id), "w", encoding="utf-8") as fp:
            json.dump([l.model_dump() for l in logs], fp, indent=2)

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
            updated_at=datetime.utcnow().isoformat(),
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
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(status.model_dump(), fp, indent=2)

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
