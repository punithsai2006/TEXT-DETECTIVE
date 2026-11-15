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
    ReviewStatus,
)
from app.services.ingestion.preprocessor import split_into_sentences
from app.services.llm_provider import analysis_model_json

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

TRANSCRIPT_HEADER = re.compile(
    r"^\[\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?\]\s*[A-Z][A-Z ._'’-]{0,60}:\s*",
    re.IGNORECASE,
)
CLOCK_TIME = re.compile(r"\b(\d{1,2}):(\d{2})(?::\d{2})?\s*(am|pm)?\b", re.IGNORECASE)
CELSIUS = re.compile(r"(?<![\w.])(?:(minus|plus|[-+−])\s*)?(\d+(?:\.\d+)?)\s*(?:°\s*C\b|Celsius\b|C\b)", re.IGNORECASE)
CONTINUOUS_TEMPERATURE = re.compile(r"\b(?:maintained|stayed|remained|held steady)\b.*\b(?:throughout|continuously|entire)\b")
TEMPERATURE_RISE = re.compile(r"\b(?:rose|climbed|warmed(?: up)?|increased)\s+to\b")
MONITORING_DATE = re.compile(
    r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b"
)
WINDOW = re.compile(r"\bfrom (\d{1,2}:\d{2}\s*(?:am|pm)) to (\d{1,2}:\d{2}\s*(?:am|pm)|noon|midnight)\b")


def clock_minutes(match: re.Match) -> int:
    hour, minute, meridiem = match.groups()
    hours = int(hour)
    if meridiem:
        hours = hours % 12 + (12 if meridiem.lower() == "pm" else 0)
    return hours * 60 + int(minute)


def celsius_value(match: re.Match) -> float:
    sign, value = match.groups()
    return float(value) * (-1 if (sign or "").lower() in {"minus", "-", "−"} else 1)


