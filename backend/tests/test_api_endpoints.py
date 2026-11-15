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


def test_api_provenance_validation():
    from app.api.routes import validate_case_provenance
    val_rep = validate_case_provenance("case_01_meridian")
    assert val_rep.case_id == "case_01_meridian"
    assert val_rep.is_valid is True
    assert val_rep.passed_checks > 0


def test_api_contradiction_review():
    from app.api.routes import review_contradiction
    from app.models.schemas import ContradictionReviewRequest, ReviewStatus
    conflicts = get_case_contradictions("case_01_meridian")
    assert len(conflicts) > 0
    cid = conflicts[0].id

    req = ContradictionReviewRequest(
        review_status=ReviewStatus.CONFIRMED,
        reviewer_id="lead_investigator_1",
        review_notes="Cross-referenced with physical telemetry logs.",
    )
    updated = review_contradiction("case_01_meridian", cid, req)
    assert updated.review_status == ReviewStatus.CONFIRMED
    assert updated.reviewer_id == "lead_investigator_1"


    res_html = download_report("case_01_meridian", format="html")
    assert res_html.status_code == 200
    assert b"<!DOCTYPE html>" in res_html.body


def test_api_upload_ground_truth_rejected():
    from io import BytesIO
    from fastapi import UploadFile, HTTPException
    from app.api.routes import upload_documents

    gt_payload = b'{"case_id": "fake", "correct_hypothesis": {"title": "X"}, "planted_contradictions": []}'
    mock_file = UploadFile(filename="ground_truth_test.json", file=BytesIO(gt_payload))

    with pytest.raises(HTTPException) as exc_info:
        upload_documents("case_01_meridian", files=[mock_file])
    assert exc_info.value.status_code == 400
    assert "ground-truth" in exc_info.value.detail.lower()


def test_api_upload_unsupported_extension_rejected():
    from io import BytesIO
    from fastapi import UploadFile, HTTPException
    from app.api.routes import upload_documents

    mock_file = UploadFile(filename="malicious_payload.exe", file=BytesIO(b"binary data"))
    with pytest.raises(HTTPException) as exc_info:
        upload_documents("case_01_meridian", files=[mock_file])
    assert exc_info.value.status_code == 400
    assert "unsupported file extension" in exc_info.value.detail.lower()


def test_api_empty_case_handling():
    from app.api.routes import create_case, delete_case
    from app.models.schemas import CaseCreateRequest

    req = CaseCreateRequest(name="Empty Test Case", description="Testing clean handling of empty cases.")
    new_case = create_case(req)
    cid = new_case.case_id

    try:
        assert get_case(cid).case_id == cid
        assert get_case_documents(cid) == []
        assert get_case_timeline(cid) == []
        assert get_case_contradictions(cid) == []
        assert get_case_hypotheses(cid) == []
    finally:
        delete_case(cid)


def test_api_hypothesis_scoring_formula():
    from app.services.hypothesis.scorer import compute_exact_hypothesis_score

    # Formula from Slide 18: Score(H) = Support - Conflict + Corroboration - ConflictPenalty
    assert compute_exact_hypothesis_score(support=10, conflict=2, corroboration=3, conflict_penalty=1) == 10
    assert compute_exact_hypothesis_score(support=5, conflict=5, corroboration=2, conflict_penalty=2) == 0
    assert compute_exact_hypothesis_score(support=0, conflict=3, corroboration=0, conflict_penalty=2) == -5
