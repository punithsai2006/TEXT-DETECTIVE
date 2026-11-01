from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def get_utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ==========================================
# ENUMS & CONSTANTS
# ==========================================

class DocumentType(str, Enum):
    INTERVIEW = "interview"
    EMAIL = "email"
    REPORT = "report"
    LOG = "log"
    OTHER = "other"


class EntityType(str, Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    OBJECT = "object"


class TemporalRelation(str, Enum):
    BEFORE = "before"
    AFTER = "after"
    OVERLAP = "overlap"
    SAME_TIME = "same_time"
    UNKNOWN = "unknown"


class NLILabel(str, Enum):
    CONTRADICTION = "contradiction"
    ENTAILMENT = "entailment"
    NEUTRAL = "neutral"


class ContradictionType(str, Enum):
    CONFIRMED_CONTRADICTION = "confirmed_contradiction"
    POSSIBLE_CONTRADICTION = "possible_contradiction"
    AGREEMENT = "agreement"
    NEUTRAL = "neutral"


class ReviewStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    NEEDS_FURTHER_INVESTIGATION = "needs_further_investigation"


class EvidenceClassification(str, Enum):
    DIRECT_FACT = "direct_fact"
    SUPPORTING_EVIDENCE = "supporting_evidence"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    INCONCLUSIVE_EVIDENCE = "inconclusive_evidence"
    MODEL_INTERPRETATION = "model_interpretation"
    SYSTEM_INFERENCE = "system_inference"


class CaseStatus(str, Enum):
    CREATED = "created"
    INGESTING = "ingesting"
    EXTRACTING = "extracting"
    RETRIEVING = "retrieving"
    CHECKING_CONTRADICTIONS = "checking_contradictions"
    SCORING_HYPOTHESES = "scoring_hypotheses"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    OUTDATED = "outdated"
    FAILED = "failed"


# ==========================================
# MODULE 1: INGESTION & CHUNKS
# ==========================================

class TextChunk(BaseModel):
    chunk_id: str
    case_id: str
    document_id: str
    filename: str
    document_type: DocumentType
    speaker: Optional[str] = None
    timestamp: Optional[str] = None
    page_number: Optional[int] = None
    text: str
    sentence_indices: List[int] = Field(default_factory=list)
    char_start: int = 0
    char_end: int = 0


class DocumentMetadata(BaseModel):
    document_id: str
    case_id: str
    filename: str
    document_type: DocumentType
    speaker: Optional[str] = None
    author: Optional[str] = None
    timestamp: Optional[str] = None
    description: Optional[str] = None
    file_size_bytes: int = 0
    sha256_hash: str = ""
    raw_text: str = ""
    cleaned_text: str = ""
    chunks: List[TextChunk] = Field(default_factory=list)
    uploaded_at: str = Field(default_factory=get_utc_now_iso)
    status: str = "processed"
    warning: Optional[str] = None


# ==========================================
# MODULE 2: EXTRACTION, TIMELINE & CASE GRAPH
# ==========================================

class Entity(BaseModel):
    entity_id: str
    name: str
    entity_type: EntityType
    mentions_count: int = 1
    document_ids: List[str] = Field(default_factory=list)
    source_sentences: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Event(BaseModel):
    event_id: str
    description: str
    participants: List[str] = Field(default_factory=list)  # Person names or entity_ids
    location: Optional[str] = None
    time_str: Optional[str] = None
    parsed_timestamp: Optional[str] = None
    uses_objects: List[str] = Field(default_factory=list)
    document_id: str
    document_name: str
    chunk_id: Optional[str] = None
    sentence_idx: Optional[int] = None
    char_start: int = 0
    char_end: int = 0
    source_sentence: str
    uncertainty: bool = False


class TemporalLink(BaseModel):
    source_event_id: str
    target_event_id: str
    relation: TemporalRelation
    source_sentence: str


class TimelineEntry(BaseModel):
    entry_id: str
    event_id: str
    timestamp_display: str
    event_description: str
    participants: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    document_name: str
    document_type: DocumentType
    document_id: Optional[str] = None
    chunk_id: Optional[str] = None
    sentence_idx: Optional[int] = None
    char_start: int = 0
    char_end: int = 0
    source_sentence: str
    is_uncertain: bool = False
    sort_key: str = ""


class CaseGraphNode(BaseModel):
    id: str
    label: str
    node_type: str  # entity (person, organization, location, object), event, document, time
    sub_type: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class CaseGraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation: str  # stated_in, involved_in, works_for, before, after, overlap, same_time, occurs_at_time, located_at, uses, provides_evidence
    evidence_sentence: Optional[str] = None


class CaseGraph(BaseModel):
    nodes: List[CaseGraphNode] = Field(default_factory=list)
    edges: List[CaseGraphEdge] = Field(default_factory=list)


# ==========================================
# MODULE 3: EVIDENCE RETRIEVAL
# ==========================================

class EvidenceItem(BaseModel):
    evidence_id: str
    case_id: str
    document_id: str
    document_name: str
    document_type: DocumentType
    chunk_id: str
    text: str
    speaker: Optional[str] = None
    timestamp: Optional[str] = None
    sentence_indices: List[int] = Field(default_factory=list)
    char_start: int = 0
    char_end: int = 0
    page_number: Optional[int] = None
    score: float
    retrieval_method: str = "hybrid"  # semantic, keyword, hybrid
    classification: EvidenceClassification = EvidenceClassification.SUPPORTING_EVIDENCE


class EvidenceSearchRequest(BaseModel):
    query: str
    top_k: int = 10
    document_ids: Optional[List[str]] = None
    threshold: Optional[float] = 0.0


# ==========================================
# MODULE 4: CONTRADICTION & LINKING
# ==========================================

class ContradictionItem(BaseModel):
    id: str
    case_id: str
    statement_a: str
    statement_b: str
    doc_a_id: str
    doc_b_id: str
    doc_a_name: str
    doc_b_name: str
    chunk_a_id: Optional[str] = None
    chunk_b_id: Optional[str] = None
    sentence_a_idx: Optional[int] = None
    sentence_b_idx: Optional[int] = None
    speaker_a: Optional[str] = None
    speaker_b: Optional[str] = None
    timestamp_a: Optional[str] = None
    timestamp_b: Optional[str] = None
    entity_event_link: str
    contradiction_type: ContradictionType
    nli_label: NLILabel
    confidence: float
    calculation_source: str = "cross_encoder_nli_and_conflict_rules"
    detection_engine: str = "rules"  # nli, rules, llm_verified
    explanation: str
    resolution_status: str = "unresolved"  # unresolved, resolved, investigating
    review_status: ReviewStatus = ReviewStatus.PENDING_REVIEW
    reviewer_id: Optional[str] = None
    review_timestamp: Optional[str] = None
    previous_review_status: Optional[str] = None
    review_notes: Optional[str] = None
    source_sentences: List[str] = Field(default_factory=list)


class ContradictionReviewRequest(BaseModel):
    review_status: ReviewStatus
    reviewer_id: Optional[str] = "analyst_1"
    review_notes: Optional[str] = None


# ==========================================
# MODULE 5: HYPOTHESES & SCORING
# ==========================================

class HypothesisClaim(BaseModel):
    claim_id: str
    text: str
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    conflicting_evidence_ids: List[str] = Field(default_factory=list)
    contributing_documents: List[str] = Field(default_factory=list)
    contributing_speakers: List[str] = Field(default_factory=list)
    is_corroborated: bool = False
    unresolved_conflicts_count: int = 0


class Hypothesis(BaseModel):
    hypothesis_id: str
    case_id: str
    title: str
    description: str
    origin: str = "user"  # user, generated
    claims: List[HypothesisClaim] = Field(default_factory=list)
    support_score: int = 0
    conflict_score: int = 0
    corroboration_score: int = 0
    conflict_penalty: int = 0
    total_score: int = 0
    rank: int = 1
    is_proposed_explanation: bool = False
    explanation: str = ""
    uncertainty_warning: Optional[str] = None


class HypothesisInput(BaseModel):
    title: str
    description: str


# ==========================================
# MODULE 6: REPORT & CITATIONS
# ==========================================

class InvestigationReport(BaseModel):
    report_id: str
    case_id: str
    case_name: str
    generated_at: str = Field(default_factory=get_utc_now_iso)
    case_overview: str
    documents_analyzed: List[Dict[str, Any]]
    investigation_summary: str
    extracted_entities: List[Entity]
    important_events: List[Event]
    chronological_timeline: List[TimelineEntry]
    key_evidence: List[EvidenceItem]
    agreements: List[ContradictionItem]
    contradictions: List[ContradictionItem]
    candidate_hypotheses: List[Hypothesis]
    score_breakdown: List[Dict[str, Any]]
    proposed_explanation: Optional[Hypothesis] = None
    supporting_evidence: List[EvidenceItem] = Field(default_factory=list)
    conflicting_evidence: List[EvidenceItem] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    limitations_and_uncertainty: str
    source_references: List[Dict[str, Any]]


# ==========================================
# REPRODUCIBLE ANALYSIS RECORD (TASK 6)
# ==========================================

class AnalysisRunRecord(BaseModel):
    run_id: str
    case_id: str
    timestamp: str = Field(default_factory=get_utc_now_iso)
    parser_version: str = "1.1.0"
    model_provider: str = "mock"
    model_name: str = "mock-investigator-v1"
    prompt_version: str = "v1.0"
    retrieval_settings: Dict[str, Any] = Field(default_factory=dict)
    nli_model: str = "cross-encoder-nli-heuristics"
    scoring_config: Dict[str, Any] = Field(default_factory=dict)
    controller_loop_counts: Dict[str, int] = Field(default_factory=dict)
    document_hashes: Dict[str, str] = Field(default_factory=dict)
    is_outdated: bool = False
    metrics_summary: Dict[str, Any] = Field(default_factory=dict)


# ==========================================
# CONTROLLER AUDIT & PROGRESS
# ==========================================

class ControllerFeedbackLoopEvent(BaseModel):
    loop_name: str  # Loop 1: Need More Evidence, Loop 2: Need Clarification, Loop 3: Need Additional Analysis
    iteration: int
    trigger_reason: str
    action_taken: str
    result_summary: str
    timestamp: str = Field(default_factory=get_utc_now_iso)


class AnalysisStatus(BaseModel):
    case_id: str
    status: CaseStatus
    current_module: str
    progress_percentage: int
    message: str
    feedback_loops: List[ControllerFeedbackLoopEvent] = Field(default_factory=list)
    updated_at: str = Field(default_factory=get_utc_now_iso)
    error: Optional[str] = None


# ==========================================
# CASE METADATA & RESPONSES
# ==========================================

class Case(BaseModel):
    case_id: str
    name: str
    description: str
    is_demo: bool = False
    created_at: str = Field(default_factory=get_utc_now_iso)
    updated_at: str = Field(default_factory=get_utc_now_iso)
    status: CaseStatus = CaseStatus.CREATED
    document_count: int = 0
    entity_count: int = 0
    event_count: int = 0
    contradiction_count: int = 0
    hypothesis_count: int = 0
    single_document_warning: bool = False


class CaseCreateRequest(BaseModel):
    name: str
    description: str = ""
    is_demo: bool = False


class CaseUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class AskQuestionRequest(BaseModel):
    question: str
    top_k: int = 5


class AskQuestionResponse(BaseModel):
    question: str
    answer: str
    evidence: List[EvidenceItem]
    sources: List[Dict[str, Any]]
    model_used: str
    is_mock: bool = False
    uncertainty_note: Optional[str] = None

