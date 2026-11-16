"""End-to-end contracts use explicit fixtures; no test is real-model accuracy."""
from io import BytesIO
import json
from pathlib import Path
import pytest
from pypdf import PdfReader

from app.config import settings
from app.models.case_analysis import HypothesisProposal, HypothesisAssessment, RankedHypothesis
from app.models.schemas import EvidenceSearchRequest
from app.services.hypothesis.evidence_reasoning import score_assessment, choose_leader, load_reasoning, reason_case
from app.services.orchestration.integrated_pipeline import run_pipeline, publish
from app.services.orchestration.evidence_review import EvidenceReviewService, WorkflowError
from app.services.retrieval.case_search import search_case
from app.services.reporting.evidence_report import markdown_report, pdf_report
from app.services.ingestion.preprocessor import process_uploaded_file
from app.storage.case_store import CaseStore
from evidence_fixtures import door_provider, DOOR_A, DOOR_B, FixtureProvider
from evidence_fixtures import door_claim
from test_evidence_review import service, seed, upload


def proposal():
    return HypothesisProposal(hypothesis_id="H", title="A proposed account", description="An account may fit the passages.",
        necessary_claims=[{"requirement_id": "R", "text": "The door was locked"}], relevant_claim_ids=[], source_span_ids=["s1"])


def assessment(positive=None, negative=None):
    return HypothesisAssessment(requirements=[{"requirement_id": "R", "supporting_source_span_ids": positive or [],
        "contrary_source_span_ids": negative or [], "explanation": "Labelled unit-test assessment"}],
        temporal={"status": "unknown", "explanation": "Unknown", "source_span_ids": []},
        relationships={"status": "unknown", "explanation": "Unknown", "source_span_ids": []})


def test_scoring_reproducible_and_duplicate_lineages_do_not_boost():
    sources = {"s1": {"quote": "The door was locked."}, "s2": {"quote": "The  door was locked."},
               "graph_copy": {"quote": "The door was locked."}}
    first = score_assessment(proposal(), assessment(["s1"]), sources)
    copied = score_assessment(proposal(), assessment(["s1", "s2", "graph_copy"]), sources)
    assert first[0] == copied[0] == 6
    assert copied[1].distinct_lineage_count == 1
    assert first[1].weighted_components == copied[1].weighted_components
    assert score_assessment(proposal(), assessment(["s1"], ["s2"]), sources)[0] == 0
    with pytest.raises(ValueError, match="six"):
        score_assessment(proposal(), assessment(["s1"]), sources, {"support": 1})


def test_duplicate_necessary_claims_cannot_inflate_coverage():
    p = proposal()
    p.necessary_claims += [p.necessary_claims[0].model_copy(update={"requirement_id": "copy"})]
    a = assessment(["s1"])
    a.requirements += [a.requirements[0].model_copy(update={"requirement_id": "copy"})]
    _, breakdown, *_ = score_assessment(p, a, {"s1": {"quote": "The door was locked."}})
    assert breakdown.necessary_claim_count == 1


def test_complete_reasoning_and_report_persist_and_rerun_is_idempotent(service, tmp_path):
    cid = seed(service, tmp_path)
    # Explicit fixture enablement exists only in this test subclass.
    class FixtureService(EvidenceReviewService):
        def run(self, case_id): return super().run(case_id, allow_fixture=True)
    fixture = FixtureService(service.store, service.retriever, service.provider_factory)
    report = run_pipeline(fixture, cid)
    assert report.is_mock and report.case_summary
    assert report.case_summary.leading_hypothesis is None
    assert any(h.is_other and h.evidence_support_score is None for h in report.candidate_hypotheses)
    assert report.llm_narrative["executive_summary"]
    assert report.case_summary.summary.source_span_ids
    scores = [(h.hypothesis_id, h.evidence_support_score, h.score_breakdown) for h in report.candidate_hypotheses]
    calls = len(service.provider_factory().prompts)
    original_run_record = service.store.get_run_record(cid, report.analysis_run_id).model_dump()
    second = run_pipeline(fixture, cid)
    assert report.analysis_run_id == second.analysis_run_id
    assert calls == len(service.provider_factory().prompts)
    assert service.store.get_run_record(cid, report.analysis_run_id).model_dump() == original_run_record
    assert scores == [(h.hypothesis_id, h.evidence_support_score, h.score_breakdown) for h in second.candidate_hypotheses]
    # Restart persistence, including typed summary, scores, quotes and run references.
    reloaded_store = CaseStore(service.store.base_storage)
    saved = reloaded_store.get_report(cid)
    assert saved.case_summary.model_dump() == report.case_summary.model_dump()
    assert saved.analysis_run_id == report.analysis_run_id
    assert len({n.id for n in saved.graph_snapshot.nodes}) == len(saved.graph_snapshot.nodes)
    assert any(n.node_type == "claim" for n in saved.graph_snapshot.nodes)
    assert any(n.node_type == "document" for n in saved.graph_snapshot.nodes)
    assert all(edge.source_span_ids for edge in saved.graph_snapshot.edges)
    markdown = markdown_report(saved)
    for section in ["Executive summary", "Hypothesis Scoring", "Detailed timeline", "Evidence appendix", "limitations"]:
        assert section in markdown
    pdf = pdf_report(saved)
    reader = PdfReader(BytesIO(pdf))
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert len(reader.pages) >= 2
    assert "FIXTURE ONLY" in text and "guard.txt" in text and "Evidence appendix" in text
    assert str(report.analysis_run_id) in text


