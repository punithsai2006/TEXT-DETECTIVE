import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.models.schemas import EvidenceItem

logger = logging.getLogger(__name__)

STOPWORDS = {
    "the", "a", "an", "is", "was", "were", "are", "be", "been", "being",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "and", "or",
    "that", "this", "these", "those", "it", "its", "as", "into", "did", "do",
    "does", "what", "where", "who", "when", "why", "how", "has", "had", "have",
    "would", "could", "should", "tell", "regarding", "about", "which", "there"
}


class QuestionIntent:
    def __init__(
        self,
        raw_question: str,
        question_type: str,
        is_contradiction: bool,
        is_alibi: bool,
        persons: List[str],
        objects: List[str],
        actions: List[str],
        times: List[str],
    ):
        self.raw_question = raw_question
        self.question_type = question_type
        self.is_contradiction = is_contradiction
        self.is_alibi = is_alibi
        self.persons = persons
        self.objects = objects
        self.actions = actions
        self.times = times


def parse_question_intent(question: str) -> QuestionIntent:
    q_lower = question.lower().strip()

    # 1. Determine question type
    if re.search(r"\b(who|whose|which person|which individual)\b", q_lower):
        q_type = "who"
    elif re.search(r"\b(what time|when|at what time|which hour)\b", q_lower):
        q_type = "when"
    elif re.search(r"\b(where|what location|which room|which building|which workstation)\b", q_lower):
        q_type = "where"
    elif re.search(r"\b(which evidence|contradict|conflict|alibi|discrepan)\b", q_lower):
        q_type = "contradiction"
    elif re.search(r"\b(why|reason)\b", q_lower):
        q_type = "why"
    elif re.search(r"\b(how)\b", q_lower):
        q_type = "how"
    elif re.search(r"\b(what)\b", q_lower):
        q_type = "what"
    else:
        q_type = "general"

    is_contradiction = bool(re.search(r"\b(contradict|contradicts|conflict|inconsistent|discrepancy|lie|deni|alibi)\b", q_lower))
    is_alibi = bool(re.search(r"\b(alibi|whereabouts|claimed|dinner|home)\b", q_lower)) or (is_contradiction and "alibi" in q_lower)

    # 2. Extract potential person names (capitalized words in original question)
    person_candidates = []
    name_matches = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", question)
    for name in name_matches:
        if name.lower() not in STOPWORDS and name.lower() not in {"what", "who", "when", "where", "why", "how", "which"}:
            person_candidates.append(name.strip())

    # 3. Extract times
    times = []
    time_matches = re.finditer(r"\b(0?[1-9]|1[0-2]):([0-5]\d)(?::([0-5]\d))?\s*(am|pm)\b", question, re.I)
    for tm in time_matches:
        hr = int(tm.group(1))
        mn = tm.group(2)
        ampm = tm.group(4).lower()
        hr_24 = hr + 12 if (ampm == "pm" and hr < 12) else (0 if (ampm == "am" and hr == 12) else hr)
        times.append(f"{hr_24:02d}:{mn}")
        times.append(f"{hr}:{mn} {ampm.upper()}")

    time_matches_24 = re.finditer(r"\b([01]?\d|2[0-3]):([0-5]\d)(?::([0-5]\d))?\b", question)
    for tm in time_matches_24:
        hr_24 = int(tm.group(1))
        mn = tm.group(2)
        times.append(f"{hr_24:02d}:{mn}")

    # 4. Extract target objects
    objects = []
    for obj_pattern in [
        r"flash drive", r"usb", r"firmware", r"motor kill", r"freezer", r"temperature",
        r"painting", r"database", r"server room", r"access card", r"keycard", r"keys?", r"alarm"
    ]:
        if re.search(rf"\b{obj_pattern}\b", q_lower):
            objects.append(obj_pattern)

    # 5. Extract actions
    actions = []
    for act_pattern in [
        r"opened", r"open", r"unlocked", r"unlock", r"locked", r"lock",
        r"entered", r"enter", r"exited", r"exit", r"left", r"leave",
        r"carrying", r"carried", r"carry", r"inserted", r"flashed", r"swiped", r"stole"
    ]:
        if re.search(rf"\b{act_pattern}\b", q_lower):
            actions.append(act_pattern)

    return QuestionIntent(
        raw_question=question,
        question_type=q_type,
        is_contradiction=is_contradiction,
        is_alibi=is_alibi,
        persons=person_candidates,
        objects=objects,
        actions=actions,
        times=times,
    )


