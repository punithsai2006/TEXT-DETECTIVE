import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

from app.models.schemas import (
    ContradictionItem,
    ContradictionType,
    DocumentMetadata,
    Entity,
    Event,
    NLILabel,
)
from app.services.ingestion.preprocessor import split_into_sentences
from app.services.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)

# Key thematic conflict word pairs
CONFLICT_PAIRS = [
    (r"\b(unlocked|open|left open)\b", r"\b(locked|secured|shut)\b"),
    (r"\b(authorized|permitted|allowed)\b", r"\b(unauthorized|forbidden|prohibited|not allowed)\b"),
    (r"\b(alone|by myself|solo)\b", r"\b(accompanied|with|together with)\b"),
    (r"\b(inside|entered|accessed|swiped|authenticated|logged in)\b", r"\b(outside|never entered|did not enter|never inside|not inside|away|offsite)\b"),
    (r"\b(present|there|at the site)\b", r"\b(absent|at home|offsite|elsewhere|never there)\b"),
    (r"\b(downloaded|copied|extracted)\b", r"\b(did not download|never copied|no transfer)\b"),
    (r"\b(working|active|online)\b", r"\b(broken|disabled|offline|malfunctioning)\b"),
]

NEGATION_WORDS = {"not", "never", "no", "didn't", "wasn't", "couldn't", "denied", "denies", "refused", "neither"}


