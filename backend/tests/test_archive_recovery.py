"""Configuration failure and archive mechanics regressions; no cloud calls."""
import importlib.util
import json
import os
from pathlib import Path
import zipfile
import pytest
from fastapi.testclient import TestClient
from app.config import settings
from app.models.schemas import EvidenceSearchRequest
from app.services.llm_provider import MockLLMProvider
from app.services.offline_preview import OfflinePreviewProvider, PREFIX
from app.services.provider_readiness import provider_readiness
from app.services.orchestration.evidence_review import EvidenceReviewService
from app.services.orchestration.integrated_pipeline import run_pipeline
from app.services.retrieval.case_search import search_case
from evidence_fixtures import FixtureProvider, door_claim
from test_evidence_review import service, seed, upload


def test_mock_never_invents_dates_or_semantic_support():
    provider = MockLLMProvider()
    quote = "Alice entered at 09:15 UTC on 2024-01-02."
    response = provider.generate(json.dumps({"sources": [{"span_id": "sp_a", "document_id": "doc_a", "quote": quote}]}),
                                 '{"title":"Extraction"}')
    claim = json.loads(response.content)["claims"][0]
    assert claim["event_start"] is None and claim["timezone"] is None
    checks = provider.generate(json.dumps({"assertions": [{"assertion_id": "a", "text": "Alice removed the map.",
        "kind": "interpretation", "passages": [{"quote": quote}]}]}), '{"title": "VerificationBatch"}')
    assert json.loads(checks.content)["checks"][0]["supported"] is False


def test_offline_verifier_accepts_only_literal_source_preview():
    provider = OfflinePreviewProvider()
    source = {"quote": "The card was used."}
    result = provider.generate(json.dumps({"assertions": [{"assertion_id": "a", "kind": "source_claim",
        "text": PREFIX + source["quote"], "passages": [source]}]}), '{"title": "VerificationBatch"}')
    assert json.loads(result.content)["checks"][0]["supported"] is True


def test_readiness_is_actionable_and_contains_no_secret(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    state = provider_readiness()
    assert state["can_analyze"] is False and state["status"] == "missing_credentials"
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-private-test-not-a-real-key")
    state = provider_readiness()
    assert state["can_analyze"] and "sk-private" not in json.dumps(state)
    assert not state["generation_tested"]


def test_retry_reaches_all_55_candidates_without_publishing_partial(service, tmp_path, monkeypatch):
    cid = service.store.create_case("55 pair coverage").case_id
    quotes = [f"Account {i}: archive door state {i}." for i in range(11)]
    provider = FixtureProvider({q: [{**door_claim(str(i)), "entity_identity": "ambiguous"}] for i, q in enumerate(quotes)})
    service.provider_factory = lambda: provider
    upload(service, cid, tmp_path, "accounts.txt", "\n\n".join(quotes))
    monkeypatch.setattr(settings, "COMPARISON_BATCH_SIZE", 40)
    first = service.run(cid, allow_fixture=True)
    assert first["status"] == "partial" and first["processed_comparisons"] == 40
    assert first["pending_comparisons"] == 15
    # A normal request cannot silently activate mocks, even after prior fixtures.
    with pytest.raises(ValueError, match="Real-model verification blocked"):
        run_pipeline(service, cid)
    assert service.store.get_report(cid) is None
    second = service.run(cid, allow_fixture=True)
    assert second["status"] == "completed" and second["processed_comparisons"] == 55
    assert second["pending_comparisons"] == 0
    assert len({c["id"] for c in second["comparisons"]}) == 55


def test_missing_provider_retry_does_not_create_doomed_runs(service, tmp_path, monkeypatch):
    from app.main import app
    from app.api import routes, evidence_review
    cid = seed(service, tmp_path)
    service.provider_factory = lambda: MockLLMProvider()
    monkeypatch.setattr(routes, "case_store", service.store)
    monkeypatch.setattr(evidence_review, "service", service)
    with TestClient(app) as client:
        for _ in range(2):
            response = client.post(f"/api/cases/{cid}/analyze")
            assert response.status_code == 409 and "Retrying will not fix configuration" in response.json()["detail"]
    assert service.load(cid) is None
    assert len(service.documents(cid)) == 2
    assert search_case(service, cid, EvidenceSearchRequest(query="locked"))


def archive_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "verify_case_archive.py"
    spec = importlib.util.spec_from_file_location("verify_archive_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_archive_traversal_rejected(tmp_path):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("../documents/escape.txt", "untrusted")
    with zipfile.ZipFile(archive) as z, pytest.raises(ValueError, match="unsafe"):
        archive_module().evidence_members(z)


def test_archive_ground_truth_excluded_from_preview(tmp_path):
    archive = tmp_path / "test.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("case/documents/source.txt", "A source says the door was open.")
        z.writestr("case/ground_truth/key.json", json.dumps({"document_count": 1, "correct_hypothesis": "SECRET_GOLD_LABEL"}))
    result = archive_module().verify_archive(archive, tmp_path / "result", "offline-preview")
    assert result["analysis_status"] == "completed" and not result["ground_truth_indexed"]
    assert result["report_survives_restart"] and result["correction_marks_stale"]
    assert "SECRET_GOLD_LABEL" not in (tmp_path / "result" / "report.json").read_text(encoding="utf-8")
    assert result["answer_status"] == "abstained"


@pytest.mark.skipif(not os.environ.get("TEXT_DETECTIVE_CASE_ARCHIVE"), reason="Set TEXT_DETECTIVE_CASE_ARCHIVE for supplied-archive integration check")
def test_supplied_lakeview_archive_end_to_end(tmp_path):
    result = archive_module().verify_archive(Path(os.environ["TEXT_DETECTIVE_CASE_ARCHIVE"]), tmp_path / "lakeview", "offline-preview")
    assert result["document_count"] == 11 and result["analysis_status"] == "completed"
    assert result["quotation_checks"] == {"passed": 35, "total": 35}
    assert result["agent_status"] == "completed" and result["leading_hypothesis"] is None
    assert result["retrieval_recall_at_5"] == 1