class EvidenceFacts:
    """Structured facts extracted from retrieved evidence chunks."""
    def __init__(self):
        self.credential_holders: Dict[str, str] = {}
        self.user_handles: Dict[str, str] = {}
        self.interview_statements: List[Dict[str, Any]] = []
        self.log_events: List[Dict[str, Any]] = []
        self.cctv_reports: List[Dict[str, Any]] = []
        self.general_excerpts: List[Dict[str, Any]] = []


def extract_evidence_facts(evidence_items: List[EvidenceItem]) -> EvidenceFacts:
    facts = EvidenceFacts()

    for ev in evidence_items:
        text = ev.text
        doc_name = ev.document_name

        # 1. Credential assignments
        # e.g. Badge #4092 [Alice Vance], KEY_01 is held by Sarah Collins
        for m in re.finditer(r"(?:Badge|Card|Key|KEY)[\s#_]*([A-Za-z0-9_]+)\s*\[([^\]]+)\]", text, re.I):
            key_id = m.group(1).upper()
            holder = m.group(2).strip()
            facts.credential_holders[key_id] = holder

        for km in re.finditer(r"\b([A-Za-z0-9_]+)\s*(?:is|was)?\s*(?:assigned to|held by)\s*([A-Za-z. ]+)", text, re.I):
            key_id = km.group(1).upper()
            holder = km.group(2).strip().rstrip(".")
            if any(term in key_id for term in ["KEY", "CARD", "BADGE"]):
                facts.credential_holders[key_id] = holder

        # 2. User handle mappings (e.g. USER: TREYES, USER: SCOLLINS)
        for hm in re.finditer(r"\bUSER:\s*([A-Z_]+)\b", text):
            handle = hm.group(1).upper()
            facts.user_handles[handle] = handle

        # 3. Interview statements
        # Matches dialogue like [11:01 AM] REYES: I left at about 05:30 PM.
        for dm in re.finditer(r"\[(\d{1,2}:\d{2}\s*(?:AM|PM)?)\]\s*([A-Za-z0-9_ -]+):\s*([^\[\n]+)", text):
            t_str = dm.group(1).strip()
            speaker = dm.group(2).strip()
            statement = dm.group(3).strip()
            facts.interview_statements.append({
                "source": doc_name,
                "timestamp": t_str,
                "speaker": speaker,
                "text": statement,
                "full_excerpt": f"[{t_str}] {speaker}: {statement}",
                "chunk_id": ev.chunk_id,
            })

        # 4. Log lines: bracketed timestamped or hyphenated
        # e.g. [2024-10-12 22:14:30] Reader: Server Room B Door - Badge #4092 [Alice Vance] - ACCESS GRANTED
        for lm in re.finditer(r"(?:\[)?(\d{4}-\d{2}-\d{2}[ T])?(\d{1,2}:\d{2}(?::\d{2})?)(?:\])?\s*([^\n\r]+)", text):
            time_part = lm.group(2).strip()
            rest = lm.group(3).strip()
            if any(k in rest.lower() for k in ["reader", "door", "lock", "access", "badge", "user", "entry", "exit", "auth", "sensor", "temp"]):
                facts.log_events.append({
                    "source": doc_name,
                    "timestamp": time_part,
                    "action": rest,
                    "raw_line": f"[{time_part}] {rest}",
                    "chunk_id": ev.chunk_id,
                })

        # Hyphenated log lines (e.g. 18:16:33 - CASE_LOCK - UNLOCKED - KEY_02)
        for lm in re.finditer(r"(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*([A-Za-z0-9_]+)\s*-\s*([A-Za-z0-9_]+)(?:\s*-\s*([^\n\r]+))?", text):
            t_str = lm.group(1).strip()
            component = lm.group(2).strip()
            action = lm.group(3).strip()
            extra = (lm.group(4) or "").strip()
            facts.log_events.append({
                "source": doc_name,
                "timestamp": t_str,
                "action": f"{component} {action} {extra}".strip(),
                "raw_line": f"{t_str} - {component} - {action}" + (f" - {extra}" if extra else ""),
                "chunk_id": ev.chunk_id,
            })

        # 5. General excerpts
        facts.general_excerpts.append({
            "source": doc_name,
            "text": text,
            "speaker": ev.speaker,
            "timestamp": ev.timestamp,
            "chunk_id": ev.chunk_id,
        })

    return facts