class ContradictionDetector:
    def __init__(self):
        self._nli_pipeline = None
        self._nli_model_name = "roberta-large-mnli"
        self._attempted_pipeline = False

    def _get_nli_pipeline(self):
        if self._attempted_pipeline:
            return self._nli_pipeline
        self._attempted_pipeline = True
        try:
            from transformers import pipeline
            self._nli_pipeline = pipeline("text-classification", model="roberta-large-mnli")
            logger.info("Loaded RoBERTa-MNLI pipeline successfully.")
        except Exception as e:
            logger.info(f"Transformers RoBERTa-MNLI unavailable ({e}). Using deterministic rule/semantic NLI engine.")
            self._nli_pipeline = None
        return self._nli_pipeline

    def evaluate_pair(
        self,
        stmt_a: str,
        stmt_b: str,
        entity_context: str = ""
    ) -> Tuple[NLILabel, ContradictionType, float, str]:
        """
        Evaluates premise-hypothesis statement pair.
        Returns (nli_label, contradiction_type, confidence, explanation).
        """
        a_clean = stmt_a.strip().lower()
        b_clean = stmt_b.strip().lower()

        # Check for exact or near-identical agreement
        if a_clean == b_clean or (len(a_clean) > 20 and a_clean in b_clean) or (len(b_clean) > 20 and b_clean in a_clean):
            return (
                NLILabel.ENTAILMENT,
                ContradictionType.AGREEMENT,
                0.95,
                "Both statements assert the identical factual detail across sources."
            )

        # 1. Check semantic conflict word pairs
        for pattern_pos, pattern_neg in CONFLICT_PAIRS:
            match_a_pos = re.search(pattern_pos, a_clean)
            match_b_neg = re.search(pattern_neg, b_clean)
            match_a_neg = re.search(pattern_neg, a_clean)
            match_b_pos = re.search(pattern_pos, b_clean)

            if (match_a_pos and match_b_neg) or (match_a_neg and match_b_pos):
                word1 = match_a_pos.group(0) if match_a_pos else match_a_neg.group(0)
                word2 = match_b_neg.group(0) if match_b_neg else match_b_pos.group(0)
                return (
                    NLILabel.CONTRADICTION,
                    ContradictionType.CONFIRMED_CONTRADICTION,
                    0.92,
                    f"Direct contradiction detected: Statement A states '{word1}' while Statement B asserts '{word2}'."
                )

        # 2. Check negation disparity on key verbs
        verbs = ["entered", "saw", "accessed", "authorized", "present", "left", "downloaded", "swiped", "met", "spoke"]
        for v in verbs:
            in_a = v in a_clean
            in_b = v in b_clean
            if in_a and in_b:
                neg_a = any(neg in a_clean.split() for neg in NEGATION_WORDS)
                neg_b = any(neg in b_clean.split() for neg in NEGATION_WORDS)
                if neg_a != neg_b:
                    return (
                        NLILabel.CONTRADICTION,
                        ContradictionType.CONFIRMED_CONTRADICTION,
                        0.90,
                        f"Opposing assertions regarding action '{v}': one statement affirms it while the other explicitly negates it."
                    )

        # 3. Check conflicting clock times for the same entity
        time_match_a = re.findall(r"\b(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)\b", stmt_a)
        time_match_b = re.findall(r"\b(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)\b", stmt_b)
        if time_match_a and time_match_b and time_match_a[0].lower() != time_match_b[0].lower():
            # If both mention the same person or key action
            return (
                NLILabel.CONTRADICTION,
                ContradictionType.POSSIBLE_CONTRADICTION,
                0.84,
                f"Temporal discrepancy: Statement A references {time_match_a[0]} while Statement B references {time_match_b[0]}."
            )

        # 4. Check conflicting locations for the same entity at similar time
        loc_indicators = ["server room", "floor 3", "floor 2", "floor 1", "lobby", "outside", "cafeteria", "office", "vault", "home"]
        locs_in_a = [loc for loc in loc_indicators if loc in a_clean]
        locs_in_b = [loc for loc in loc_indicators if loc in b_clean]
        if locs_in_a and locs_in_b and locs_in_a[0] != locs_in_b[0]:
            return (
                NLILabel.CONTRADICTION,
                ContradictionType.CONFIRMED_CONTRADICTION,
                0.88,
                f"Conflicting locations for the same timeframe: Statement A places activity in '{locs_in_a[0]}' while Statement B claims '{locs_in_b[0]}'."
            )

        # 5. Overlapping affirmation
        words_a = set(re.findall(r"\b[A-Za-z0-9]{3,}\b", a_clean)) - {"the", "and", "that", "this", "with", "from"}
        words_b = set(re.findall(r"\b[A-Za-z0-9]{3,}\b", b_clean)) - {"the", "and", "that", "this", "with", "from"}
        overlap_ratio = len(words_a & words_b) / max(len(words_a | words_b), 1)

        if overlap_ratio > 0.65:
            return (
                NLILabel.ENTAILMENT,
                ContradictionType.AGREEMENT,
                0.85,
                "Substantial factual and lexical overlap confirming the same sequence of events."
            )

        return (
            NLILabel.NEUTRAL,
            ContradictionType.NEUTRAL,
            0.50,
            "Statements discuss distinct aspects or lack conflicting factual assertions."
        )

    def find_cross_document_contradictions(
        self,
        case_id: str,
        documents: List[DocumentMetadata],
        entities: List[Entity],
        events: List[Event],
    ) -> List[ContradictionItem]:
        """
        Compares statements across all distinct documents and identifies
        confirmed contradictions, possible contradictions, and key agreements.
        """
        if len(documents) < 2:
            return []

        # Map entities and keywords to sentences across documents
        # Structure: entity_name -> list of (doc, sentence, speaker, timestamp)
        entity_mentions: Dict[str, List[Tuple[DocumentMetadata, str, Optional[str], Optional[str]]]] = {}

        for doc in documents:
            text_val = doc.cleaned_text or doc.raw_text or ""
            sentences = split_into_sentences(text_val)
            if not sentences and text_val.strip():
                sentences = [text_val.strip()]
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                # Find which entities are touched
                for ent in entities:
                    if re.search(rf"\b{re.escape(ent.name)}\b", sent, re.IGNORECASE):
                        if ent.name not in entity_mentions:
                            entity_mentions[ent.name] = []
                        entity_mentions[ent.name].append((doc, sent, doc.speaker, doc.timestamp))

        contradictions: List[ContradictionItem] = []
        compared_pairs = set()

        for ent_name, mentions in entity_mentions.items():
            if len(mentions) < 2:
                continue

            for i in range(len(mentions)):
                doc_a, sent_a, spk_a, time_a = mentions[i]
                for j in range(i + 1, len(mentions)):
                    doc_b, sent_b, spk_b, time_b = mentions[j]

                    # MUST be cross-document
                    if doc_a.document_id == doc_b.document_id:
                        continue

                    pair_key = tuple(sorted([sent_a, sent_b]))
                    if pair_key in compared_pairs:
                        continue
                    compared_pairs.add(pair_key)

                    nli_label, c_type, conf, explanation = self.evaluate_pair(
                        sent_a, sent_b, entity_context=ent_name
                    )

                    # Only record meaningful conflicts or key corroborated agreements
                    if c_type in [
                        ContradictionType.CONFIRMED_CONTRADICTION,
                        ContradictionType.POSSIBLE_CONTRADICTION,
                        ContradictionType.AGREEMENT
                    ]:
                        c_id = f"contra_{uuid.uuid4().hex[:8]}"
                        contradictions.append(
                            ContradictionItem(
                                id=c_id,
                                case_id=case_id,
                                statement_a=sent_a,
                                statement_b=sent_b,
                                doc_a_id=doc_a.document_id,
                                doc_b_id=doc_b.document_id,
                                doc_a_name=doc_a.filename,
                                doc_b_name=doc_b.filename,
                                speaker_a=spk_a,
                                speaker_b=spk_b,
                                timestamp_a=time_a,
                                timestamp_b=time_b,
                                entity_event_link=ent_name,
                                contradiction_type=c_type,
                                nli_label=nli_label,
                                confidence=conf,
                                explanation=explanation,
                                resolution_status="unresolved" if "contradiction" in c_type.value else "resolved",
                                source_sentences=[sent_a, sent_b],
                            )
                        )

        return contradictions


# Global singleton instance
contradiction_detector = ContradictionDetector()