def test_report_failure_resumes_successful_hypothesis_checkpoints(service, tmp_path):
    cid = seed(service, tmp_path)
    run = service.run(cid, allow_fixture=True)
    original = service.provider_factory()
    class FailsReport(FixtureProvider):
        def generate(self, prompt, system_prompt=None):
            if '\"title\": \"ReportDraft\"' in system_prompt:
                raise RuntimeError("Simulated report-stage failure")
            return original.generate(prompt, system_prompt)
    service.provider_factory = lambda: FailsReport()
    with pytest.raises(WorkflowError):
        reason_case(service, cid, run)
    failed = load_reasoning(service, cid, run)
    assert failed["status"] == "failed" and failed["hypotheses"]
    assert "hypotheses" in failed["stages"]
    previous_scores = [(h["hypothesis_id"], h["evidence_support_score"]) for h in failed["hypotheses"]]
    service.provider_factory = lambda: original
    before = len(original.prompts)
    resumed = reason_case(service, cid, run)
    assert resumed["status"] == "completed"
    assert len(original.prompts) - before == 2  # Only report draft + its support verification.
    assert previous_scores == [(h["hypothesis_id"], h["evidence_support_score"]) for h in resumed["hypotheses"]]


def test_search_exact_filters_links_and_model_independence(service, tmp_path):
    cid = seed(service, tmp_path)
    docs = service.documents(cid)
    before = len(service.provider_factory().prompts)
    results = search_case(service, cid, EvidenceSearchRequest(query="archive door was locked", mode="exact"))
    assert len(results) == 1 and results[0].text == DOOR_A
    assert len(service.provider_factory().prompts) == before
    assert not search_case(service, cid, EvidenceSearchRequest(query="archive door was locked", mode="exact", document_ids=[docs[1].document_id]))
    run = service.run(cid, allow_fixture=True)
    results = search_case(service, cid, EvidenceSearchRequest(query="archive door", mode="exact", entity="archive door", date_from="2026-11-01", date_to="2026-11-01"))
    assert len(results) == 2 and all(result.related_event_ids for result in results)
    assert not search_case(service, cid, EvidenceSearchRequest(query="archive", mode="exact", date_from="2027-01-01"))
    other = service.store.create_case("Other case").case_id
    upload(service, other, tmp_path, "other.txt", "Unique outsider account")
    assert not search_case(service, cid, EvidenceSearchRequest(query="Unique outsider", mode="exact"))


def test_answer_key_after_first_eight_kilobytes_is_rejected(tmp_path):
    path = tmp_path / "evidence.txt"
    path.write_text("Ordinary text. " * 1000 + '\n{"correct_hypothesis": "DO NOT INGEST"}', encoding="utf-8")
    with pytest.raises(ValueError, match="answer keys"):
        process_uploaded_file("case_keys", path, path.name)


def test_hypothesis_question_uses_persisted_assessments_without_regenerating_report(service, tmp_path):
    cid = seed(service, tmp_path)
    class FixtureService(EvidenceReviewService):
        def run(self, case_id): return super().run(case_id, allow_fixture=True)
    fixture = FixtureService(service.store, service.retriever, service.provider_factory)
    run_pipeline(fixture, cid)
    provider = service.provider_factory()
    before = len(provider.prompts)
    answer = fixture.answer(cid, "Which hypothesis is best supported, and why?")
    assert answer["status"] == "answered" and "tied" in answer["assertions"][0]["text"]
    prompts = provider.prompts[before:]
    assert not any('\"title\": \"ReportDraft\"' in system for _, system in prompts)
    assert any(action["role"] == "hypothesis_analysis_agent" and action["tool"] == "decision" for action in answer["actions"])


def test_bad_score_weights_invalidate_previous_run(service, tmp_path, monkeypatch):
    cid = seed(service, tmp_path)
    run = service.run(cid, allow_fixture=True)
    monkeypatch.setattr(settings, "SCORE_WEIGHTS", {**settings.SCORE_WEIGHTS, "support": 5})
    assert service.load(cid, run["run_id"])["stale"]


def test_tied_and_insufficient_hypotheses_have_no_leader():
    base = dict(hypothesis_id="H", title="Candidate", description="Qualified account", evidence_support_score=0,
        score_method_version="test", score_breakdown=None, supporting_source_span_ids=[], contrary_source_span_ids=[],
        assumptions=[], missing_evidence=[], relevant_claim_ids=[], relevant_event_ids=[], relevant_graph_node_ids=[], limitations=[])
    assert choose_leader([RankedHypothesis(**base)]) is None
    first = RankedHypothesis(**base)
    assert choose_leader([first, first.model_copy(update={"hypothesis_id": "H2"})]) is None