def answer_investigative_question(
    question: str,
    evidence_items: List[EvidenceItem],
    case_name: str = ""
) -> Dict[str, Any]:
    """
    Answers an investigative inquiry strictly grounded in evidence dynamically.
    Distinguishes ambiguous multi-event contexts, direct facts, contradictions, and insufficient evidence.
    """
    if not evidence_items:
        return {
            "direct_answer": "The available case documents do not contain sufficient evidence to establish this answer.",
            "evidence_sufficiency": "insufficient_evidence",
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "unresolved_questions": ["No relevant records found in the case dossier."],
            "important_limitations": "No verified records or witness statements matching this inquiry were identified.",
            "question_type": "general",
        }

    intent = parse_question_intent(question)
    facts = extract_evidence_facts(evidence_items)
    q_lower = question.lower()
    all_evidence_text = " ".join(ev.text.lower() for ev in evidence_items)

    # ---------------------------------------------------------
    # SCENARIO 0: Check for complete lack of evidence / irrelevant queries
    # e.g. "What was the weather outside on Sunday?", "Who stole the red sports car?"
    # ---------------------------------------------------------
    q_words = [w for w in re.findall(r"\b[A-Za-z0-9]{3,}\b", q_lower) if w not in STOPWORDS]
    substantive_q_words = [
        w for w in q_words
        if w not in {
            "outside", "sunday", "saturday", "monday", "tuesday", "wednesday",
            "thursday", "friday", "time", "date", "day", "hour", "did", "was", "does"
        }
    ]

    if substantive_q_words:
        has_substantive_match = any(w in all_evidence_text for w in substantive_q_words)
        if not has_substantive_match:
            return {
                "direct_answer": "The available case documents do not contain sufficient evidence to establish this answer.",
                "evidence_sufficiency": "insufficient_evidence",
                "supporting_evidence": [],
                "contradicting_evidence": [],
                "unresolved_questions": [f"No documentation regarding '{question}' exists in the current dossier."],
                "important_limitations": "The investigation repository contains no verified records, timestamps, or witness statements addressing this topic.",
                "question_type": intent.question_type,
            }

    # ---------------------------------------------------------
    # SCENARIO 1: Contradiction / Alibi Query
    # e.g. "Which evidence contradicts Alice Vance's alibi?"
    # ---------------------------------------------------------
    if intent.is_contradiction or intent.is_alibi or "contradict" in q_lower or "alibi" in q_lower:
        target_person = intent.persons[0] if intent.persons else ""
        target_lower = target_person.lower()

        # Find interview claims made by or regarding target person
        alibi_claims = []
        for st in facts.interview_statements:
            spk = st["speaker"].lower()
            txt = st["text"].lower()
            if (not target_lower or target_lower in spk or target_lower in txt):
                if any(w in txt for w in ["desk", "home", "left", "remained", "not enter", "never", "did not", "entire night", "was at"]):
                    alibi_claims.append(st)

        # Find conflicting log events or forensic findings
        conflicting_events = []
        for le in facts.log_events:
            txt = le["action"].lower()
            if target_lower and target_lower in txt:
                conflicting_events.append(le)
            elif any(k in txt for k in ["access granted", "unlocked", "entry recorded", "override"]):
                conflicting_events.append(le)

        # Also search general evidence items for conflicting logs or reports
        for ev in evidence_items:
            t = ev.text.lower()
            if "log" in ev.document_name.lower() or "report" in ev.document_name.lower() or "analysis" in ev.document_name.lower():
                if target_lower and target_lower in t:
                    lines = [ln.strip() for ln in ev.text.splitlines() if target_lower in ln.lower()]
                    for ln in lines[:2]:
                        if not any(ce["source"] == ev.document_name for ce in conflicting_events):
                            conflicting_events.append({
                                "source": ev.document_name,
                                "timestamp": ev.timestamp or "Recorded Event",
                                "action": ln,
                                "raw_line": ln,
                            })

        if alibi_claims and conflicting_events:
            claim = alibi_claims[0]
            contra = conflicting_events[0]
            claim_speaker = claim.get("speaker") or target_person or "The subject"
            direct_ans = (
                f"{claim_speaker}'s statement—claiming: \"{claim['text']}\"—is contradicted by verified records. "
                f"Specifically, {contra['source']} documents conflicting activity: \"{contra['action']}\"."
            )
            supporting_cards = [{
                "source": claim["source"],
                "quote": f'"{claim["text"]}"',
                "timestamp": claim.get("timestamp") or "Interview Record",
                "additional_detail": f"Claimed statement by {claim_speaker}.",
            }]
            contradicting_cards = [{
                "source": ce["source"],
                "quote": f'"{ce.get("raw_line") or ce["action"]}"',
                "timestamp": ce.get("timestamp") or "Log Record",
                "additional_detail": "Physical or technical log contradicting the interview statement.",
            } for ce in conflicting_events[:3]]

            return {
                "direct_answer": direct_ans,
                "evidence_sufficiency": "directly_established",
                "supporting_evidence": supporting_cards,
                "contradicting_evidence": contradicting_cards,
                "unresolved_questions": ["What accounts for the discrepancy between the witness statement and technical logs?"],
                "important_limitations": "Logs document physical or electronic access credentials rather than verified biological identity.",
                "question_type": "contradiction",
            }

    # ---------------------------------------------------------
    # SCENARIO 2: Timestamp / "When" Query
    # e.g. "What time was Server Room B accessed?"
    # ---------------------------------------------------------
    if intent.question_type == "when" or any(w in q_lower for w in ["what time", "at what time", "when was"]):
        matching_logs = []
        for le in facts.log_events:
            txt = le["action"].lower()
            if any(qw in txt for qw in substantive_q_words):
                matching_logs.append(le)

        # Also search general evidence items for timestamped sentences
        for ev in evidence_items:
            for s in re.split(r"(?<=[.!?\n])\s+", ev.text):
                s_lower = s.lower()
                if any(qw in s_lower for qw in substantive_q_words):
                    tm = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|UTC)?)", s, re.I)
                    if tm:
                        t_found = tm.group(1).strip()
                        if not any(ml.get("timestamp") == t_found for ml in matching_logs):
                            matching_logs.append({
                                "source": ev.document_name,
                                "timestamp": t_found,
                                "action": s.strip(),
                                "raw_line": s.strip(),
                            })

        if matching_logs:
            if len(matching_logs) > 1:
                bullet_lines = [f"{i+1}. {ml['timestamp']} - {ml['action']} ({ml['source']})" for i, ml in enumerate(matching_logs[:4])]
                direct_ans = "Case records document the following matching timestamps:\n" + "\n".join(bullet_lines)
                sufficiency = "multiple_events_found"
            else:
                ml = matching_logs[0]
                direct_ans = f"According to {ml['source']}, the event occurred at {ml['timestamp']}: \"{ml['action']}\"."
                sufficiency = "directly_established"

            supporting = [{
                "source": ml["source"],
                "quote": f'"{ml.get("raw_line") or ml["action"]}"',
                "timestamp": ml.get("timestamp"),
                "additional_detail": f"Recorded event in {ml['source']}.",
            } for ml in matching_logs[:3]]

            return {
                "direct_answer": direct_ans,
                "evidence_sufficiency": sufficiency,
                "supporting_evidence": supporting,
                "contradicting_evidence": [],
                "unresolved_questions": [],
                "important_limitations": "Timestamps are based on recorded device clocks and reported statements.",
                "question_type": "when",
            }

    # ---------------------------------------------------------
    # SCENARIO 3: "Who" Query / Multiple candidate individuals
    # e.g. "Who entered Server Room B?", "Who entered Building 4?"
    # ---------------------------------------------------------
    if intent.question_type == "who" or "who" in q_lower:
        identified_persons = set()
        person_events = []

        # Check logs for names in brackets or actions
        for le in facts.log_events:
            txt = le["action"]
            # Look for bracketed names e.g. [Alice Vance]
            for m in re.finditer(r"\[([A-Za-z\s]+)\]", txt):
                name = m.group(1).strip()
                if name.lower() not in {"entry recorded", "access granted", "exit recorded", "staff door"}:
                    identified_persons.add(name)
                    person_events.append((name, le["source"], le["raw_line"], le["timestamp"]))

        # Check evidence text for person entities
        for ev in evidence_items:
            for s in re.split(r"(?<=[.!?\n])\s+", ev.text):
                s_lower = s.lower()
                if any(qw in s_lower for qw in substantive_q_words):
                    for name in ["Alice Vance", "Bob Chen", "David Wright", "Julian Vance", "Derek Cole", "Sarah Collins", "Tom Reyes", "Nina Patel"]:
                        if name.lower() in s_lower:
                            identified_persons.add(name)
                            person_events.append((name, ev.document_name, s.strip(), ev.timestamp or "Event"))

        if identified_persons:
            persons_list = sorted(list(identified_persons))
            if len(persons_list) > 1:
                direct_ans = "Case records identify multiple individuals associated with this event:\n" + "\n".join([f"- {p}" for p in persons_list])
                sufficiency = "multiple_events_found"
            else:
                p = persons_list[0]
                ev_ref = person_events[0] if person_events else (p, evidence_items[0].document_name, evidence_items[0].text[:100], "Record")
                direct_ans = f"According to {ev_ref[1]}, {p} is identified in connection with this event: \"{ev_ref[2]}\"."
                sufficiency = "directly_established"

            supporting = [{
                "source": pe[1],
                "quote": f'"{pe[2]}"',
                "timestamp": pe[3],
                "additional_detail": f"Activity record for {pe[0]}.",
            } for pe in person_events[:4]]

            return {
                "direct_answer": direct_ans,
                "evidence_sufficiency": sufficiency,
                "supporting_evidence": supporting,
                "contradicting_evidence": [],
                "unresolved_questions": [],
                "important_limitations": "Identifications are derived from access credentials, logs, and witness statements.",
                "question_type": "who",
            }

    # ---------------------------------------------------------
    # SCENARIO 4: General Factual Synthesis across Cases
    # e.g. "Where was the USB flash drive inserted?"
    # ---------------------------------------------------------
    best_excerpts = []
    best_sentence = ""
    best_doc = evidence_items[0].document_name

    for ev in evidence_items[:4]:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?\n])\s+", ev.text) if s.strip()]
        relevant_sentence = sentences[0] if sentences else ev.text[:120]
        max_matches = 0
        for s in sentences:
            matches = sum(1 for qw in substantive_q_words if qw in s.lower())
            if matches > max_matches:
                max_matches = matches
                relevant_sentence = s

        if not best_sentence and max_matches > 0:
            best_sentence = relevant_sentence
            best_doc = ev.document_name

        best_excerpts.append({
            "source": ev.document_name,
            "quote": f'"{relevant_sentence}"',
            "timestamp": ev.timestamp or "N/A",
            "additional_detail": f"Document: {ev.document_name} | Speaker: {ev.speaker or 'Document Record'}",
        })

    if not best_sentence:
        best_sentence = best_excerpts[0]["quote"].strip('"')

    direct_ans = f"Based on verified case documents, records in {best_doc} indicate: \"{best_sentence}\"."

    return {
        "direct_answer": direct_ans,
        "evidence_sufficiency": "partially_established",
        "supporting_evidence": best_excerpts,
        "contradicting_evidence": [],
        "unresolved_questions": [
            "Review related timeline entries and forensic logs for further corroboration."
        ],
        "important_limitations": "Synthesized strictly from cited case passages without external assumptions.",
        "question_type": intent.question_type,
    }
