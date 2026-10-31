import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

from app.models.schemas import (
    ContradictionItem,
    ContradictionType,
    EvidenceItem,
    Hypothesis,
    HypothesisClaim,
)
from app.services.llm_provider import get_llm_provider
from app.services.retrieval.retriever import retriever

logger = logging.getLogger(__name__)


def compute_exact_hypothesis_score(
    support: int,
    conflict: int,
    corroboration: int,
    conflict_penalty: int
) -> int:
    """
    Exact formula from Slide 18:
    Score(H) = Support - Conflict + Corroboration - ConflictPenalty

    Pure, deterministic mathematical calculation.
    """
    return support - conflict + corroboration - conflict_penalty


def decompose_hypothesis_into_claims(
    hypothesis_title: str,
    hypothesis_description: str,
    case_context: Optional[str] = None
) -> List[str]:
    """
    Breaks down a candidate hypothesis into smaller verifiable claims.
    Uses LLM provider if configured or deterministic semantic rules.
    """
    provider = get_llm_provider()
    prompt = (
        f"Hypothesis Title: {hypothesis_title}\n"
        f"Hypothesis Description: {hypothesis_description}\n"
        "Decompose this investigation hypothesis into 2 to 4 atomic, verifiable factual claims. "
        "List each claim starting with a dash (-)."
    )

    try:
        response = provider.generate(prompt=prompt, system_prompt="You are an expert criminal and forensic investigator.")
        try:
            # Check if JSON
            data = json.loads(response.content)
            if "claims" in data and isinstance(data["claims"], list):
                return [c.strip() for c in data["claims"] if c.strip()]
        except json.JSONDecodeError:
            pass

        # Parse bullet lines
        lines = [line.strip() for line in response.content.split("\n") if line.strip()]
        claims = []
        for line in lines:
            if line.startswith("-") or line.startswith("*") or line.startswith("•") or re.match(r"^\d+\.", line):
                clean = re.sub(r"^[-*•\d.]+\s*", "", line).strip()
                if len(clean) > 5:
                    claims.append(clean)
        if claims:
            return claims[:4]
    except Exception as e:
        logger.warning(f"Error in LLM claim decomposition: {e}. Falling back to rule decomposition.")

    # Fallback deterministic decomposition
    sentences = [s.strip() for s in re.split(r"[.;]\s*", hypothesis_description) if len(s.strip()) > 10]
    if len(sentences) >= 2:
        return sentences[:4]

    return [
        f"{hypothesis_title} occurred during the documented timeframe.",
        f"The primary actor accessed the critical systems or location.",
        "Physical or digital records reflect the actions described.",
    ]


