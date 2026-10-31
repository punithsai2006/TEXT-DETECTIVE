import os
import shutil
import tempfile
from pathlib import Path
import pytest

from app.models.schemas import (
    CaseCreateRequest,
    ContradictionItem,
    ContradictionType,
    DocumentType,
    EntityType,
    Hypothesis,
    NLILabel,
    TextChunk,
)
from app.services.contradiction.detector import contradiction_detector
from app.services.extraction.extractor import (
    extract_entities_from_text,
    extract_events_and_timeline,
    parse_timestamp_from_text,
    run_extraction_pipeline,
)
from app.services.hypothesis.scorer import (
    compute_exact_hypothesis_score,
    decompose_hypothesis_into_claims,
    hypothesis_engine,
)
from app.services.ingestion.preprocessor import (
    chunk_document,
    detect_document_type,
    normalize_whitespace_and_noise,
    process_uploaded_file,
    split_into_sentences,
)
from app.services.llm_provider import MockLLMProvider, get_llm_provider
from app.services.orchestration.controller import controller
from app.services.reporting.reporter import (
    export_report_to_json,
    export_report_to_markdown,
    generate_investigation_report,
)
from app.services.retrieval.retriever import retriever
from app.storage.case_store import CaseStore


# ==========================================
# 1. HYPOTHESIS SCORING TESTS (SLIDE 18)
# ==========================================

def test_exact_hypothesis_scoring_formula():
    """
    REQUIRED UNIT TEST FROM SPECIFICATION & SLIDE 18:
    Support = 3
    Conflict = 1
    Corroboration = 1
    ConflictPenalty = 0
    Expected score = 3
    Formula: Score(H) = Support - Conflict + Corroboration - ConflictPenalty
    """
    support = 3
    conflict = 1
    corroboration = 1
    conflict_penalty = 0

    score = compute_exact_hypothesis_score(
        support=support,
        conflict=conflict,
        corroboration=corroboration,
        conflict_penalty=conflict_penalty
    )

    assert score == 3, f"Expected score 3, got {score}"


def test_hypothesis_scoring_variations():
    # High conflict scenario
    score_penalty = compute_exact_hypothesis_score(support=2, conflict=4, corroboration=0, conflict_penalty=2)
    assert score_penalty == -4

    # High corroboration scenario
    score_corrob = compute_exact_hypothesis_score(support=5, conflict=0, corroboration=3, conflict_penalty=0)
    assert score_corrob == 8


def test_hypothesis_ranking_order_and_ties():
    h1 = Hypothesis(
        hypothesis_id="h1", case_id="c1", title="Hyp 1", description="Desc 1",
        support_score=4, conflict_score=1, corroboration_score=1, conflict_penalty=0, total_score=4
    )
    h2 = Hypothesis(
        hypothesis_id="h2", case_id="c1", title="Hyp 2", description="Desc 2",
        support_score=6, conflict_score=0, corroboration_score=2, conflict_penalty=0, total_score=8
    )
    h3 = Hypothesis(
        hypothesis_id="h3", case_id="c1", title="Hyp 3", description="Desc 3",
        support_score=1, conflict_score=3, corroboration_score=0, conflict_penalty=1, total_score=-3
    )

    ranked = hypothesis_engine.rank_hypotheses([h1, h2, h3])

    assert ranked[0].hypothesis_id == "h2"
    assert ranked[0].rank == 1
    assert ranked[0].is_proposed_explanation is True
    assert ranked[1].hypothesis_id == "h1"
    assert ranked[2].hypothesis_id == "h3"
    assert ranked[2].is_proposed_explanation is False


def test_hypothesis_ambiguity_warning_on_tie():
    h1 = Hypothesis(
        hypothesis_id="h1", case_id="c1", title="Hyp 1", description="Desc 1", total_score=5
    )
    h2 = Hypothesis(
        hypothesis_id="h2", case_id="c1", title="Hyp 2", description="Desc 2", total_score=5
    )

    ranked = hypothesis_engine.rank_hypotheses([h1, h2])
    assert ranked[0].uncertainty_warning is not None
    assert "identical score" in ranked[0].uncertainty_warning


