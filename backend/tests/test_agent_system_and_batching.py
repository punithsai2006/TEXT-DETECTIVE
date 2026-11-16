import json
import pytest
from pathlib import Path
from types import SimpleNamespace

from app.models.schemas import TimelineEntry, CaseGraph
from app.models.evidence_review import Claim, Outcome
from app.services.agents.evidence_orchestrator import (
    ForensicTimelineAgent,
    LeadInvestigatorAgent,
    KnowledgeGraphRAGAgent,
    CrossExaminationAgent,
    classify_investigation_phase,
    load_deliberation,
)
from app.services.contradiction.candidates import (
    candidate_pairs,
    subjects_compatible,
    locations_compatible,
    objects_compatible,
)
from app.services.ingestion.preprocessor import process_uploaded_file
from app.services.orchestration.evidence_review import EvidenceReviewService
from app.services.orchestration.integrated_pipeline import run_pipeline, publish
from app.services.retrieval.retriever import HybridRetriever
from app.storage.case_store import CaseStore
from evidence_fixtures import DOOR_A, DOOR_B, door_provider


def test_classify_investigation_phase():
    assert classify_investigation_phase("Reconnaissance and planning of building access") == "Preparation"
    assert classify_investigation_phase("Guard swiped badge and unlocked archive door") == "Access or entry"
    assert classify_investigation_phase("Theft of canvas and unauthorized database exfiltration") == "Critical incident"
    assert classify_investigation_phase("Departed via rear exit gate at 21:00") == "Exit or aftermath"
    assert classify_investigation_phase("Witness gave interview statement regarding whereabouts") == "Subsequent accounts and investigation"
    assert classify_investigation_phase("General lighting in courtyard") == "unclassified"


def test_forensic_timeline_milestones_and_uncertainty():
    agent = ForensicTimelineAgent()
    timeline = [
        TimelineEntry(
            entry_id="e1",
            event_id="e1",
            timestamp_display="2026-11-01 20:00 UTC",
            event_description="Guard swiped badge and entered server room",
            document_name="guard.txt",
            document_type="log",
            document_id="doc1",
            chunk_id="sp_1",
            char_start=0,
            char_end=20,
            source_sentence="Guard swiped badge and entered server room",
            ordering_group="comparable UTC timestamps",
            is_uncertain=False,
            event_basis="logged",
            source_span_ids=["sp_1"],
        ),
        TimelineEntry(
            entry_id="e2",
            event_id="e2",
            timestamp_display="2026-11-01 20:30 UTC",
            event_description="Theft of confidential prototype payload reported",
            document_name="incident.txt",
            document_type="report",
            document_id="doc2",
            chunk_id="sp_2",
            char_start=0,
            char_end=30,
            source_sentence="Theft of confidential prototype payload reported",
            ordering_group="comparable UTC timestamps",
            is_uncertain=False,
            event_basis="observed",
            source_span_ids=["sp_2"],
        ),
        TimelineEntry(
            entry_id="e3",
            event_id="e3",
            timestamp_display="Unknown time (approximate)",
            event_description="Interview statement claiming suspect was at dinner",
            document_name="interview.txt",
            document_type="interview",
            document_id="doc3",
            chunk_id="sp_3",
            char_start=0,
            char_end=25,
            source_sentence="Interview statement claiming suspect was at dinner",
            ordering_group="uncertain/unordered",
            is_uncertain=True,
            event_basis="reported",
            source_span_ids=["sp_3"],
        ),
    ]

    milestones = agent.run(timeline)
    assert len(milestones) == 3
    # Check phases
    assert milestones[0].phase == "Access or entry"
    assert milestones[0].event_basis == "logged"
    assert not milestones[0].uncertainty

    assert milestones[1].phase == "Critical incident"
    assert milestones[1].event_basis == "observed"

    assert milestones[2].phase == "Subsequent accounts and investigation"
    assert milestones[2].uncertainty is True