def test_approximate_430_and_432_contextual_compatibility_contract(service, tmp_path):
    cid = service.store.create_case("Approximate-time fixture").case_id
    a = "Alex reports entering the archive around 4:30 PM on 1 November 2026."
    b = "A badge entry for Alex is recorded at 4:32 PM on 1 November 2026."
    first = {**door_claim("archive"), "subject": "Alex", "predicate": "entered", "approximate": True,
             "precision": "approximate", "event_start": "2026-11-01T16:30:00+00:00"}
    second = {**first, "approximate": False, "precision": "minute", "event_start": "2026-11-01T16:32:00+00:00"}
    provider = FixtureProvider({a: [first], b: [second]})
    service.provider_factory = lambda: provider
    upload(service, cid, tmp_path, "witness.txt", a)
    upload(service, cid, tmp_path, "badge.txt", b)
    run = service.run(cid, allow_fixture=True)
    assert run["comparisons"][0]["outcome"] == "COMPATIBLE"
    assert any(action.get("action") == "retrieve_context" for action in run["actions"])


def test_partial_comparison_retry_reuses_completed_outputs(service, tmp_path, monkeypatch):
    import app.services.orchestration.evidence_review as module
    cid = service.store.create_case("Bounded retry fixture").case_id
    side_a, side_b = DOOR_A.replace("archive", "side"), DOOR_B.replace("archive", "side")
    provider = FixtureProvider({DOOR_A: [door_claim("locked")], DOOR_B: [door_claim("open")],
        side_a: [{**door_claim("locked"), "subject": "side door"}], side_b: [{**door_claim("open"), "subject": "side door"}]})
    service.provider_factory = lambda: provider
    upload(service, cid, tmp_path, "first.txt", DOOR_A + "\n\n" + side_a)
    upload(service, cid, tmp_path, "second.txt", DOOR_B + "\n\n" + side_b)
    original_budget = module.Budget
    monkeypatch.setattr(module, "Budget", lambda *args, **kwargs: original_budget(calls=4, seconds=120))
    first = service.run(cid, allow_fixture=True)
    assert first["status"] == "partial" and len(first["comparisons"]) == 1
    second = service.run(cid, allow_fixture=True)
    assert second["status"] == "completed" and len(second["comparisons"]) == 2
    assert {a["tool"] for a in second["actions"]} >= {"reuse_extraction_checkpoint", "reuse_comparison_checkpoint"}


def test_bad_hypothesis_reference_does_not_poison_retry_checkpoint(service, tmp_path):
    from app.services.llm_provider import LLMResponse
    cid = seed(service, tmp_path)
    run = service.run(cid, allow_fixture=True)
    original = service.provider_factory()
    class OneBadReference(FixtureProvider):
        invalid = True
        def generate(self, prompt, system_prompt=None):
            response = original.generate(prompt, system_prompt)
            if self.invalid and '\"title\": \"HypothesisDraft\"' in system_prompt:
                self.invalid = False
                payload = json.loads(response.content)
                payload["hypotheses"][0]["source_span_ids"] = ["other_case_unavailable_source"]
                return response.model_copy(update={"content": json.dumps(payload)})
            return response
    provider = OneBadReference()
    service.provider_factory = lambda: provider
    with pytest.raises(WorkflowError, match="unavailable"):
        reason_case(service, cid, run)
    assert "hypotheses" not in load_reasoning(service, cid, run)["stages"]
    assert reason_case(service, cid, run)["status"] == "completed"


def test_follow_up_history_is_persisted_and_case_scoped(service, tmp_path):
    cid = seed(service, tmp_path)
    service.run(cid, allow_fixture=True)
    service.answer(cid, "What state was the archive door in?")
    service.answer(cid, "What context supports that account?")
    payloads = [json.loads(prompt) for prompt, system in service.provider_factory().prompts if '\"title\": \"AnswerDraft\"' in system]
    assert payloads[-1]["conversation_context"][0]["question"] == "What state was the archive door in?"
    assert len(service.answer_history(cid)) == 2
    other = service.store.create_case("Isolated conversation").case_id
    assert service.answer_history(other) == []


def test_fixture_checkpoints_cannot_masquerade_as_real_provider_results(service, tmp_path):
    cid = seed(service, tmp_path)
    service.run(cid, allow_fixture=True)
    class FailingTransport(FixtureProvider):
        is_mock = False  # Simulate a differently configured transport, without network.
        def generate(self, *args, **kwargs):
            raise RuntimeError("Test transport failed; no real inference executed")
    service.provider_factory = FailingTransport
    run = service.run(cid)
    assert run["status"] == "failed" and run["model_calls"] == 2
    assert not any(a["tool"] == "reuse_extraction_checkpoint" for a in run["actions"])
