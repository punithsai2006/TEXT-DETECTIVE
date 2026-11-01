"""
Automated Tests for Evidence Provenance Validation, Security Controls,
Document Deletion Workflow, and Reproducible Analysis Runs.
"""

import os
import tempfile
from pathlib import Path
import pytest

from app.models.schemas import (
    Case,
    CaseStatus,
    ContradictionItem,
    ContradictionType,
    DocumentMetadata,
    DocumentType,
    Event,
    EvidenceClassification,
    EvidenceItem,
    Hypothesis,
    HypothesisClaim,
    InvestigationReport,
    NLILabel,
    ReviewStatus,
    TextChunk,
    TimelineEntry,
)
from app.services.provenance.provenance_validator import ProvenanceValidator
from app.storage.case_store import CaseStore


@pytest.fixture
def test_case_store(tmp_path):
    return CaseStore(base_dir=tmp_path)


def test_provenance_validator_accepts_valid_citations():
    """Verify that legitimate, grounded citations pass provenance validation."""
    doc = DocumentMetadata(
        document_id="doc_01",
        case_id="case_prov_1",
        filename="interview_witness.txt",
        document_type=DocumentType.INTERVIEW,
        raw_text="Elena Vance arrived at the office at 21:00 UTC. She left the premises at 22:38 UTC.",
        cleaned_text="Elena Vance arrived at the office at 21:00 UTC. She left the premises at 22:38 UTC.",
    )

    event = Event(
        event_id="ev_01",
        description="Elena Vance arrival",
        participants=["Elena Vance"],
        document_id="doc_01",
        document_name="interview_witness.txt",
        source_sentence="Elena Vance arrived at the office at 21:00 UTC.",
    )

    report = ProvenanceValidator.validate_case(
        case_id="case_prov_1",
        documents=[doc],
        events=[event],
    )

    assert report.is_valid is True
    assert report.failed_checks == 0
    assert report.passed_checks >= 1


def test_provenance_validator_rejects_invalid_citation():
    """Intentionally insert an invalid citation referencing a fabricated passage and verify rejection."""
    doc = DocumentMetadata(
        document_id="doc_01",
        case_id="case_prov_1",
        filename="interview_witness.txt",
        document_type=DocumentType.INTERVIEW,
        raw_text="Elena Vance arrived at the office at 21:00 UTC.",
        cleaned_text="Elena Vance arrived at the office at 21:00 UTC.",
    )

    # Event references a sentence that does not exist in the document text
    hallucinated_event = Event(
        event_id="ev_fake_99",
        description="Marcus Reed admitted to stealing data in Moscow",
        participants=["Marcus Reed"],
        document_id="doc_01",
        document_name="interview_witness.txt",
        source_sentence="Marcus Reed boarded a private jet to Moscow at midnight.",
    )

    report = ProvenanceValidator.validate_case(
        case_id="case_prov_1",
        documents=[doc],
        events=[hallucinated_event],
    )

    assert report.is_valid is False
    assert report.failed_checks >= 1
    failure = report.failures[0]
    assert failure.module == "events"
    assert failure.item_id == "ev_fake_99"
    assert "cannot be located" in failure.reason.lower() or "absent" in failure.reason.lower()


def test_provenance_validator_rejects_missing_document_id():
    """Verify that a contradiction referencing a non-existent document ID is rejected."""
    doc_a = DocumentMetadata(
        document_id="doc_01",
        case_id="case_prov_1",
        filename="interview_a.txt",
        document_type=DocumentType.INTERVIEW,
        raw_text="The server room door was locked all night.",
        cleaned_text="The server room door was locked all night.",
    )

    contradiction = ContradictionItem(
        id="con_fake_01",
        case_id="case_prov_1",
        statement_a="The server room door was locked all night.",
        statement_b="The server room door was propped open with a chair.",
        doc_a_id="doc_01",
        doc_b_id="doc_non_existent_999",  # Missing document
        doc_a_name="interview_a.txt",
        doc_b_name="interview_missing.txt",
        entity_event_link="server room door",
        contradiction_type=ContradictionType.CONFIRMED_CONTRADICTION,
        nli_label=NLILabel.CONTRADICTION,
        confidence=0.95,
        explanation="Conflict over door status.",
    )

    report = ProvenanceValidator.validate_case(
        case_id="case_prov_1",
        documents=[doc_a],
        contradictions=[contradiction],
    )

    assert report.is_valid is False
    assert any("missing document" in f.reason.lower() or "non-existent" in f.reason.lower() for f in report.failures)


def test_document_deletion_workflow_and_outdated_status(test_case_store):
    """Verify document deletion removes file from disk, updates count, and marks case OUTDATED."""
    case = test_case_store.create_case("Homicide Case Alpha", "Initial review")
    case_id = case.case_id

    # Create dummy upload file
    uploads_dir = test_case_store.uploads_dir / case_id
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / "statement_jones.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Officer Jones arrived at 20:00.")

    doc = DocumentMetadata(
        document_id="doc_jones_01",
        case_id=case_id,
        filename="statement_jones.txt",
        document_type=DocumentType.REPORT,
        raw_text="Officer Jones arrived at 20:00.",
    )
    test_case_store.add_document(case_id, doc)
    assert len(test_case_store.get_documents(case_id)) == 1

    # Mark case completed to test outdated transition
    test_case_store.update_case_status(
        case_id, CaseStatus.COMPLETED, "Complete", 100, "Done"
    )

    # Delete document
    deleted = test_case_store.delete_document(case_id, "doc_jones_01")
    assert deleted is True

    # 1. Physical file removed
    assert not file_path.exists()

    # 2. Document removed from metadata list
    assert len(test_case_store.get_documents(case_id)) == 0

    # 3. Case status marked OUTDATED
    updated_case = test_case_store.get_case(case_id)
    assert updated_case.document_count == 0
    assert updated_case.status == CaseStatus.OUTDATED


