"""Evidence-linked observable collaboration; no private reasoning or verdicts."""
from typing import Literal
from pydantic import Field
from app.models.evidence_review import StrictModel, AnswerAssertion


class AgentFinding(StrictModel):
    finding_id: str
    agent_name: str
    finding_type: str
    summary: str
    supporting_span_ids: list[str] = Field(default_factory=list)
    opposing_span_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    verification_status: str = "locator_checked_human_review_required"
    related_graph_node_ids: list[str] = Field(default_factory=list)
    graph_paths: list[dict] = Field(default_factory=list)


class DebateDraft(StrictModel):
    arguments: list[AnswerAssertion] = Field(default_factory=list, max_length=6)
    unresolved_questions: list[str] = Field(default_factory=list, max_length=10)


class AgentState(StrictModel):
    name: str
    responsibility: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    tool_calls: int = 0
    evidence_items: int = 0
    findings_produced: int = 0
    warnings: list[str] = Field(default_factory=list)


class TimelineMilestone(StrictModel):
    milestone_id: str
    timestamp_range: str
    summary: str
    event_basis: str
    event_ids: list[str]
    source_span_ids: list[str]
    phase: Literal["Preparation", "Access or entry", "Critical incident", "Exit or aftermath", "Subsequent accounts and investigation"] | None = None
    uncertainty: bool = True
