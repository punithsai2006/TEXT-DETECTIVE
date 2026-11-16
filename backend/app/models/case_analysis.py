"""Nested contracts for evidence-based hypotheses and versioned case summaries."""
from typing import Literal
from pydantic import Field, model_validator
from app.models.evidence_review import StrictModel, AnswerAssertion


class NecessaryClaim(StrictModel):
    requirement_id: str
    text: str = Field(min_length=1, max_length=1600)


class HypothesisProposal(StrictModel):
    hypothesis_id: str
    title: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1, max_length=2500)
    necessary_claims: list[NecessaryClaim] = Field(min_length=1, max_length=6)
    relevant_claim_ids: list[str] = Field(max_length=30)
    source_span_ids: list[str] = Field(min_length=1, max_length=16)
    assumptions: list[str] = Field(default_factory=list, max_length=12)
    missing_evidence: list[str] = Field(default_factory=list, max_length=12)


class HypothesisDraft(StrictModel):
    hypotheses: list[HypothesisProposal] = Field(max_length=4)
    unanswered_questions: list[str] = Field(default_factory=list, max_length=15)


class RequirementAssessment(StrictModel):
    requirement_id: str
    supporting_source_span_ids: list[str] = Field(default_factory=list, max_length=16)
    contrary_source_span_ids: list[str] = Field(default_factory=list, max_length=16)
    explanation: str = Field(min_length=1, max_length=2000)
    unresolved_assumptions: list[str] = Field(default_factory=list, max_length=10)


class ConstraintAssessment(StrictModel):
    status: Literal["supported", "conflicting", "unknown"]
    explanation: str = Field(min_length=1, max_length=2000)
    source_span_ids: list[str] = Field(default_factory=list, max_length=16)

    @model_validator(mode="after")
    def evidence_required(self):
        if self.status != "unknown" and not self.source_span_ids:
            raise ValueError("A known constraint requires source references")
        return self


class HypothesisAssessment(StrictModel):
    requirements: list[RequirementAssessment] = Field(max_length=6)
    temporal: ConstraintAssessment
    relationships: ConstraintAssessment
    additional_missing_evidence: list[str] = Field(default_factory=list, max_length=12)


class VerificationCheck(StrictModel):
    assertion_id: str
    supported: bool
    explanation: str = Field(min_length=1, max_length=2000)


class VerificationBatch(StrictModel):
    checks: list[VerificationCheck] = Field(max_length=40)


class ReportSection(StrictModel):
    title: str = Field(min_length=1, max_length=160)
    assertions: list[AnswerAssertion] = Field(default_factory=list, max_length=8)
    unknowns: list[str] = Field(default_factory=list, max_length=12)


class ReportDraft(StrictModel):
    executive_summary: list[AnswerAssertion] = Field(max_length=6)
    sections: list[ReportSection] = Field(default_factory=list, max_length=5)
    unanswered_questions: list[str] = Field(default_factory=list, max_length=20)
    limitations: list[str] = Field(default_factory=list, max_length=20)


class ScoreBreakdown(StrictModel):
    support: float
    conflict: float
    temporal: float
    relationships: float
    coverage: float
    assumptions: float
    weights: dict[str, float]
    weighted_components: dict[str, float]
    necessary_claim_count: int
    supported_claim_count: int
    conflicting_claim_count: int
    distinct_lineage_count: int
    lineage_ids: list[str]


class Limitation(StrictModel):
    code: str
    text: str


class RankedHypothesis(StrictModel):
    hypothesis_id: str
    title: str
    description: str
    description_source_span_ids: list[str] = Field(default_factory=list)
    evidence_support_score: float | None
    score_method_version: str
    score_breakdown: ScoreBreakdown | None
    supporting_source_span_ids: list[str]
    contrary_source_span_ids: list[str]
    assumptions: list[str]
    missing_evidence: list[str]
    relevant_claim_ids: list[str]
    relevant_event_ids: list[str]
    relevant_graph_node_ids: list[str]
    limitations: list[Limitation]
    is_other: bool = False
    necessary_claims: list[NecessaryClaim] = Field(default_factory=list)
    requirement_assessments: list[RequirementAssessment] = Field(default_factory=list)


class SummaryText(StrictModel):
    text: str
    source_span_ids: list[str]


class SummaryDiscrepancy(StrictModel):
    contradiction_id: str
    classification: str
    description: str
    claim_ids: list[str]
    source_span_ids: list[str]
    unresolved_assumptions: list[str]
    review_status: str


class SummaryEvent(StrictModel):
    event_id: str
    time_start: str | None
    time_end: str | None
    timezone: str | None
    time_precision: str
    description: str
    attribution: str
    event_basis: Literal["observed", "logged", "reported", "inferred", "unknown"]
    source_span_ids: list[str]


class CaseSummary(StrictModel):
    case_id: str
    case_name: str
    analysis_run_id: str
    document_count: int
    analysis_status: str
    summary: SummaryText
    leading_hypothesis: RankedHypothesis | None
    alternative_hypotheses: list[RankedHypothesis]
    detected_contradictions: list[SummaryDiscrepancy]
    minor_discrepancies: list[SummaryDiscrepancy]
    timeline: list[SummaryEvent]
    unanswered_questions: list[str]
    limitations: list[Limitation]