class HypothesisScoringEngine:
    """
    Evaluates candidate hypotheses against retrieved evidence and cross-document
    contradictions, implementing the exact Slide 18 algorithm.
    """

    def evaluate_claim_against_evidence(
        self,
        case_id: str,
        claim_text: str,
        case_contradictions: List[ContradictionItem],
    ) -> HypothesisClaim:
        """
        Retrieves evidence for a claim, checks agreement/conflict, and computes corroboration.
        """
        claim_id = f"clm_{uuid.uuid4().hex[:8]}"
        # Retrieve top evidence for this claim
        evidence_items = retriever.search(case_id=case_id, query=claim_text, top_k=6)

        supporting_evidence_ids: List[str] = []
        conflicting_evidence_ids: List[str] = []
        contributing_documents: Set[str] = set()
        contributing_speakers: Set[str] = set()

        q_terms = set(re.findall(r"\b[A-Za-z0-9]{3,}\b", claim_text.lower())) - {
            "the", "and", "that", "this", "with", "from", "were", "been", "have", "during"
        }

        for ev in evidence_items:
            ev_text = ev.text.lower()
            overlap = len([t for t in q_terms if t in ev_text])

            # Check if this evidence contradicts or negates the claim
            has_negation = any(neg in ev_text.split() for neg in ["never", "not", "denies", "no", "false", "unauthorized"])
            claim_has_neg = any(neg in claim_text.lower().split() for neg in ["never", "not", "no", "unauthorized"])

            if overlap >= 2:
                if has_negation != claim_has_neg and ("entered" in ev_text or "access" in ev_text or "locked" in ev_text):
                    conflicting_evidence_ids.append(ev.evidence_id)
                else:
                    supporting_evidence_ids.append(ev.evidence_id)
                    contributing_documents.add(ev.document_name)
                    if ev.speaker:
                        contributing_speakers.add(ev.speaker)

        # Corroboration Rule (Slide 18 / Phase 5):
        # +1 corroboration per claim supported by evidence from at least TWO different
        # documents AND at least TWO different speakers/authors.
        is_corroborated = (len(contributing_documents) >= 2 and len(contributing_speakers) >= 2)

        # Check unresolved contradictions touching this claim
        unresolved_count = 0
        for contra in case_contradictions:
            if contra.resolution_status == "unresolved":
                # Check if contradiction touches keywords of the claim
                contra_text = (contra.statement_a + " " + contra.statement_b).lower()
                c_overlap = len([t for t in q_terms if t in contra_text])
                if c_overlap >= 2:
                    unresolved_count += 1

        return HypothesisClaim(
            claim_id=claim_id,
            text=claim_text,
            supporting_evidence_ids=supporting_evidence_ids,
            conflicting_evidence_ids=conflicting_evidence_ids,
            contributing_documents=list(contributing_documents),
            contributing_speakers=list(contributing_speakers),
            is_corroborated=is_corroborated,
            unresolved_conflicts_count=unresolved_count,
        )

    def score_hypothesis(
        self,
        case_id: str,
        hypothesis_id: str,
        title: str,
        description: str,
        origin: str,
        case_contradictions: List[ContradictionItem],
        pre_defined_claims: Optional[List[str]] = None,
    ) -> Hypothesis:
        """
        Calculates Support, Conflict, Corroboration, ConflictPenalty and Total Score.
        """
        claim_texts = pre_defined_claims or decompose_hypothesis_into_claims(title, description)
        claims: List[HypothesisClaim] = []

        unique_support_ev_ids: Set[str] = set()
        unique_conflict_ev_ids: Set[str] = set()
        corroboration_score = 0
        conflict_penalty = 0

        for claim_text in claim_texts:
            evaluated_claim = self.evaluate_claim_against_evidence(case_id, claim_text, case_contradictions)
            claims.append(evaluated_claim)

            # Prevent double-counting identical evidence chunks across claims
            unique_support_ev_ids.update(evaluated_claim.supporting_evidence_ids)
            unique_conflict_ev_ids.update(evaluated_claim.conflicting_evidence_ids)

            if evaluated_claim.is_corroborated:
                corroboration_score += 1

            conflict_penalty += evaluated_claim.unresolved_conflicts_count

        support_score = len(unique_support_ev_ids)
        conflict_score = len(unique_conflict_ev_ids)

        total_score = compute_exact_hypothesis_score(
            support=support_score,
            conflict=conflict_score,
            corroboration=corroboration_score,
            conflict_penalty=conflict_penalty,
        )

        explanation = (
            f"Score calculation: Support ({support_score}) - Conflict ({conflict_score}) + "
            f"Corroboration ({corroboration_score}) - Conflict Penalty ({conflict_penalty}) = {total_score}. "
            f"Evaluated against {len(claims)} verifiable claims."
        )

        return Hypothesis(
            hypothesis_id=hypothesis_id,
            case_id=case_id,
            title=title,
            description=description,
            origin=origin,
            claims=claims,
            support_score=support_score,
            conflict_score=conflict_score,
            corroboration_score=corroboration_score,
            conflict_penalty=conflict_penalty,
            total_score=total_score,
            rank=1,
            is_proposed_explanation=False,
            explanation=explanation,
            uncertainty_warning=None,
        )

    def rank_hypotheses(self, hypotheses: List[Hypothesis]) -> List[Hypothesis]:
        """
        Sorts hypotheses descending by total_score. Highest score is designated
        'System's Proposed Explanation'. Checks for ties/ambiguity.
        """
        if not hypotheses:
            return []

        hypotheses.sort(key=lambda h: h.total_score, reverse=True)

        for i, h in enumerate(hypotheses):
            h.rank = i + 1
            h.is_proposed_explanation = (i == 0)

        # Ambiguity / uncertainty check
        if len(hypotheses) >= 2 and hypotheses[0].total_score == hypotheses[1].total_score:
            warning_msg = (
                f"Notice: Top two hypotheses ('{hypotheses[0].title}' and '{hypotheses[1].title}') "
                f"share an identical score of {hypotheses[0].total_score}. Evidence is currently "
                "insufficient to establish a single proposed explanation."
            )
            for h in hypotheses[:2]:
                h.uncertainty_warning = warning_msg

        return hypotheses


# Global singleton instance
hypothesis_engine = HypothesisScoringEngine()