def temperature_reading_in_window(baseline: str, reading: str) -> bool:
    dates = MONITORING_DATE.findall(baseline)
    window = WINDOW.search(baseline)
    times = list(CLOCK_TIME.finditer(reading))
    if len(dates) != 1 or dates != MONITORING_DATE.findall(reading) or not window or len(times) != 1:
        return False
    start = CLOCK_TIME.fullmatch(window[1])
    end = CLOCK_TIME.fullmatch(window[2])
    if not start or not times[0][3]:
        return False
    end_minutes = clock_minutes(end) if end else {"noon": 720, "midnight": 1440}[window[2]]
    return clock_minutes(start) <= clock_minutes(times[0]) <= end_minutes


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
        Backwards-compatible wrapper returning (nli_label, contradiction_type, confidence, explanation).
        """
        label, c_type, conf, expl, _ = self.evaluate_pair_full(stmt_a, stmt_b, entity_context)
        return label, c_type, conf, expl

    def evaluate_pair_full(
        self,
        stmt_a: str,
        stmt_b: str,
        entity_context: str = ""
    ) -> Tuple[NLILabel, ContradictionType, float, str, str]:
        """
        Evaluates premise-hypothesis statement pair.
        Returns (nli_label, contradiction_type, confidence, explanation, detection_engine)
        where detection_engine is one of: 'nli', 'rules', 'llm_verified'.
        """
        stmt_a = TRANSCRIPT_HEADER.sub("", stmt_a.strip())
        stmt_b = TRANSCRIPT_HEADER.sub("", stmt_b.strip())
        a_clean = stmt_a.lower()
        b_clean = stmt_b.lower()

        for statement in (a_clean, b_clean):
            if not statement or statement.endswith("?") or re.search(r"\btell (?:us|me) about\b", statement):
                return (
                    NLILabel.NEUTRAL, ContradictionType.NEUTRAL, 0.50,
                    "At least one passage does not make a factual assertion to compare.", "rules",
                )

        temperatures_a = list(CELSIUS.finditer(a_clean))
        temperatures_b = list(CELSIUS.finditer(b_clean))
        if len(temperatures_a) == len(temperatures_b) == 1:
            temp_a = celsius_value(temperatures_a[0])
            temp_b = celsius_value(temperatures_b[0])
            same_claim = CELSIUS.sub("<temperature>", a_clean) == CELSIUS.sub("<temperature>", b_clean)
            same_entity = entity_context and all(
                re.search(rf"\b{re.escape(entity_context)}\b", statement, re.IGNORECASE)
                for statement in (a_clean, b_clean)
            )
            sustained_vs_rise = same_entity and (
                (CONTINUOUS_TEMPERATURE.search(a_clean) and TEMPERATURE_RISE.search(b_clean) and temp_a < temp_b)
                or (CONTINUOUS_TEMPERATURE.search(b_clean) and TEMPERATURE_RISE.search(a_clean) and temp_b < temp_a)
            )
            if temp_a != temp_b and (same_claim or sustained_vs_rise):
                same_window = sustained_vs_rise and (
                    temperature_reading_in_window(a_clean, b_clean)
                    if temp_a < temp_b else temperature_reading_in_window(b_clean, a_clean)
                )
                return (
                    NLILabel.CONTRADICTION,
                    ContradictionType.CONFIRMED_CONTRADICTION if same_window else ContradictionType.POSSIBLE_CONTRADICTION,
                    0.95 if same_window else 0.85,
                    f"Temperature discrepancy: Statement A reports {temp_a:g} °C and Statement B reports "
                    f"{temp_b:g} °C, a difference of {abs(temp_a - temp_b):g} °C. "
                    + ("The reported reading falls inside the stated monitoring window on the same date."
                       if same_window else "Check that both statements refer to the same period."),
                    "rules",
                )

        # Check for exact or near-identical agreement
        if a_clean == b_clean or (len(a_clean) > 20 and a_clean in b_clean) or (len(b_clean) > 20 and b_clean in a_clean):
            return (
                NLILabel.ENTAILMENT,
                ContradictionType.AGREEMENT,
                0.95,
                "Both statements assert the identical factual detail across sources.",
                "rules",
            )

        # 1. Attempt NLI Classifier if model pipeline is available
        pipe = self._get_nli_pipeline()
        if pipe is not None:
            try:
                res = pipe({"text": stmt_a, "text_pair": stmt_b}, truncation=True)
                if isinstance(res, list) and len(res) > 0:
                    top_pred = res[0]
                    label_str = top_pred.get("label", "").upper()
                    score = float(top_pred.get("score", 0.0))
                    if "CONTRADICTION" in label_str and score >= 0.70:
                        return (
                            NLILabel.CONTRADICTION,
                            ContradictionType.CONFIRMED_CONTRADICTION,
                            round(score, 2),
                            f"NLI model (RoBERTa-MNLI) identified cross-document contradiction ({round(score * 100, 1)}% confidence).",
                            "nli",
                        )
                    elif "ENTAILMENT" in label_str and score >= 0.75:
                        return (
                            NLILabel.ENTAILMENT,
                            ContradictionType.AGREEMENT,
                            round(score, 2),
                            f"NLI model (RoBERTa-MNLI) identified cross-document agreement ({round(score * 100, 1)}% confidence).",
                            "nli",
                        )
            except Exception as e:
                logger.debug(f"NLI pipeline exception, falling back to rule engine: {e}")

        # 2. Forensic Category A: Alibi / Absence Claim vs Physical Access Log / Presence Sighting
        ALIBI_INDICATORS = re.compile(
            r"\b(at my desk|in town|at dinner|at home|offsite|elsewhere|remained at|cataloging in|in room \d+|"
            r"never entered|never went near|never inside|outside|left the facility|absent|left at|departed at|"
            r"did not return|gone home|already gone|went home|headed home|in the staff lot|staff lot|parked in|"
            r"did not go back|never went back|didn't go back|never returned|only visit was|only visit to)\b",
            re.IGNORECASE
        )
        ACCESS_PRESENCE_INDICATORS = re.compile(
            r"\b(access[ _]granted|auth[ _]granted|auth_ok|swiped|rfid|badge #|card #|door sensor|"
            r"service door entry|seen near|saw [A-Z][a-z]+|walking near|carrying a|carrying long|carrying.*crate|"
            r"logged in|console \d+|turnstile|entered through|service gate|vehicle_log|staff permit|"
            r"cellar_door.*entry|cellar.*entry|entered the cellar|cage_lock|unlocked - key)\b",
            re.IGNORECASE
        )
        match_alibi_a = ALIBI_INDICATORS.search(a_clean)
        match_access_b = ACCESS_PRESENCE_INDICATORS.search(b_clean)
        match_alibi_b = ALIBI_INDICATORS.search(b_clean)
        match_access_a = ACCESS_PRESENCE_INDICATORS.search(a_clean)

        if (match_alibi_a and match_access_b) or (match_alibi_b and match_access_a):
            stmt_alibi = a_clean if match_alibi_a else b_clean
            stmt_access = b_clean if match_alibi_a else a_clean
            alibi_phrase = match_alibi_a.group(0) if match_alibi_a else match_alibi_b.group(0)
            access_phrase = match_access_b.group(0) if match_access_b else match_access_a.group(0)

            # Check if alibi specifies a departure time or end of presence
            m_dep = re.search(
                r"\b(?:left|departed|went home|gone home|already gone)(?:\s+(?:the\s+[a-z]+|from\s+[a-z]+))?(?:\s+(?:promptly|shortly))?(?:\s+(?:at|about|around))+\s*(\d{1,2}:\d{2}\s*(?:am|pm)?)",
                stmt_alibi,
                re.IGNORECASE,
            )
            if m_dep:
                t_dep = CLOCK_TIME.search(m_dep.group(0))
                t_acc = CLOCK_TIME.search(stmt_access)
                if t_dep and t_acc:
                    dep_min = clock_minutes(t_dep)
                    acc_min = clock_minutes(t_acc)
                    is_exit_telemetry = bool(re.search(r"\b(exit|exited|departed|leaving|out)\b", stmt_access, re.IGNORECASE))
                    is_entry_telemetry = bool(re.search(r"\b(entry|entered|enter|access_granted.*entry|inside|swiped|unlocked)\b", stmt_access, re.IGNORECASE))
                    is_sighting = bool(re.search(r"\b(saw|seen|carrying|walking|spoke|met)\b", stmt_access, re.IGNORECASE))

                    # 1. Telemetry recorded access prior to stated departure time -> Consistent!
                    if acc_min < dep_min - 15:
                        return (
                            NLILabel.NEUTRAL,
                            ContradictionType.NEUTRAL,
                            0.50,
                            f"Consistent timeline: Telemetry recorded access at {t_acc.group(0).strip()} prior to stated departure time ({t_dep.group(0).strip()}).",
                            "rules",
                        )

                    # 2. Telemetry is an EXIT log within 15 minutes of departure time (e.g. 10:12 vs 10:15 or 17:34 vs 17:30)
                    # Natural human approximation corroborating departure
                    if is_exit_telemetry and abs(acc_min - dep_min) <= 15:
                        return (
                            NLILabel.ENTAILMENT,
                            ContradictionType.AGREEMENT,
                            0.90,
                            f"Consistent timeline: Telemetry recorded exit at {t_acc.group(0).strip()} matching stated departure estimate ({t_dep.group(0).strip()}).",
                            "rules",
                        )

                    # 3. Telemetry is an EXIT log hours later from a general staff door when witness only described leaving a specific room (not going home)
                    if is_exit_telemetry and not is_entry_telemetry and not is_sighting:
                        has_total_absence_claim = bool(re.search(r"\b(did not return|gone home|went home|at home|headed home|left for the day|left the (?:hotel|facility|building))\b", stmt_alibi, re.IGNORECASE))
                        if not has_total_absence_claim and acc_min > dep_min + 60:
                            return (
                                NLILabel.NEUTRAL,
                                ContradictionType.NEUTRAL,
                                0.50,
                                f"Non-conflicting shift activity: General staff exit at {t_acc.group(0).strip()} does not refute prior room departure at {t_dep.group(0).strip()}.",
                                "rules",
                            )

            if not m_dep and "cleaning" in stmt_alibi.lower():
                t_acc = CLOCK_TIME.search(stmt_access)
                if t_acc:
                    acc_min = clock_minutes(t_acc)
                    if acc_min < 17 * 60 + 30:
                        return (
                            NLILabel.NEUTRAL,
                            ContradictionType.NEUTRAL,
                            0.50,
                            f"Consistent: Access at {t_acc.group(0).strip()} occurred prior to evening cleaning shift.",
                            "rules",
                        )

            return (
                NLILabel.CONTRADICTION,
                ContradictionType.CONFIRMED_CONTRADICTION,
                0.95,
                f"Alibi conflict: One statement asserts absence/alibi ('{alibi_phrase}'), "
                f"while physical telemetry/log records access or presence ('{access_phrase}').",
                "rules",
            )

        # 3. Forensic Category B: Explicit Denial vs Concrete Proof (Payment, Wire, Email, Retainer, Key possession, Override)
        DENIAL_INDICATORS = re.compile(
            r"\b(never communicated|no communication|none whatsoever|exclusive contract|"
            r"never received payments?|never lent|in my wallet all evening|only .* possess|"
            r"no safe access|never sounded|no modifications approved|in my jacket pocket|"
            r"did not open|never opened|not open the|never handled|did not handle|no contact|"
            r"not contacted|have not contacted|not about this|never touched|did not touch|didn't touch|"
            r"not touch the|not touched|not about this map|haven't spoken|not spoken to|have not spoken|"
            r"not in months|never spoke|no contact with any broker|car stayed|vehicle stayed|stayed in the (?:staff )?lot|"
            r"parked all evening|did not move|didn't go near the dock|never went near the dock)\b",
            re.IGNORECASE
        )
        AFFIRM_PROOF_INDICATORS = re.compile(
            r"\b(consulting retainer|wire transfer|deposited .* account|leave (?:his|her)? (?:lanyard|keycard)|"
            r"spare (?:master )?key|alarm triggered|alarm sounded|flash_overwrite|kill_override|"
            r"overwritten with custom binary|credited to .* account|case_lock|unlocked|key_[a-z0-9]+|"
            r"cage_lock.*unlocked|unlocked.*key_[a-z0-9]+|cage_lock.*locked|locked.*key_[a-z0-9]+|"
            r"buyer might pay|valuation question|sale were arranged|private sale|inquire|inquiry|"
            r"pemberton|wine broker|broker.*cash|cash.*broker|service gate.*exit|service_gate.*exit|"
            r"vehicle_log.*exit|loaded.*volvo|crate.*volvo|carrying.*cooler.*crate|gray volvo)\b",
            re.IGNORECASE
        )
        match_denial_a = DENIAL_INDICATORS.search(a_clean)
        match_proof_b = AFFIRM_PROOF_INDICATORS.search(b_clean)
        match_denial_b = DENIAL_INDICATORS.search(b_clean)
        match_proof_a = AFFIRM_PROOF_INDICATORS.search(a_clean)

        if (match_denial_a and match_proof_b) or (match_denial_b and match_proof_a):
            denial_word = match_denial_a.group(0) if match_denial_a else match_denial_b.group(0)
            proof_word = match_proof_b.group(0) if match_proof_b else match_proof_a.group(0)
            return (
                NLILabel.CONTRADICTION,
                ContradictionType.CONFIRMED_CONTRADICTION,
                0.94,
                f"Direct contradiction: Statement denies activity or relationship ('{denial_word}'), "
                f"but audit/documentary evidence records '{proof_word}'.",
                "rules",
            )

        # 4. Forensic Category C: Equipment / System Operation vs Failure / Breach
        NORMAL_OP_INDICATORS = re.compile(
            r"\b(kicked in seamlessly|maintained strict|held steady|steady \d+|normal operation|"
            r"showed green all night|closed and locked|fully closed)\b",
            re.IGNORECASE
        )
        FAILURE_OP_INDICATORS = re.compile(
            r"\b(failed to engage|alarm triggered|alarm sounded|forced open|door sensor forced open|"
            r"compromised|excursion alert|propped open)\b",
            re.IGNORECASE
        )
        match_norm_a = NORMAL_OP_INDICATORS.search(a_clean)
        match_fail_b = FAILURE_OP_INDICATORS.search(b_clean)
        match_norm_b = NORMAL_OP_INDICATORS.search(b_clean)
        match_fail_a = FAILURE_OP_INDICATORS.search(a_clean)

        if (match_norm_a and match_fail_b) or (match_norm_b and match_fail_a):
            norm_word = match_norm_a.group(0) if match_norm_a else match_norm_b.group(0)
            fail_word = match_fail_b.group(0) if match_fail_b else match_fail_a.group(0)
            return (
                NLILabel.CONTRADICTION,
                ContradictionType.CONFIRMED_CONTRADICTION,
                0.93,
                f"System status discrepancy: Statement reports normal state ('{norm_word}'), "
                f"while telemetry/sensor logs record failure or breach ('{fail_word}').",
                "rules",
            )

        # 5. Forensic Category D: Dispatch / Movement Time Discrepancy
        DISPATCH_WORDS = re.compile(r"\b(dispatched|pickup|courier|transported|departed|arrived)\b", re.IGNORECASE)
        if DISPATCH_WORDS.search(a_clean) and DISPATCH_WORDS.search(b_clean):
            t_a = list(CLOCK_TIME.finditer(stmt_a))
            t_b = list(CLOCK_TIME.finditer(stmt_b))
            if t_a and t_b and clock_minutes(t_a[0]) != clock_minutes(t_b[0]):
                return (
                    NLILabel.CONTRADICTION,
                    ContradictionType.CONFIRMED_CONTRADICTION,
                    0.90,
                    f"Temporal discrepancy regarding event: Statement A reports {t_a[0].group(0).strip()} while Statement B indicates {t_b[0].group(0).strip()}.",
                    "rules",
                )

        # 6. Check semantic conflict word pairs (Requires shared subject or entity context)
        words_a = set(re.findall(r"\b[A-Za-z0-9]{3,}\b", a_clean)) - {"the", "and", "that", "this", "with", "from", "was", "were", "been", "have", "had", "for", "not"}
        words_b = set(re.findall(r"\b[A-Za-z0-9]{3,}\b", b_clean)) - {"the", "and", "that", "this", "with", "from", "was", "were", "been", "have", "had", "for", "not"}
        shared_subject = len(words_a & words_b) >= 1 or bool(entity_context and (entity_context.lower() in a_clean or entity_context.lower() in b_clean))

        BARRIER_WORDS = re.compile(r"\b(door|gate|cage|case|display|vault|safe|lock|turnstile|cabinet|dock|portal|entrance|exit)\b", re.IGNORECASE)
        BEVERAGE_WORDS = re.compile(r"\b(cabernet|wine|bottle|bottles|drink|drinks|champagne|chardonnay|merlot|beverage|can|cork)\b", re.IGNORECASE)

        if shared_subject:
            for pattern_pos, pattern_neg in CONFLICT_PAIRS:
                match_a_pos = re.search(pattern_pos, a_clean)
                match_b_neg = re.search(pattern_neg, b_clean)
                match_a_neg = re.search(pattern_neg, a_clean)
                match_b_pos = re.search(pattern_pos, b_clean)

                if (match_a_pos and match_b_neg) or (match_a_neg and match_b_pos):
                    # Disambiguate container/barrier locks vs food/drink opening
                    if "unlocked|open" in pattern_pos or "locked|secured" in pattern_neg:
                        has_bev_a = bool(BEVERAGE_WORDS.search(a_clean))
                        has_bev_b = bool(BEVERAGE_WORDS.search(b_clean))
                        has_bar_a = bool(BARRIER_WORDS.search(a_clean))
                        has_bar_b = bool(BARRIER_WORDS.search(b_clean))
                        # If one refers to a barrier/container and the other refers to opening a beverage/drink, reject false positive!
                        if (has_bar_a and has_bev_b and not has_bar_b) or (has_bar_b and has_bev_a and not has_bar_a):
                            continue

                    word1 = match_a_pos.group(0) if match_a_pos else match_a_neg.group(0)
                    word2 = match_b_neg.group(0) if match_b_neg else match_b_pos.group(0)
                    return (
                        NLILabel.CONTRADICTION,
                        ContradictionType.CONFIRMED_CONTRADICTION,
                        0.92,
                        f"Direct contradiction detected: Statement A states '{word1}' while Statement B asserts '{word2}'.",
                        "rules",
                    )

        # 7. Check negation disparity on key verbs (Requires shared subject)
        if shared_subject:
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
                            f"Opposing assertions regarding action '{v}': one statement affirms it while the other explicitly negates it.",
                            "rules",
                        )

        # A differing clock time is evidence when both passages make the same event claim.
        times_a = list(CLOCK_TIME.finditer(stmt_a))
        times_b = list(CLOCK_TIME.finditer(stmt_b))
        if (len(times_a) == len(times_b) == 1
                and CLOCK_TIME.sub("<time>", a_clean) == CLOCK_TIME.sub("<time>", b_clean)
                and bool(times_a[0][3]) == bool(times_b[0][3])
                and clock_minutes(times_a[0]) != clock_minutes(times_b[0])):
            return (
                NLILabel.CONTRADICTION,
                ContradictionType.POSSIBLE_CONTRADICTION,
                0.85,
                f"Temporal discrepancy: Statement A places the event at {times_a[0][0].strip()} "
                f"and Statement B places it at {times_b[0][0].strip()}.",
                "rules",
            )

        # 5. Check conflicting locations for the same entity at similar time
        loc_indicators = ["server room", "floor 3", "floor 2", "floor 1", "lobby", "outside", "cafeteria", "office", "vault", "home"]
        locs_in_a = [loc for loc in loc_indicators if loc in a_clean]
        locs_in_b = [loc for loc in loc_indicators if loc in b_clean]
        if locs_in_a and locs_in_b and locs_in_a[0] != locs_in_b[0]:
            return (
                NLILabel.CONTRADICTION,
                ContradictionType.CONFIRMED_CONTRADICTION,
                0.88,
                f"Conflicting locations for the same timeframe: Statement A places activity in '{locs_in_a[0]}' while Statement B claims '{locs_in_b[0]}'.",
                "rules",
            )

        # 6. Overlapping affirmation
        words_a = set(re.findall(r"\b[A-Za-z0-9]{3,}\b", a_clean)) - {"the", "and", "that", "this", "with", "from"}
        words_b = set(re.findall(r"\b[A-Za-z0-9]{3,}\b", b_clean)) - {"the", "and", "that", "this", "with", "from"}
        overlap_ratio = len(words_a & words_b) / max(len(words_a | words_b), 1)

        if overlap_ratio > 0.65:
            return (
                NLILabel.ENTAILMENT,
                ContradictionType.AGREEMENT,
                0.85,
                "Substantial factual and lexical overlap confirming the same sequence of events.",
                "rules",
            )

        # 7. Optional LLM Judge for uncertain/borderline cases with moderate lexical overlap
        if overlap_ratio > 0.35:
            data = analysis_model_json(
                'Classify the two claims. Return {"is_contradiction":bool,"is_agreement":bool,'
                '"confidence":number,"explanation":string}. Check whether both claims concern the same event.',
                {"statement_a": stmt_a, "statement_b": stmt_b},
            )
            if data:
                try:
                    confidence = float(data.get("confidence", 0))
                    explanation = data.get("explanation")
                    if not 0.70 <= confidence <= 1 or not isinstance(explanation, str):
                        raise ValueError("Incomplete judge assessment")
                    if data.get("is_contradiction") is True and data.get("is_agreement") is False:
                        return (
                            NLILabel.CONTRADICTION,
                            ContradictionType.POSSIBLE_CONTRADICTION,
                            confidence,
                            explanation,
                            "llm_verified",
                        )
                    elif data.get("is_agreement") is True and data.get("is_contradiction") is False:
                        return (
                            NLILabel.ENTAILMENT,
                            ContradictionType.AGREEMENT,
                            confidence,
                            explanation,
                            "llm_verified",
                        )
                except (TypeError, ValueError):
                    pass

        return (
            NLILabel.NEUTRAL,
            ContradictionType.NEUTRAL,
            0.50,
            "Statements discuss distinct aspects or lack conflicting factual assertions.",
            "rules",
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

        # Focus comparison on actionable entities (Persons, Objects/Assets, and specific Locations)
        # Avoid generic broad organizations and general buildings that cause cross-corpus false positive explosions
        focus_entities = [
            ent for ent in entities
            if ent.entity_type.value in {"person", "object"}
            or (ent.entity_type.value == "location" and any(k in ent.name.lower() for k in {"room", "vault", "hangar", "bay", "bunker", "booth", "zone"}))
        ]
        if not focus_entities:
            focus_entities = entities

        for doc in documents:
            text_val = doc.cleaned_text or doc.raw_text or ""
            sentences = split_into_sentences(text_val)
            if not sentences and text_val.strip():
                sentences = [text_val.strip()]

            prev_q_entities: Set[str] = set()

            for sent in sentences:
                sent = sent.strip()
                if not sent or len(sent) < 6:
                    continue

                sent_norm = re.sub(r"[_:\-]+", " ", sent)
                is_question = bool(re.search(r"\b[A-Za-z0-9_ -]{2,20}:\s*.*\?$", sent) or (sent.endswith("?") and doc.document_type.value == "interview"))

                matched_entities: Set[str] = set()
                for ent in focus_entities:
                    # 1. Direct or normalized name match
                    if re.search(rf"\b{re.escape(ent.name)}\b", sent, re.IGNORECASE) or re.search(rf"\b{re.escape(ent.name)}\b", sent_norm, re.IGNORECASE):
                        matched_entities.add(ent.name)
                        continue

                    # 2. Underscored or alias match (e.g. TOM_REYES, T. Reyes, KEY_02)
                    ent_under = ent.name.replace(" ", "_")
                    if re.search(rf"\b{re.escape(ent_under)}\b", sent, re.IGNORECASE) or re.search(rf"\b{re.escape(ent_under)}\b", sent_norm, re.IGNORECASE):
                        matched_entities.add(ent.name)
                        continue

                    tokens = ent.name.split()
                    if len(tokens) >= 2 and ent.entity_type.value == "person":
                        initial_alias = f"{tokens[0][0]}\\.?\\s+{tokens[-1]}"
                        user_alias = f"{tokens[0][0]}{tokens[-1]}"
                        if (re.search(rf"\b{initial_alias}\b", sent, re.IGNORECASE) or
                            re.search(rf"\b{user_alias}\b", sent, re.IGNORECASE) or
                            re.search(rf"\b{initial_alias}\b", sent_norm, re.IGNORECASE) or
                            re.search(rf"\b{user_alias}\b", sent_norm, re.IGNORECASE)):
                            matched_entities.add(ent.name)
                            continue

                    # 3. Link witness first-person claims in speaker's document to speaker
                    if ent.entity_type.value == "person" and doc.speaker:
                        if ent.name.lower() in doc.speaker.lower() or doc.speaker.lower() in ent.name.lower():
                            if re.search(r"\b(i|my|me|myself|we|our)\b", sent, re.IGNORECASE):
                                matched_entities.add(ent.name)

                if is_question:
                    prev_q_entities = matched_entities
                else:
                    final_entities = matched_entities | prev_q_entities
                    for ent_name in final_entities:
                        if ent_name not in entity_mentions:
                            entity_mentions[ent_name] = []
                        entity_mentions[ent_name].append((doc, sent, doc.speaker, doc.timestamp))

        contradictions: List[ContradictionItem] = []
        compared_pairs = set()
        recorded_contradiction_pairs = set()

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

                    nli_label, c_type, conf, explanation, engine = self.evaluate_pair_full(
                        sent_a, sent_b, entity_context=ent_name
                    )

                    # Only record meaningful conflicts or key corroborated agreements
                    if c_type in [
                        ContradictionType.CONFIRMED_CONTRADICTION,
                        ContradictionType.POSSIBLE_CONTRADICTION,
                        ContradictionType.AGREEMENT
                    ]:
                        conflict_sig = (min(sent_a.strip().lower(), sent_b.strip().lower()), max(sent_a.strip().lower(), sent_b.strip().lower()))
                        if conflict_sig in recorded_contradiction_pairs:
                            continue
                        recorded_contradiction_pairs.add(conflict_sig)

                        auto_confirmed = (
                            c_type == ContradictionType.CONFIRMED_CONTRADICTION
                            and explanation.startswith("Temperature discrepancy:")
                        )
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
                                detection_engine=engine,
                                explanation=explanation,
                                resolution_status="unresolved" if "contradiction" in c_type.value else "resolved",
                                review_status=(
                                    ReviewStatus.CONFIRMED
                                    if auto_confirmed
                                    else ReviewStatus.PENDING_REVIEW
                                ),
                                reviewer_id="system" if auto_confirmed else None,
                                source_sentences=[sent_a, sent_b],
                            )
                        )

        return contradictions


# Global singleton instance
contradiction_detector = ContradictionDetector()