# ==========================================
# 2. INGESTION & PREPROCESSING TESTS (MODULE 1)
# ==========================================

def test_normalize_whitespace_and_noise():
    raw = "Line 1.\r\nLine 2.\u00a0\u200b   With extra  spaces.\n\n\n\nLine 3."
    cleaned = normalize_whitespace_and_noise(raw)
    assert "\r" not in cleaned
    assert "\u200b" not in cleaned
    assert "\u00a0" not in cleaned
    assert "Line 1.\nLine 2.    With extra  spaces.\n\nLine 3." == cleaned


def test_sentence_splitting_with_abbreviations():
    text = "Dr. Alice Vance met with Mr. Chen at 10:15 p.m. at Meridian Tech Inc. They reviewed the incident."
    sentences = split_into_sentences(text)
    assert len(sentences) == 2
    assert sentences[0] == "Dr. Alice Vance met with Mr. Chen at 10:15 p.m. at Meridian Tech Inc."
    assert sentences[1] == "They reviewed the incident."


def test_detect_document_type():
    assert detect_document_type("interview_alice.txt", "Q: Where were you?\nA: At home.") == DocumentType.INTERVIEW
    assert detect_document_type("email_alert.txt", "From: bob@corp.com\nTo: alice@corp.com\nSubject: Help") == DocumentType.EMAIL
    assert detect_document_type("badge_swipe_logs.txt", "[2024-10-12 22:14:30] Reader: Server Room B Door - ACCESS GRANTED") == DocumentType.LOG
    assert detect_document_type("forensic_report.txt", "Incident Report: Executive summary of findings") == DocumentType.REPORT


def test_chunking_preserves_metadata():
    text = "Sentence one about the suspect. Sentence two about the location. Sentence three about the escape."
    chunks = chunk_document(
        case_id="case_test",
        document_id="doc_test",
        filename="test.txt",
        document_type=DocumentType.REPORT,
        cleaned_text=text,
        speaker="Inspector Gadget",
        timestamp="2024-10-12 10:00",
        chunk_size_sentences=2,
    )
    assert len(chunks) == 2
    assert chunks[0].speaker == "Inspector Gadget"
    assert chunks[0].timestamp == "2024-10-12 10:00"
    assert chunks[0].sentence_indices == [0, 1]
    assert chunks[1].sentence_indices == [2]


def test_empty_file_validation(tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="is empty"):
        process_uploaded_file("c1", empty_file, "empty.txt")


def test_unsupported_file_format(tmp_path):
    fake_exe = tmp_path / "malware.exe"
    fake_exe.write_bytes(b"MZ12345")
    with pytest.raises(ValueError, match="Unsupported file format"):
        process_uploaded_file("c1", fake_exe, "malware.exe")


# ==========================================
# 3. EXTRACTION TESTS (MODULE 2)
# ==========================================

def test_entity_extraction_types():
    text = "Alice Vance arrived at Server Room B carrying a Kingston USB flash drive for Meridian Tech."
    entities = extract_entities_from_text(text, "doc_1")

    # Person
    assert any("alice vance" in k for k in entities.keys())
    # Location
    assert any("server room" in k for k in entities.keys())
    # Organization
    assert any("meridian tech" in k for k in entities.keys())
    # Object
    assert any("usb" in k or "drive" in k for k in entities.keys())


def test_temporal_parsing():
    raw_time, dt, uncertain = parse_timestamp_from_text("The incident occurred at 10:15 PM in the lab.")
    assert raw_time == "10:15 PM"
    assert dt is not None
    assert dt.hour == 22 and dt.minute == 15
    assert uncertain is False

    raw_iso, dt_iso, _ = parse_timestamp_from_text("Event logged at 2024-10-12 22:14:30 in audit record.")
    assert "2024-10-12 22:14:30" in raw_iso
    assert dt_iso is not None
    assert dt_iso.year == 2024


