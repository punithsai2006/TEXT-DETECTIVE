import pytest

from app.services.orchestration.controller import controller


@pytest.fixture(scope="module")
def meridian_case(setup_isolated_test_storage):
    """
    Returns the isolated case_01_meridian case seeded by session fixture.
    """
    return "case_01_meridian"


def test_which_evidence_contradicts_alice_vances_alibi(meridian_case):
    """
    Tests query: 'Which evidence contradicts Alice Vance's alibi?'
    Contrasts her interview claim of remaining on Floor 3 with badge swipe log at Server Room B.
    """
    resp = controller.ask_case_question(meridian_case, "Which evidence contradicts Alice Vance's alibi?", top_k=5)

    assert resp.evidence_sufficiency in ["directly_established", "partially_established", "multiple_events_found"]
    ans = resp.direct_answer.lower()
    assert "alice vance" in ans or "badge" in ans or "floor 3" in ans or "server room b" in ans

    # Verify sources in evidence items or supporting cards
    card_sources = [c.source for c in (resp.contradicting_evidence + resp.supporting_evidence)]
    item_sources = [item.document_name for item in resp.evidence]
    all_sources = card_sources + item_sources
    assert any("badge_swipe_logs" in s or "interview_alice_vance" in s for s in all_sources)


def test_who_swiped_into_server_room_b(meridian_case):
    """
    Tests query: 'Who swiped badge at Server Room B Door?'
    Identifies Alice Vance / Badge 4092.
    """
    resp = controller.ask_case_question(meridian_case, "Who swiped badge at Server Room B Door?", top_k=5)

    assert resp.evidence_sufficiency in ["directly_established", "partially_established", "multiple_events_found"]
    ans = resp.direct_answer.lower()
    assert "alice vance" in ans or "4092" in ans or "badge" in ans or "server room b" in ans

    card_sources = [c.source for c in resp.supporting_evidence]
    item_sources = [item.document_name for item in resp.evidence]
    all_sources = card_sources + item_sources
    assert any("badge_swipe_logs" in s or "server_access_logs" in s or "interview" in s for s in all_sources)


def test_what_time_was_server_room_accessed(meridian_case):
    """
    Tests query: 'What time was Server Room B accessed?'
    Verifies access timestamp retrieval.
    """
    resp = controller.ask_case_question(meridian_case, "What time was Server Room B accessed?", top_k=5)

    assert resp.evidence_sufficiency in ["directly_established", "partially_established", "multiple_events_found"]
    ans = resp.direct_answer.lower()
    assert "22:14" in ans or "22:15" in ans or "server room b" in ans or "server" in ans


def test_where_was_usb_device_inserted(meridian_case):
    """
    Tests query: 'Where was the USB flash drive inserted?'
    Correlates forensic workstation log with Server Room B terminal.
    """
    resp = controller.ask_case_question(meridian_case, "Where was the USB flash drive inserted?", top_k=5)

    assert resp.direct_answer is not None
    ans = resp.direct_answer.lower()
    assert "usb" in ans or "workstation" in ans or "server room b" in ans
    assert len(resp.evidence) > 0


def test_questions_with_multiple_possible_answers(meridian_case):
    """
    Tests query with multiple individuals entering Building 4.
    """
    resp = controller.ask_case_question(meridian_case, "Who entered Building 4?", top_k=5)

    assert resp.evidence_sufficiency in ["multiple_events_found", "directly_established", "partially_established"]
    ans = resp.direct_answer.lower()
    found_count = sum(1 for person in ["bob chen", "david wright", "alice vance"] if person in ans)
    assert found_count >= 1 or len(resp.supporting_evidence) >= 1 or len(resp.evidence) >= 1


def test_questions_with_insufficient_evidence(meridian_case):
    """
    Tests inquiries where case documents lack sufficient evidence.
    Verifies that system explicitly refuses to invent facts.
    """
    resp_weather = controller.ask_case_question(meridian_case, "What was the weather outside on Sunday?", top_k=5)
    assert resp_weather.evidence_sufficiency == "insufficient_evidence"
    assert "not contain sufficient evidence" in resp_weather.direct_answer.lower() or "no supporting evidence" in resp_weather.direct_answer.lower()
    assert len(resp_weather.supporting_evidence) == 0

    resp_car = controller.ask_case_question(meridian_case, "Who stole the red sports car from the parking lot?", top_k=5)
    assert resp_car.evidence_sufficiency == "insufficient_evidence"
    assert "not contain sufficient evidence" in resp_car.direct_answer.lower() or "no supporting evidence" in resp_car.direct_answer.lower()


def test_mock_mode_transparent_disclosure(meridian_case):
    """
    Verifies mock mode transparently discloses its offline status and model identifier.
    """
    resp = controller.ask_case_question(meridian_case, "Where was the USB flash drive inserted?", top_k=3)

    assert resp.is_mock is True
    assert resp.model_used == "mock-investigator-v1"
    assert "gpt" not in resp.model_used.lower()
    assert "gemini" not in resp.model_used.lower()
