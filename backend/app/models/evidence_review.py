"""Versioned evidence-review contracts. No field represents probability of truth."""
from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceSpan(StrictModel):
    span_id: str
    case_id: str
    document_id: str
    extraction_version: str
    quote: str
    page_number: int | None = None
    paragraph: int
    char_start: int
    char_end: int
    status: str = "extracted"
    uncertainty: list[str] = Field(default_factory=list)


class Claim(StrictModel):
    claim_id: str = ""
    subject: str = Field(min_length=1, max_length=200)
    predicate: str = Field(min_length=1, max_length=200)
    object: str = Field(max_length=500)
    speaker: str | None = None
    polarity: Literal["positive", "negative", "unknown"] = "unknown"
    event_scope: str | None = None
    event_start: str | None = None
    event_end: str | None = None
    timezone: str | None = None
    precision: Literal["second", "minute", "hour", "day", "approximate", "unknown"] = "unknown"
    approximate: bool = False
    clock_uncertainty: str | None = None
    record_time: str | None = None
    location: str | None = None
    attribution: Literal["source_assertion", "hearsay", "hypothesis", "question"] = "source_assertion"
    entity_identity: Literal["explicit", "ambiguous"] = "ambiguous"
    quantity: float | None = None
    unit: str | None = None
    source_span_ids: list[str] = Field(min_length=1, max_length=8)
    uncertainty: list[str] = Field(default_factory=list)
    event_basis: Literal["observed", "logged", "reported", "inferred", "unknown"] = "reported"
    review_status: Literal["pending_review", "corrected"] = "pending_review"
    originating_document_id: str | None = None
    originating_source: str | None = None
    quotations: list[str] = Field(default_factory=list)


class EntityMention(StrictModel):
    name: str = Field(min_length=1, max_length=200)
    entity_type: Literal["person", "organization", "place", "object", "unknown"]
    source_span_ids: list[str] = Field(min_length=1, max_length=8)


class Extraction(StrictModel):
    claims: list[Claim] = Field(max_length=100)
    entities: list[EntityMention] = Field(default_factory=list, max_length=100)


class Outcome(str, Enum):
    POTENTIAL_CONTRADICTION = "POTENTIAL_CONTRADICTION"
    COMPATIBLE = "COMPATIBLE"
    EXPLAINABLE_VARIANCE = "EXPLAINABLE_VARIANCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class Comparison(StrictModel):
    outcome: Outcome
    conflict_type: str
    explanation: str = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)


class ToolDecision(StrictModel):
    action: Literal["retrieve_context", "compare"]
    query: str = Field(default="", max_length=500)
    reason: str = Field(min_length=1, max_length=1000)


class AnswerAssertion(StrictModel):
    text: str = Field(min_length=1, max_length=2000)
    kind: Literal["source_claim", "interpretation"]
    source_span_ids: list[str] = Field(min_length=1, max_length=8)


class AnswerDraft(StrictModel):
    assertions: list[AnswerAssertion] = Field(max_length=12)
    unknowns: list[str] = Field(default_factory=list)


class SupportDecision(StrictModel):
    supported: bool
    explanation: str = Field(min_length=1)


class ReviewRequest(StrictModel):
    action: Literal["accept_lead", "explainable_variance", "reject", "request_context", "correct_claim"]
    reviewer: str = Field(default="local_reviewer", min_length=1, max_length=100)
    notes: str = Field(default="", max_length=4000)
    correction: Claim | None = None

    @model_validator(mode="after")
    def correction_required(self):
        if (self.action == "correct_claim") != (self.correction is not None):
            raise ValueError("Only correct_claim requires a complete corrected claim")
        return self


class QuestionRequest(StrictModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)