def test_contradiction_human_review_workflow(test_case_store):
    """Verify human review status transition on detected contradictions (Task 5)."""
    case = test_case_store.create_case("Art Theft", "Museum investigation")
    case_id = case.case_id

    contradiction = ContradictionItem(
        id="con_101",
        case_id=case_id,
        statement_a="Security guard claims he was on patrol.",
        statement_b="Motion sensor log shows no movement.",
        doc_a_id="doc_1",
        doc_b_id="doc_2",
        doc_a_name="guard.txt",
        doc_b_name="sensor.log",
        entity_event_link="guard patrol",
        contradiction_type=ContradictionType.CONFIRMED_CONTRADICTION,
        nli_label=NLILabel.CONTRADICTION,
        confidence=0.88,
        explanation="Contradiction between guard testimony and sensor telemetry.",
        review_status=ReviewStatus.PENDING_REVIEW,
    )
    test_case_store.save_contradictions(case_id, [contradiction])

    # Analyst confirms contradiction
    updated = test_case_store.update_contradiction_review(
        case_id=case_id,
        contradiction_id="con_101",
        review_status=ReviewStatus.CONFIRMED,
        reviewer_id="lead_analyst_smith",
        review_notes="Telemetry logs verified by system administrator.",
    )

    assert updated is not None
    assert updated.review_status == ReviewStatus.CONFIRMED
    assert updated.reviewer_id == "lead_analyst_smith"
    assert updated.previous_review_status == "pending_review"
    assert updated.review_timestamp is not None
    assert "verified" in updated.review_notes.lower()


def test_reproducible_analysis_run_records(test_case_store):
    """Verify recording and retrieval of immutable analysis run history (Task 6)."""
    case = test_case_store.create_case("Financial Fraud", "Audit investigation")
    case_id = case.case_id

    from app.models.schemas import AnalysisRunRecord

    run_record = AnalysisRunRecord(
        run_id="run_20261101_120000_abc123",
        case_id=case_id,
        parser_version="1.1.0",
        model_provider="mock",
        model_name="mock-investigator-v1",
        prompt_version="v1.0",
        retrieval_settings={"top_k": 10},
        document_hashes={"ledger.csv": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},
        is_outdated=False,
    )

    test_case_store.save_run_record(case_id, run_record)
    runs = test_case_store.list_run_records(case_id)

    assert len(runs) == 1
    assert runs[0].run_id == "run_20261101_120000_abc123"
    assert runs[0].is_outdated is False

    # When documents change, mark runs outdated
    test_case_store.mark_runs_outdated(case_id)
    runs_after = test_case_store.list_run_records(case_id)
    assert runs_after[0].is_outdated is True


def test_contradiction_detection_engine_tracking():
    """Verify that contradiction detection records the specific detection engine (rules/nli/llm_verified)."""
    from app.services.contradiction.detector import contradiction_detector

    stmt_a = "Alice was inside Server Room B at 10:14 PM according to the badge logs."
    stmt_b = "Alice was never inside Server Room B and was absent offsite."

    label, c_type, conf, expl, engine = contradiction_detector.evaluate_pair_full(stmt_a, stmt_b)
    assert label == NLILabel.CONTRADICTION
    assert c_type == ContradictionType.CONFIRMED_CONTRADICTION
    assert engine in ["rules", "nli", "llm_verified"]
    assert conf >= 0.85

    item = ContradictionItem(
        id="contra_test_1",
        case_id="case_eng_1",
        statement_a=stmt_a,
        statement_b=stmt_b,
        doc_a_id="doc_1",
        doc_b_id="doc_2",
        doc_a_name="badge_logs.txt",
        doc_b_name="interview_alice.txt",
        entity_event_link="Alice",
        contradiction_type=c_type,
        nli_label=label,
        confidence=conf,
        detection_engine=engine,
        explanation=expl,
    )
    assert item.detection_engine == engine


def test_atomic_batch_upload_rollback(tmp_path):
    """Verify that batch upload rollback cleanly removes partially written files without leaving orphans."""
    from app.api.routes import _rollback_batch_uploads

    case_dir = tmp_path / "uploads" / "case_test_atomic"
    case_dir.mkdir(parents=True, exist_ok=True)
    f1 = case_dir / "file1.txt"
    f2 = case_dir / "file2.txt"
    f1.write_text("file 1 content")
    f2.write_text("file 2 content")

    assert f1.exists()
    assert f2.exists()

    _rollback_batch_uploads(written_paths=[f1, f2], uploaded_docs=[], case_id="case_test_atomic")

    assert not f1.exists()
    assert not f2.exists()


def test_atomic_write_json_integrity(test_case_store):
    """Verify that atomic JSON writing writes valid data and cleans up temporary files."""
    test_file = test_case_store.base_storage / "atomic_test.json"
    data = {"system": "Text Detective", "status": "active", "code": 42}

    test_case_store._atomic_write_json(test_file, data)

    assert test_file.exists()
    import json
    with open(test_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["code"] == 42

    # Verify no .tmp files left in the directory
    tmp_files = list(test_case_store.base_storage.glob("*.tmp_*"))
    assert len(tmp_files) == 0
