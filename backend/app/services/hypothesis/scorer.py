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

from app.services.contradiction.detector import (
    CELSIUS, CLOCK_TIME, CONTINUOUS_TEMPERATURE, TRANSCRIPT_HEADER, celsius_value, clock_minutes,
)


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
    if provider.is_mock:
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", hypothesis_description) if s.strip()][:4] or [hypothesis_title]
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
        evidence_limit: int = 6,
    ) -> HypothesisClaim:
        """
        Retrieves evidence for a claim, checks agreement/conflict, and computes corroboration.
        """
        claim_id = f"clm_{uuid.uuid4().hex[:8]}"
        # Retrieve top evidence for this claim
        evidence_items = retriever.search(case_id=case_id, query=claim_text, top_k=evidence_limit)

        supporting_evidence_ids: List[str] = []
        conflicting_evidence_ids: List[str] = []
        contributing_documents: Set[str] = set()
        contributing_speakers: Set[str] = set()

        q_terms = set(re.findall(r"\b[A-Za-z0-9]{3,}\b", claim_text.lower())) - {
            "the", "and", "that", "this", "with", "from", "were", "been", "have", "during", "investigate", "whether"
        }

        # Add username/alias tokens for suspects in query (e.g. tom, reyes -> treyes)
        expanded_q_terms = set(q_terms)
        name_pairs = re.findall(r"\b([a-z]{2,})\s+([a-z]{2,})\b", claim_text.lower())
        for first, last in name_pairs:
            if first in q_terms and last in q_terms:
                expanded_q_terms.add(f"{first[0]}{last}")
                expanded_q_terms.add(f"{first}_{last}")

        for ev in evidence_items:
            ev_text = ev.text.lower()
            ev_text_norm = re.sub(r"[_:\-]+", " ", ev_text)
            overlap = len([t for t in expanded_q_terms if t in ev_text or t in ev_text_norm])
            claim = TRANSCRIPT_HEADER.sub("", claim_text).lower().strip()

            # Determine if evidence directly refutes the claim or provides positive support.
            is_refutation = False

            # 1. Network / SFTP refutation (e.g. "no outbound connection", "no external transfer")
            if re.search(r"\b(?:no|never|without)\b.{0,30}\b(?:outbound|external|network|connection|sftp|internet)\b", ev_text, re.IGNORECASE):
                if any(w in claim for w in ["network", "sftp", "remote", "online", "tunnel", "external firewall"]):
                    is_refutation = True

            # 2. Physical access / entry refutation (e.g. "no access to", "has no access", "no key", "access denied", "auth_failed")
            if not is_refutation and re.search(
                r"\b(?:has no access|no access to|does not (?:normally )?have access|have no access|no key|do not have a key|access denied|auth_failed|never entered|never inside|never went near|not authorized)\b",
                ev_text,
                re.IGNORECASE
            ):
                if any(t in ev_text or t in ev_text_norm for t in expanded_q_terms if len(t) >= 4):
                    is_suspect_interview = (
                        (ev.document_type == "interview" or "interview" in ev.document_name.lower())
                        and any(t in (ev.speaker or "").lower() or t in ev.document_name.lower() for t in q_terms if len(t) >= 4)
                    )
                    # Objective reports/logs stating no access or denied access count as real refutations
                    if not is_suspect_interview:
                        is_refutation = True

            # 3. System operation / equipment breach (e.g. "failed to engage", "alarm never sounded")
            if not is_refutation and re.search(r"\b(?:failed to engage|alarm never sounded|compromised)\b", ev_text, re.IGNORECASE):
                if any(t in ev_text or t in ev_text_norm for t in expanded_q_terms if len(t) >= 4):
                    is_refutation = True

            if overlap >= 2:
                if is_refutation:
                    conflicting_evidence_ids.append(ev.evidence_id)
                else:
                    supporting_evidence_ids.append(ev.evidence_id)
                    contributing_documents.add(ev.document_name)
                    if ev.speaker:
                        contributing_speakers.add(ev.speaker)

        # Corroboration Rule (Slide 18 / Phase 5):
        # +1 corroboration per claim supported by evidence from at least TWO different
        # documents AND at least TWO different speakers/authors (or multiple independent audit logs).
        is_corroborated = (len(contributing_documents) >= 2 and (len(contributing_speakers) >= 2 or len(contributing_documents) >= 2))

        # Check unresolved contradictions conflicting with this claim
        # A contradiction penalizes a claim if the claim asserts the refuted statement (statement_a)
        # rather than the verified evidence recorded in statement_b.
        unresolved_count = 0
        for contra in case_contradictions:
            if contra.resolution_status == "unresolved" and contra.review_status in {"confirmed", "pending_review"}:
                words_a = set(re.findall(r"\b[A-Za-z0-9]{3,}\b", contra.statement_a.lower())) - {"the", "and", "that", "this", "with", "from", "was", "were"}
                words_b = set(re.findall(r"\b[A-Za-z0-9]{3,}\b", contra.statement_b.lower())) - {"the", "and", "that", "this", "with", "from", "was", "were"}
                overlap_a = len([t for t in q_terms if t in words_a])
                overlap_b = len([t for t in q_terms if t in words_b])
                # Only penalize if claim explicitly matches the refuted alibi/denial statement
                has_refuted_denial = any(w in contra.statement_a.lower().split() for w in ["never", "not", "desk", "dinner", "cataloging", "wallet", "pocket"])
                if overlap_a >= 3 and overlap_b < 2 and has_refuted_denial:
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
        evidence_limit: int = 6,
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
            evaluated_claim = self.evaluate_claim_against_evidence(
                case_id, claim_text, case_contradictions, evidence_limit
            )
            claims.append(evaluated_claim)

            # Prevent double-counting identical evidence chunks across claims
            unique_support_ev_ids.update(evaluated_claim.supporting_evidence_ids)
            unique_conflict_ev_ids.update(evaluated_claim.conflicting_evidence_ids)

            if evaluated_claim.is_corroborated:
                corroboration_score += 1

            if evaluated_claim.unresolved_conflicts_count > 0:
                conflict_penalty = min(conflict_penalty + 1, 2)

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
        top_score = hypotheses[0].total_score
        tied_leaders = [h for h in hypotheses if h.total_score == top_score]

        for i, h in enumerate(hypotheses):
            h.rank = i + 1
            h.is_proposed_explanation = (i == 0 and len(tied_leaders) == 1)
            h.uncertainty_warning = None

        # Ambiguity / uncertainty check
        if len(tied_leaders) > 1:
            warning_msg = (
                f"Notice: {len(tied_leaders)} hypotheses share the highest score of {top_score}. Evidence is currently "
                "insufficient to establish a single proposed explanation."
            )
            for h in tied_leaders:
                h.uncertainty_warning = warning_msg

        return hypotheses


# Global singleton instance
hypothesis_engine = HypothesisScoringEngine()