# ==========================================
# 4. EVIDENCE RETRIEVAL TESTS (MODULE 3)
# ==========================================

def test_retriever_case_isolation(tmp_path):
    temp_store = tmp_path / "chroma"
    from app.services.retrieval.retriever import HybridRetriever
    r = HybridRetriever(storage_dir=temp_store)

    doc_case_a = TextChunk(
        chunk_id="c_a1", case_id="case_A", document_id="doc_a", filename="a.txt",
        document_type=DocumentType.REPORT, text="David Wright had a Kingston USB flash drive.",
        sentence_indices=[0]
    )
    doc_case_b = TextChunk(
        chunk_id="c_b1", case_id="case_B", document_id="doc_b", filename="b.txt",
        document_type=DocumentType.REPORT, text="Julian Vance entered the gallery vault at Blackwood.",
        sentence_indices=[0]
    )

    from app.models.schemas import DocumentMetadata
    dm_a = DocumentMetadata(
        document_id="doc_a", case_id="case_A", filename="a.txt", document_type=DocumentType.REPORT,
        chunks=[doc_case_a], raw_text=doc_case_a.text, cleaned_text=doc_case_a.text
    )
    dm_b = DocumentMetadata(
        document_id="doc_b", case_id="case_B", filename="b.txt", document_type=DocumentType.REPORT,
        chunks=[doc_case_b], raw_text=doc_case_b.text, cleaned_text=doc_case_b.text
    )

    r.index_case_chunks("case_A", [dm_a])
    r.index_case_chunks("case_B", [dm_b])

    # Search in case_A should never find content from case_B
    results_a = r.search("case_A", "Blackwood gallery vault")
    assert not any("Blackwood" in res.text for res in results_a)

    results_b = r.search("case_B", "Kingston USB")
    assert not any("Kingston" in res.text for res in results_b)


# ==========================================
# 5. CONTRADICTION TESTS (MODULE 4)
# ==========================================

def test_contradiction_detection_confirmed_and_agreements():
    # Direct contradiction on door lock
    stmt1 = "The security door was locked and secured at 10:00 PM."
    stmt2 = "The door latch pin was taped down, leaving the room open and unlocked."
    label, c_type, conf, expl = contradiction_detector.evaluate_pair(stmt1, stmt2)

    assert label == NLILabel.CONTRADICTION
    assert c_type == ContradictionType.CONFIRMED_CONTRADICTION
    assert conf >= 0.85

    # Direct agreement
    stmt3 = "Julian Vance arrived at the security booth at 7:00 PM."
    stmt4 = "Julian Vance arrived at the security booth at 7:00 PM."
    label_agr, c_type_agr, _, _ = contradiction_detector.evaluate_pair(stmt3, stmt4)
    assert label_agr == NLILabel.ENTAILMENT
    assert c_type_agr == ContradictionType.AGREEMENT


# ==========================================
# 6. REPORT GENERATION & EXPORTS (MODULE 6)
# ==========================================

def test_report_generation_and_markdown_export():
    from app.models.schemas import Case, CaseStatus
    case = Case(
        case_id="case_test", name="Test Case", description="Test Description", status=CaseStatus.COMPLETED
    )
    report = generate_investigation_report(
        case=case, documents=[], entities=[], events=[], timeline=[],
        key_evidence=[], contradictions=[], hypotheses=[]
    )

    md = export_report_to_markdown(report)
    js = export_report_to_json(report)

    assert "# TEXT DETECTIVE INVESTIGATION REPORT" in md
    assert "Test Case" in md
    assert "LIMITATIONS & UNCERTAINTY" in md
    assert '"case_name": "Test Case"' in js


# ==========================================
# 7. CONTROLLER QUESTION ANSWERING
# ==========================================

def test_ask_question_with_no_evidence():
    resp = controller.ask_case_question(case_id="non_existent_case", question="Who did it?")
    assert "No supporting evidence found" in resp.answer
    assert len(resp.evidence) == 0
