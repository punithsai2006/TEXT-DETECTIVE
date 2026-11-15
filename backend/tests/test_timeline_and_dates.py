from datetime import date, datetime, time
import pytest
from app.models.ground_truth_adapter import normalize_ground_truth_data, GroundTruthHypothesis
from app.models.schemas import ContradictionReviewRequest, DocumentMetadata, DocumentType, ReviewStatus
from app.services.extraction.date_parser import (
    extract_document_header_datetime,
    parse_date_string,
    parse_time_string,
    resolve_sentence_timestamp,
)
from app.services.extraction.extractor import extract_events_and_timeline
from app.api.routes import review_contradiction, upload_documents
from app.storage.case_store import case_store


def test_parse_date_formats():
    # 1. 19 Nov 2026
    d1 = parse_date_string("19 Nov 2026")
    assert d1 == date(2026, 11, 19)

    # 2. 19 November 2026
    d2 = parse_date_string("19 November 2026")
    assert d2 == date(2026, 11, 19)

    # 3. November 19, 2026
    d3 = parse_date_string("November 19, 2026")
    assert d3 == date(2026, 11, 19)

    # 4. Nov 19, 2026
    d4 = parse_date_string("Nov 19, 2026")
    assert d4 == date(2026, 11, 19)

    # 5. 2026-11-19
    d5 = parse_date_string("2026-11-19")
    assert d5 == date(2026, 11, 19)

    # 6. 19/11/2026
    d6 = parse_date_string("19/11/2026")
    assert d6 == date(2026, 11, 19)

    # 7. 19-11-2026
    d7 = parse_date_string("19-11-2026")
    assert d7 == date(2026, 11, 19)

    # Day + Month without year (inherits default year)
    d8 = parse_date_string("21 November", default_year=2026)
    assert d8 == date(2026, 11, 21)

    # Invalid date returns None, does not raise
    assert parse_date_string("not a valid date string") is None


def test_parse_time_formats_and_timezones():
    # 24h with seconds
    t1, raw1, tz1, prec1 = parse_time_string("18:16:33")
    assert t1 == time(18, 16, 33)
    assert prec1 == "second"

    # 12h with AM/PM
    t2, raw2, tz2, prec2 = parse_time_string("09:14 PM")
    assert t2 == time(21, 14, 0)
    assert prec2 == "minute"

    # With timezone
    t3, raw3, tz3, prec3 = parse_time_string("10:15 AM EST")
    assert t3 == time(10, 15, 0)
    assert tz3 == "EST"

    # Approximate time
    t4, raw4, tz4, prec4 = parse_time_string("around 03:30 PM")
    assert t4 == time(15, 30, 0)
    assert prec4 == "approximate"


def test_contextual_date_resolution():
    doc_date = date(2026, 11, 21)

    # Statement with time only inherits doc_date
    ts_obj, ctx = resolve_sentence_timestamp("09:02:15 - ENTRY - ACCESS_GRANTED", doc_date, doc_date)
    assert ts_obj.dt == datetime(2026, 11, 21, 9, 2, 15)
    assert ts_obj.is_date_inferred is True
    assert ts_obj.confidence >= 0.8
    assert "2026-11-21" in ts_obj.display_str

    # Statement with explicit different date overrides context
    ts_explicit, new_ctx = resolve_sentence_timestamp("On 22 November at 08:05 AM, incident reported", doc_date, doc_date)
    assert ts_explicit.dt == datetime(2026, 11, 22, 8, 5, 0)
    assert ts_explicit.is_date_inferred is False
    assert new_ctx == date(2026, 11, 22)

    # Time only without any document date context returns None for dt (never invents 2024-01-01)
    ts_unknown, _ = resolve_sentence_timestamp("At 14:00 something happened", None, None)
    assert ts_unknown.dt is None
    assert "(Date unspecified)" in ts_unknown.display_str
    assert ts_unknown.sort_key == "99999999999999"


