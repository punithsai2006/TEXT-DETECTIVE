import shutil
from pathlib import Path
import pytest

from app.services.ingestion.preprocessor import process_uploaded_file
from app.services.orchestration.controller import controller
from app.storage.case_store import case_store


@pytest.fixture(scope="module")
def lakeview_case(setup_isolated_test_storage):
    """
    Seeds case_05_lakeview into the isolated test storage for Ask AI Assistant tests.
    """
    case_id = "case_05_lakeview"
    existing = case_store.get_case(case_id)
    if not existing:
        case_store.create_case(
            name="The Lakeview Library Rare Map Theft",
            description="Theft of antique survey map from Rare Maps Room.",
            is_demo=True,
            custom_id=case_id,
        )

    base_data = Path(__file__).resolve().parent.parent.parent / "data" / "sample_cases" / "case_05_lakeview"
    uploads_dir = case_store.uploads_dir / case_id
    uploads_dir.mkdir(parents=True, exist_ok=True)

    if base_data.exists():
        for file_path in sorted(base_data.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in {".txt", ".log", ".csv"}:
                dest = uploads_dir / file_path.name
                shutil.copyfile(file_path, dest)
                doc_meta = process_uploaded_file(
                    case_id=case_id,
                    file_path=dest,
                    original_filename=file_path.name,
                )
                case_store.add_document(case_id, doc_meta)

        controller.run_investigation(case_id=case_id)

    return case_id


def test_who_opened_display_case_distinguishes_events(lakeview_case):
    """
    Tests that 'Who opened the display case?' explicitly distinguishes:
    1. Sarah Collins opening for photography at ~3:30 PM.
    2. KEY_02 unlocking at 18:16:33 during the after-hours incident window.
    """
    resp = controller.ask_case_question(lakeview_case, "Who opened the display case?", top_k=5)

    assert resp.evidence_sufficiency == "partially_established"
    assert "sarah collins" in resp.direct_answer.lower()
    assert "3:30 pm" in resp.direct_answer.lower() or "03:30 pm" in resp.direct_answer.lower()
    assert "key_02" in resp.direct_answer.lower()
    assert "18:16:33" in resp.direct_answer.lower()
    assert "tom reyes" in resp.direct_answer.lower()

    # Verify supporting evidence citations
    assert len(resp.supporting_evidence) >= 2
    sources = [se.source for se in resp.supporting_evidence]
    assert any("02_interview_sarah_collins" in s for s in sources)
    assert any("07_alarm_and_case_lock_log" in s for s in sources)

    # Verify important limitation highlights key vs operator distinction
    assert resp.important_limitations is not None
    assert "theft" in resp.important_limitations.lower() or "photograph" in resp.important_limitations.lower()


def test_who_entered_building_at_602_pm(lakeview_case):
    """
    Tests query: 'Who entered the building at 6:02 PM?'
    Correlates staff door access log (18:02:19 Tom Reyes) with exterior CCTV (06:02 PM).
    """
    resp = controller.ask_case_question(lakeview_case, "Who entered the building at 6:02 PM?", top_k=5)

    assert resp.evidence_sufficiency == "directly_established"
    assert "tom reyes" in resp.direct_answer.lower()
    assert "18:02:19" in resp.direct_answer or "6:02" in resp.direct_answer.lower()

    sources = [se.source for se in resp.supporting_evidence]
    assert any("06_badge_access_log" in s for s in sources)
    assert any("08_cctv_review_report" in s for s in sources)


def test_what_time_was_case_unlocked(lakeview_case):
    """
    Tests query: 'What time was the case unlocked?'
    Identifies 10:00:22, 15:30:05, and 18:16:33 unlock events.
    """
    resp = controller.ask_case_question(lakeview_case, "What time was the case unlocked?", top_k=5)

    assert resp.evidence_sufficiency == "directly_established"
    assert "10:00:22" in resp.direct_answer
    assert "15:30:05" in resp.direct_answer
    assert "18:16:33" in resp.direct_answer

    sources = [se.source for se in resp.supporting_evidence]
    assert any("07_alarm_and_case_lock_log" in s for s in sources)


def test_who_was_carrying_long_tube(lakeview_case):
    """
    Tests query: 'Who was carrying the long tube?'
    Correlates Greg Hall eyewitness testimony (06:29 PM) and CCTV (06:31 PM).
    """
    resp = controller.ask_case_question(lakeview_case, "Who was carrying the long tube?", top_k=5)

    assert resp.evidence_sufficiency == "directly_established"
    assert "tom reyes" in resp.direct_answer.lower()
    assert "greg hall" in resp.direct_answer.lower()

    sources = [se.source for se in resp.supporting_evidence]
    assert any("05_interview_greg_hall" in s for s in sources)
    assert any("08_cctv_review_report" in s for s in sources)


def test_which_evidence_contradicts_toms_alibi(lakeview_case):
    """
    Tests query: 'Which evidence contradicts Tom's alibi?'
    Contrasts 05:30 PM departure claim with door badge, alarm/lock logs, witness, and CCTV.
    """
    resp = controller.ask_case_question(lakeview_case, "Which evidence contradicts Tom's alibi?", top_k=5)

    assert resp.evidence_sufficiency == "directly_established"
    assert "05:30 pm" in resp.direct_answer.lower()
    assert "18:02" in resp.direct_answer or "18:02:19" in resp.direct_answer
    assert "18:16:33" in resp.direct_answer or "key_02" in resp.direct_answer.lower()

    assert len(resp.contradicting_evidence) >= 2
    contra_sources = [ce.source for ce in resp.contradicting_evidence]
    assert any("06_badge_access_log" in s for s in contra_sources)
    assert any("07_alarm_and_case_lock_log" in s for s in contra_sources)


def test_questions_with_insufficient_evidence(lakeview_case):
    """
    Tests inquiries where case documents lack sufficient evidence.
    Verifies that system explicitly refuses to invent facts.
    """
    resp_weather = controller.ask_case_question(lakeview_case, "What was the weather outside on Sunday?", top_k=5)
    assert resp_weather.evidence_sufficiency == "insufficient_evidence"
    assert "not contain sufficient evidence" in resp_weather.direct_answer.lower()
    assert len(resp_weather.supporting_evidence) == 0

    resp_car = controller.ask_case_question(lakeview_case, "Who stole the red sports car from the parking lot?", top_k=5)
    assert resp_car.evidence_sufficiency == "insufficient_evidence"
    assert "not contain sufficient evidence" in resp_car.direct_answer.lower() or "no supporting evidence" in resp_car.direct_answer.lower()


def test_questions_with_multiple_possible_answers(lakeview_case):
    """
    Tests questions with multiple matching entities (e.g. access permissions).
    """
    resp = controller.ask_case_question(lakeview_case, "Who had access to the Rare Maps Room?", top_k=5)

    assert resp.evidence_sufficiency in ["multiple_events_found", "directly_established"]
    assert "sarah collins" in resp.direct_answer.lower()
    assert "tom reyes" in resp.direct_answer.lower()
    assert "nina patel" in resp.direct_answer.lower()
    assert "greg hall" in resp.direct_answer.lower()


def test_meridian_usb_question_generalization():
    """
    Ensures question answering generalizes domain-agnostically to other cases (case_01_meridian).
    """
    resp = controller.ask_case_question("case_01_meridian", "Where was the USB flash drive inserted?", top_k=4)

    assert resp.direct_answer is not None
    assert "usb" in resp.direct_answer.lower()
    assert len(resp.evidence) > 0


def test_mock_mode_transparent_disclosure(lakeview_case):
    """
    Verifies mock mode transparently discloses its offline status and model identifier.
    """
    resp = controller.ask_case_question(lakeview_case, "Who opened the display case?", top_k=3)

    assert resp.is_mock is True
    assert resp.model_used == "mock-investigator-v1"
    assert "gpt" not in resp.model_used.lower()
    assert "gemini" not in resp.model_used.lower()