def test_candidate_matching_helpers():
    # Subject alias matching
    assert subjects_compatible("Alice Vance", "Alice Vance")
    assert subjects_compatible("A. Vance", "Alice Vance")
    assert subjects_compatible("Dr. Alice Vance", "Alice Vance")
    assert not subjects_compatible("Bob Chen", "Alice Vance")

    # Location matching
    assert locations_compatible("Server Room B", "Server Room B")
    assert locations_compatible("Room B", "Room B")
    assert not locations_compatible("Basement Vault", "Roof Hangar")

    # Object matching
    assert objects_compatible("archive door", "Archive Door")
    assert objects_compatible("USB Flash Drive", "usb flash drive")
    assert not objects_compatible("Cardboard Tube", "Server Console")


def test_candidate_pairs_generator():
    claims = [
        {"claim_id": "c1", "subject": "Alice Vance", "predicate": "door state", "object": "locked", "location": "Room B"},
        {"claim_id": "c2", "subject": "A. Vance", "predicate": "door state", "object": "open", "location": "Room B"},
        {"claim_id": "c3", "subject": "David Wright", "predicate": "workstation access", "object": "logged in", "location": "Floor 2"},
    ]
    pairs = list(candidate_pairs(claims))
    assert len(pairs) >= 1
    # First pair should match Alice Vance and A. Vance due to compatible subject and identical predicate
    pair_ids = {(p[0]["claim_id"], p[1]["claim_id"]) for p in pairs}
    assert ("c1", "c2") in pair_ids


def test_persisted_deliberation_reloads_from_disk(tmp_path):
    store = CaseStore(tmp_path / "store")
    retriever = HybridRetriever(tmp_path / "index")
    retriever._model_load_attempted = True
    provider = door_provider()

    class FixtureService(EvidenceReviewService):
        def run(self, cid, allow_fixture=True):
            return super().run(cid, allow_fixture=True)

    service = FixtureService(store, retriever, lambda: provider)

    cid = store.create_case("Deliberation persistence case").case_id
    folder = store.uploads_dir / cid
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "guard.txt").write_text(DOOR_A, encoding="utf-8")
    (folder / "maintenance.txt").write_text(DOOR_B, encoding="utf-8")
    store.add_document(cid, process_uploaded_file(cid, folder / "guard.txt", "guard.txt"))
    store.add_document(cid, process_uploaded_file(cid, folder / "maintenance.txt", "maintenance.txt"))

    report = run_pipeline(service, cid)
    assert report.agent_deliberations is not None
    assert report.agent_deliberations.processing_status == "completed"

    # Reload from fresh service instance
    fresh_store = CaseStore(tmp_path / "store")
    fresh_service = FixtureService(fresh_store, retriever, lambda: provider)
    fresh_run = fresh_service.load(cid)
    assert fresh_run is not None
    loaded_delib = load_deliberation(fresh_service, cid, fresh_run)
    assert loaded_delib is not None
    assert loaded_delib.deliberation_id == report.agent_deliberations.deliberation_id
    assert len(loaded_delib.agent_states) == 5


def test_resume_contradictions_endpoint(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api import routes as api_routes
    from app.api import evidence_review as ev_routes

    store = CaseStore(tmp_path / "store")
    retriever = HybridRetriever(tmp_path / "index")
    retriever._model_load_attempted = True
    provider = door_provider()

    class FixtureService(EvidenceReviewService):
        def run(self, cid, allow_fixture=True):
            return super().run(cid, allow_fixture=True)

    service = FixtureService(store, retriever, lambda: provider)
    monkeypatch.setattr(api_routes, "case_store", store)
    monkeypatch.setattr(ev_routes, "service", service)

    cid = store.create_case("Resume batch case").case_id
    folder = store.uploads_dir / cid
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "guard.txt").write_text(DOOR_A, encoding="utf-8")
    (folder / "maintenance.txt").write_text(DOOR_B, encoding="utf-8")
    store.add_document(cid, process_uploaded_file(cid, folder / "guard.txt", "guard.txt"))
    store.add_document(cid, process_uploaded_file(cid, folder / "maintenance.txt", "maintenance.txt"))

    # Initial analysis
    run_pipeline(service, cid)

    with TestClient(app) as client:
        res = client.post(f"/api/cases/{cid}/contradictions/resume")
        assert res.status_code == 200
        data = res.json()
        assert "processed_comparisons" in data
        assert "pending_comparisons" in data
        assert "status" in data