def test_multi_day_chronology_and_sorting():
    # Documents spanning Nov 19, Nov 21, and Nov 22
    email_text = "From: Tom Reyes\nTo: Oliver Grant\nDate: 19 November 2026\nTime: 09:14 PM\nSubject: Valuation\nI would like to know what a buyer might pay."
    doc_email = DocumentMetadata(
        document_id="doc_email",
        case_id="case_test",
        filename="09_dealer_email.txt",
        document_type=DocumentType.EMAIL,
        cleaned_text=email_text,
        chunks=[],
    )

    log_text = "Date: 21 November 2026\n09:02:15 - SARAH_COLLINS - STAFF_DOOR - ENTRY - ACCESS_GRANTED\n18:31:20 - TOM_REYES - STAFF_DOOR - EXIT - ACCESS_GRANTED\nSYSTEM NOTE: System active."
    doc_log = DocumentMetadata(
        document_id="doc_log",
        case_id="case_test",
        filename="06_badge_access_log.txt",
        document_type=DocumentType.LOG,
        cleaned_text=log_text,
        chunks=[],
    )

    report_text = "Date: 22 November 2026\nAt 08:05 AM on 22 November 2026, head librarian Sarah Collins reported the map missing."
    doc_report = DocumentMetadata(
        document_id="doc_report",
        case_id="case_test",
        filename="01_incident_report.txt",
        document_type=DocumentType.REPORT,
        cleaned_text=report_text,
        chunks=[],
    )

    events, timeline, _ = extract_events_and_timeline(
        [doc_email, doc_log, doc_report],
        known_people={"Tom Reyes", "Sarah Collins", "Oliver Grant"},
        known_locations={"Staff Door"},
        known_objects={"map"},
    )

    # Verify chronological ordering across days:
    # 1. Nov 19 21:14
    # 2. Nov 21 09:02
    # 3. Nov 21 18:31
    # 4. Nov 22 08:05
    timestamps = [t.timestamp_display for t in timeline]
    assert len(timeline) >= 4

    assert "2026-11-19 21:14:00" in timestamps[0]
    assert "2026-11-21 09:02:15" in timestamps[1]
    assert "2026-11-21 18:31:20" in timestamps[2]
    assert "2026-11-22 08:05:00" in timestamps[3]


def test_cross_document_duplicate_event_merging():
    # Two documents recording the exact same event at 18:02 on Nov 21
    doc_log = DocumentMetadata(
        document_id="doc_log",
        case_id="case_test",
        filename="06_badge_access_log.txt",
        document_type=DocumentType.LOG,
        cleaned_text="Date: 21 November 2026\n18:02:19 - TOM_REYES - STAFF_DOOR - ENTRY - ACCESS_GRANTED",
        chunks=[],
    )
    doc_cctv = DocumentMetadata(
        document_id="doc_cctv",
        case_id="case_test",
        filename="08_cctv_review_report.txt",
        document_type=DocumentType.REPORT,
        cleaned_text="Review Date: 22 November 2026\nAt 06:02 PM on 21 November, a person wearing a gray coat entered through the staff door.",
        chunks=[],
    )

    events, timeline, _ = extract_events_and_timeline(
        [doc_log, doc_cctv],
        known_people={"Tom Reyes"},
        known_locations={"Staff Door"},
        known_objects=set(),
    )

    # Should be merged into a single event with secondary sources preserved
    assert len(timeline) == 1
    assert len(timeline[0].secondary_sources) == 1
    assert timeline[0].secondary_sources[0]["document_name"] == "08_cctv_review_report.txt"


def test_ground_truth_schema_adapter_string_decoys():
    # Raw ground truth where decoys are represented as plain strings
    raw_gt = {
        "case_id": "case_test_schema",
        "case_name": "Schema Test Case",
        "correct_hypothesis": {
            "title": "Suspect A committed theft",
            "description": "Full description of suspect A action",
            "is_correct": True,
        },
        "decoy_hypotheses": [
            "Decoy B was acting suspiciously but innocent",
            "Decoy C had no access to the vault",
        ],
    }

    normalized = normalize_ground_truth_data(raw_gt)
    assert normalized.case_id == "case_test_schema"
    assert len(normalized.decoy_hypotheses) == 2
    assert isinstance(normalized.decoy_hypotheses[0], GroundTruthHypothesis)
    assert normalized.decoy_hypotheses[0].title == "Decoy B was acting suspiciously but innocent"
    assert normalized.decoy_hypotheses[0].is_correct is False


def test_contradiction_review_workflow_all_three_states():
    # Verify review_contradiction route transitions through pending, confirmed, and rejected
    case_id = "case_01_meridian"
    contras = case_store.get_contradictions(case_id)
    assert len(contras) > 0
    contra_id = contras[0].id

    # 1. Confirm
    req_confirm = ContradictionReviewRequest(
        review_status=ReviewStatus.CONFIRMED,
        reviewer_id="lead_analyst",
        review_notes="Verified against badge logs",
    )
    res_c = review_contradiction(case_id, contra_id, req_confirm)
    assert res_c.review_status == ReviewStatus.CONFIRMED
    assert res_c.reviewer_id == "lead_analyst"

    # 2. Reject
    req_reject = ContradictionReviewRequest(
        review_status=ReviewStatus.REJECTED,
        reviewer_id="lead_analyst",
        review_notes="False positive due to timezone offset",
    )
    res_r = review_contradiction(case_id, contra_id, req_reject)
    assert res_r.review_status == ReviewStatus.REJECTED
    assert res_r.reviewer_id == "lead_analyst"

    # 3. Reset to Pending
    req_pending = ContradictionReviewRequest(
        review_status=ReviewStatus.PENDING_REVIEW,
        reviewer_id="lead_analyst",
        review_notes="Needs additional sensor log review",
    )
    res_p = review_contradiction(case_id, contra_id, req_pending)
    assert res_p.review_status == ReviewStatus.PENDING_REVIEW
