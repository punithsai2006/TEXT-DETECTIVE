import pytest
from app.api.routes import (
    ask_question,
    download_report,
    get_case,
    get_case_contradictions,
    get_case_documents,
    get_case_graph,
    get_case_hypotheses,
    get_case_timeline,
    get_health,
    get_report,
    list_cases,
    search_evidence,
)
from app.models.schemas import AskQuestionRequest, EvidenceSearchRequest


def test_api_health():
    data = get_health()
    assert data["status"] == "healthy"
    assert data["service"] == "Text Detective Framework"
    assert "llm_provider" in data


def test_api_cases_list():
    cases = list_cases()
    assert isinstance(cases, list)
    assert len(cases) >= 3


def test_api_get_case_detail():
    c = get_case("case_01_meridian")
    assert c.case_id == "case_01_meridian"
    assert "Meridian" in c.name


def test_api_get_documents():
    docs = get_case_documents("case_01_meridian")
    assert len(docs) >= 8
    assert any("interview_alice_vance" in d.filename for d in docs)


def test_api_get_timeline():
    timeline = get_case_timeline("case_01_meridian")
    assert len(timeline) > 0
    # Chronological sort check
    for i in range(len(timeline) - 1):
        assert timeline[i].sort_key <= timeline[i + 1].sort_key


def test_api_get_contradictions():
    conflicts = get_case_contradictions("case_01_meridian")
    assert len(conflicts) > 0


def test_api_get_hypotheses():
    hyps = get_case_hypotheses("case_01_meridian")
    assert len(hyps) >= 3
    # Rank 1 must have highest score
    assert hyps[0].rank == 1
    assert hyps[0].is_proposed_explanation is True
    assert hyps[0].total_score >= hyps[1].total_score


def test_api_get_case_graph():
    graph = get_case_graph("case_01_meridian")
    assert len(graph.nodes) > 0
    assert len(graph.edges) > 0


def test_api_get_report():
    rep = get_report("case_01_meridian")
    assert rep.case_id == "case_01_meridian"
    assert rep.proposed_explanation is not None
    assert len(rep.documents_analyzed) >= 8


def test_api_search_evidence():
    req = EvidenceSearchRequest(query="Server Room B keycard access", top_k=5)
    results = search_evidence("case_01_meridian", req)
    assert len(results) > 0
    assert any("Server Room B" in r.text for r in results)


def test_api_ask_question():
    req = AskQuestionRequest(question="Where was the USB flash drive inserted?", top_k=4)
    data = ask_question("case_01_meridian", req)
    assert data.answer is not None
    assert len(data.evidence) > 0


def test_api_report_downloads():
    res_md = download_report("case_01_meridian", format="markdown")
    assert res_md.status_code == 200
    assert b"# TEXT DETECTIVE" in res_md.body

    res_json = download_report("case_01_meridian", format="json")
    assert res_json.status_code == 200
    assert b"case_name" in res_json.body

    res_html = download_report("case_01_meridian", format="html")
    assert res_html.status_code == 200
    assert b"<!DOCTYPE html>" in res_html.body
