import re
import uuid
from functools import lru_cache
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx
from app.config import settings
from app.services.llm_provider import analysis_model_json
from app.services.extraction.date_parser import (
    extract_document_header_date,
    extract_document_header_datetime,
    parse_date_string,
    parse_time_string,
    resolve_sentence_timestamp,
    ParsedEventTimestamp,
)
from app.services.extraction.event_summarizer import summarize_event_to_ground_truth

from app.models.schemas import (
    CaseGraph,
    CaseGraphEdge,
    CaseGraphNode,
    DocumentMetadata,
    DocumentType,
    Entity,
    EntityType,
    Event,
    TemporalLink,
    TemporalRelation,
    TimelineEntry,
)

# Common title prefixes and common organization suffixes
TITLES = ["Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Officer", "Agent", "Inspector", "Detective", "Director", "Chief"]
ORG_INDICATORS = ["Corp", "Inc", "LLC", "Ltd", "Technologies", "Tech", "Security", "Department", "Dept", "Police", "Pharma", "Hospital", "Laboratories", "Labs", "Group", "Agency", "Foundation", "Solutions", "Robotics"]
LOCATION_INDICATORS = ["Room", "Office", "Building", "Hall", "Floor", "Suite", "Vault", "Street", "Avenue", "Boulevard", "Lab", "Center", "Server Room", "Warehouse", "Annex", "Hangar", "Bunker", "Range", "Bay", "Site"]
OBJECT_INDICATORS = ["Keycard", "Badge", "USB", "Dongle", "Flash Drive", "Laptop", "Hard Drive", "Server", "Safe", "Console", "Terminal", "Device", "Camera", "Firmware", "Payload", "Painting", "Canvas", "Cutter", "Crowbar", "Waybill", "Tape", "Sensor"]

MONTHS_AND_DAYS = {"January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
NON_PERSON_WORDS = {"North", "South", "East", "West", "Main", "Rear", "Front", "High", "Low", "Critical", "Active", "Pending", "Final", "Stable", "Custom", "Exclusive", "Direct", "Authorized", "Unauthorized", "Access", "Audit", "Incident", "Security", "Report"}
STOP_WORDS_ENTITY = {"the", "this", "that", "there", "where", "what", "who", "why", "when", "how", "these", "those", "inserted", "used", "accessed", "logged", "local", "remote", "unauthorized", "physical", "system", "final", "stable", "custom", "none", "every", "another", "either", "neither", "initial", "direct", "total", "approximately"}


@lru_cache(maxsize=1)
def load_spacy_model(model_name: str):
    import spacy

    return spacy.load(model_name)


def canonicalize_entity_name(name: str) -> str:
    cleaned = name.strip().strip(".,;:\"'()[]{}<>-`~*")
    cleaned = re.sub(r"^[\s\d\-:_./\\]+", "", cleaned).strip()
    for t in TITLES:
        if cleaned.startswith(t + " "):
            cleaned = cleaned[len(t) + 1:].strip()
    return cleaned


def extract_entities_from_text(
    text: str,
    doc_id: str,
    speaker: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Extracts entities (Person, Org, Location, Object) with high precision
    and links each entity to its exact source sentence.
    """
    entities: Dict[str, Dict[str, Any]] = {}

    def add_entity(name: str, ent_type: EntityType, sentence: str):
        c_name = canonicalize_entity_name(name)
        if len(c_name) < 2 or c_name.lower() in STOP_WORDS_ENTITY:
            return
        if re.fullmatch(r"[\d\s\-:_./\\]+", c_name) or re.fullmatch(r"\d{1,2}:\d{2}(?::\d{2})?", c_name):
            return
        if c_name in MONTHS_AND_DAYS or c_name.lower() in {m.lower() for m in MONTHS_AND_DAYS}:
            return
        if ent_type == EntityType.OBJECT:
            # Drop pure generic nouns without identifier/name
            if c_name.lower() in {"file", "document", "logs", "device", "terminal", "console", "flash drive"}:
                return
            c_name = re.sub(r"^[\d\-]+\s*", "", c_name).strip()
            if len(c_name) < 2:
                return

        key = f"{ent_type.value}:{c_name.lower()}"
        if key not in entities:
            entities[key] = {
                "name": c_name,
                "type": ent_type,
                "mentions": 0,
                "docs": set(),
                "sentences": set(),
            }
        entities[key]["mentions"] += 1
        entities[key]["docs"].add(doc_id)
        if len(sentence.strip()) > 5:
            entities[key]["sentences"].add(sentence.strip())

    # Add document speaker if present
    if speaker:
        add_entity(speaker, EntityType.PERSON, f"Speaker/Author of document: {speaker}")

    sentences = [s.strip() for s in text.split("\n") if s.strip()]
    for sentence in sentences:
        # 1. Person: capitalized name pairs, e.g. "Alice Vance", "Bob Chen", "David Wright"
        # Also handle "Dr. Vance", "Mr. Chen"
        title_pattern = rf"\b(?:{'|'.join(re.escape(t) for t in TITLES)})\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
        for m in re.finditer(title_pattern, sentence):
            add_entity(m.group(1), EntityType.PERSON, sentence)

        person_pairs = re.findall(r"\b([A-Z][a-z]{1,15}\s+[A-Z][a-z]{1,15})\b", sentence)
        for p in person_pairs:
            # Filter out non-person pairs like "Server Room", "October 12", etc.
            words = p.split()
            if any(w in LOCATION_INDICATORS or w in ORG_INDICATORS or w in OBJECT_INDICATORS or w in MONTHS_AND_DAYS or w in NON_PERSON_WORDS for w in words):
                continue
            if words[0] in ["The", "An", "In", "On", "At", "After", "Before", "During", "Since", "While", "Under", "With", "From", "Into"]:
                continue
            add_entity(p, EntityType.PERSON, sentence)

        # 2. Organizations
        for org_ind in ORG_INDICATORS:
            org_matches = re.findall(rf"\b([A-Z][A-Za-z0-9&'-]+(?:\s+[A-Z][A-Za-z0-9&'-]+)*\s+{re.escape(org_ind)})\b", sentence)
            for org in org_matches:
                add_entity(org, EntityType.ORGANIZATION, sentence)

        # 3. Locations
        for loc_ind in LOCATION_INDICATORS:
            loc_matches = re.findall(rf"\b([A-Z0-9][A-Za-z0-9'-]*(?:\s+[A-Z0-9][A-Za-z0-9'-]*)*\s+{re.escape(loc_ind)}(?:\s+[A-Z0-9]+)?)\b", sentence)
            for loc in loc_matches:
                add_entity(loc, EntityType.LOCATION, sentence)
            # Match "Server Room B", "Room 402"
            alt_matches = re.findall(rf"\b({re.escape(loc_ind)}\s+[A-Z0-9]+)\b", sentence)
            for loc in alt_matches:
                add_entity(loc, EntityType.LOCATION, sentence)

        # 4. Objects
        for obj_ind in OBJECT_INDICATORS:
            obj_matches = re.findall(rf"\b([A-Za-z0-9'-]+(?:\s+[A-Za-z0-9'-]+){{0,2}}\s+{re.escape(obj_ind)}(?:\s+#[0-9A-Za-z]+|\s+[A-Za-z0-9]+)?)\b", sentence, re.IGNORECASE)
            for obj in obj_matches:
                # Disallow if starts with stop words or digits
                clean_obj = re.sub(r"^[\d\-:]+\s*", "", obj).strip()
                if clean_obj.lower() not in STOP_WORDS_ENTITY and not any(w in clean_obj.lower().split()[:1] for w in ["a", "an", "the", "inserted", "used"]):
                    add_entity(clean_obj.title(), EntityType.OBJECT, sentence)
            alt_obj = re.findall(rf"\b({re.escape(obj_ind)}\s+(?:#[0-9A-Za-z]+|[A-Za-z0-9._-]+))\b", sentence, re.IGNORECASE)
            for obj in alt_obj:
                add_entity(obj.title(), EntityType.OBJECT, sentence)

    if settings.SPACY_MODEL and sentences:
        labels = {
            "PERSON": EntityType.PERSON,
            "ORG": EntityType.ORGANIZATION,
            "GPE": EntityType.LOCATION,
            "LOC": EntityType.LOCATION,
            "FAC": EntityType.LOCATION,
            "PRODUCT": EntityType.OBJECT,
        }
        for parsed in load_spacy_model(settings.SPACY_MODEL).pipe(sentences):
            for span in parsed.ents:
                if span.label_ in labels:
                    name = canonicalize_entity_name(span.text)
                    existing = entities.get(f"{labels[span.label_].value}:{name.lower()}")
                    if not existing or parsed.text not in existing["sentences"]:
                        add_entity(span.text, labels[span.label_], parsed.text)

    for start in range(0, len(sentences), 20):
        batch = sentences[start:start + 20]
        result = analysis_model_json(
            'Extract named entities as {"entities":[{"name":"verbatim span",'
            '"type":"person|organization|location|object","line":0}]}. Line numbers are zero-based.',
            batch,
        )
        if result is None:
            break
        candidates = result.get("entities")
        if not isinstance(candidates, list):
            continue
        for item in candidates:
            if not isinstance(item, dict):
                continue
            name, label, line = item.get("name"), item.get("type"), item.get("line")
            if not isinstance(name, str) or not name.strip() or type(line) is not int:
                continue
            if not 0 <= line < len(batch) or name not in batch[line]:
                continue
            if not isinstance(label, str) or label not in {t.value for t in EntityType}:
                continue
            entity_type = EntityType(label)
            key = f"{label}:{canonicalize_entity_name(name).lower()}"
            if key not in entities or batch[line] not in entities[key]["sentences"]:
                add_entity(name, entity_type, batch[line])

    return entities


TRANSCRIPT_HEADER = re.compile(r"^\[\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\]\s*[A-Z0-9_ -]{2,25}:\s*")


def is_non_event_sentence(sentence: str) -> bool:
    """
    Filters out system notes, document headers, metadata markers, and pure interview questions.
    """
    s = sentence.strip()
    if not s or len(s) < 6:
        return True
    s_lower = s.lower()
    # System notes and audit disclaimers
    prefixes = [
        "system note:", "audit note:", "audit:", "note:", "notes:",
        "image file:", "uploaded by:", "document ", "document type:",
        "author:", "interviewer:", "interviewee:", "system:", "facility:",
        "subsystem:", "review date:", "interview date:", "interview time:", "date:", "time:", "subject:",
        "from:", "to:", "case id:", "reporting officer:", "case:", "location:"
    ]
    if any(s_lower.startswith(p) for p in prefixes):
        return True
    # Pure interview questions asking for times/events (the reply holds the event)
    if re.match(r"^\[\d{1,2}:\d{2}\s*(?:AM|PM)?\]\s*[A-Z0-9_ -]+:.*\?$", s, re.IGNORECASE):
        return True
    # Conversational salutations, closings, and short dialogue turn-taking without action
    content = re.sub(r"^\[\d{1,2}:\d{2}\s*(?:AM|PM)?\]\s*[A-Z0-9_ -]+:\s*", "", s).strip()
    if len(content.split()) < 4 and not any(k in content.lower() for k in ["left", "enter", "came", "went", "saw", "unlocked", "locked", "took", "stole", "badged", "opened", "swiped"]):
        return True
    if any(cl in content.lower() for cl in ["thank you", "that is all for now", "walk us through your whereabouts", "good morning", "can you confirm"]):
        return True
    # Short conversational replies without action
    if s_lower in {"yes.", "no.", "no, absolutely not.", "not about this map.", "hello mr. grant,", "please keep this between us for now.", "best regards,"}:
        return True
    return False


def parse_timestamp_from_text(text: str) -> Tuple[Optional[str], Optional[datetime], bool]:
    """
    Parses timestamps using date_parser.
    Returns (display_str, parsed_dt_if_exact, is_uncertain).
    """
    ts_obj, _ = resolve_sentence_timestamp(text, None, None)
    if ts_obj.dt:
        return ts_obj.raw_text or ts_obj.display_str, ts_obj.dt, ts_obj.confidence < 0.7

    parsed_t, raw_t, tz_str, precision = parse_time_string(text)
    if parsed_t:
        dt = datetime.combine(date(2024, 1, 1), parsed_t)
        return raw_t or ts_obj.raw_text or ts_obj.display_str, dt, False

    if ts_obj.raw_text:
        return ts_obj.raw_text, None, True
    return None, None, True


def extract_events_and_timeline(
    documents: List[DocumentMetadata],
    known_people: Set[str],
    known_locations: Set[str],
    known_objects: Set[str],
) -> Tuple[List[Event], List[TimelineEntry], List[TemporalLink]]:
    events: List[Event] = []
    temporal_links: List[TemporalLink] = []

    # Action verbs commonly marking investigation events
    EVENT_VERBS = [
        "accessed", "entered", "swiped", "logged", "transferred", "downloaded",
        "saw", "spoke", "met", "discovered", "reported", "left", "arrived",
        "opened", "locked", "unlocked", "noticed", "found", "deleted", "alerted",
        "inquired", "emailed", "photographed", "scanned", "armed", "disarmed", "bypassed"
    ]
    verb_pattern = re.compile(rf"\b({'|'.join(EVENT_VERBS)})\b", re.IGNORECASE)

    event_counter = 0

    for doc in documents:
        doc_header_date, doc_header_time, doc_header_tz = extract_document_header_datetime(doc.cleaned_text)
        current_context_date = doc_header_date

        # If document is an email and has header date + time, add the email transmission event
        is_email = doc.document_type == DocumentType.EMAIL or "email" in doc.filename.lower() or "subject:" in doc.cleaned_text.lower()[:500]
        if is_email and doc_header_date and doc_header_time:
            from_match = re.search(r"^(?:From):\s*([^\n\r]+)", doc.cleaned_text[:1000], re.MULTILINE)
            to_match = re.search(r"^(?:To):\s*([^\n\r]+)", doc.cleaned_text[:1000], re.MULTILINE)
            subj_match = re.search(r"^(?:Subject):\s*([^\n\r]+)", doc.cleaned_text[:1000], re.MULTILINE)
            sender = from_match.group(1).strip() if from_match else (doc.speaker or "Sender")
            recipient = to_match.group(1).strip() if to_match else "Recipient"
            subject = subj_match.group(1).strip() if subj_match else "Email transmission"
            body_lines = [ln.strip() for ln in doc.cleaned_text.split("\n") if ln.strip() and not is_non_event_sentence(ln)]
            body_snip = body_lines[0] if body_lines else f"Email sent from {sender} to {recipient}"
            dt_email = datetime.combine(doc_header_date, doc_header_time)
            disp_time = dt_email.strftime("%Y-%m-%d %H:%M:%S")

            email_parts = []
            for p in known_people:
                if p.lower() in sender.lower() or p.lower() in recipient.lower():
                    email_parts.append(p)
            if not email_parts and doc.speaker:
                email_parts.append(doc.speaker)

            event_counter += 1
            ev_id = f"ev_{doc.document_id}_{event_counter}"
            email_event = Event(
                event_id=ev_id,
                description=f"{sender} emails {recipient} regarding {subject}: {body_snip}",
                participants=list(set(email_parts)),
                location=None,
                time_str=disp_time,
                parsed_timestamp=dt_email.isoformat(),
                uses_objects=[],
                document_id=doc.document_id,
                document_name=doc.filename,
                source_sentence=body_snip,
                uncertainty=False,
                parsed_date=doc_header_date.isoformat(),
                parsed_time=doc_header_time.strftime("%H:%M:%S"),
                timezone=doc_header_tz,
                precision="minute",
                confidence=1.0,
                is_date_inferred=False,
                raw_timestamp_text=f"{doc_header_date.isoformat()} {doc_header_time.strftime('%H:%M:%S')}",
            )
            events.append(email_event)

        is_interview = doc.document_type == DocumentType.INTERVIEW or "interview" in doc.filename.lower()
        sentences = [s.strip() for s in doc.cleaned_text.split("\n") if s.strip()]
        for sentence in sentences:
            # Check for explicit date mentions in every sentence to keep contextual date updated
            ts_obj, updated_context = resolve_sentence_timestamp(
                sentence, doc_header_date, current_context_date, doc.document_type.value
            )
            current_context_date = updated_context

            if is_non_event_sentence(sentence):
                continue

            # In interview transcripts, testimonial Q&A lines are subjective claims for cross-examination,
            # not physical timeline events, UNLESS they describe direct third-party physical sightings
            # (saw, witnessed, spotted, carrying).
            if is_interview and TRANSCRIPT_HEADER.match(sentence):
                s_lower = sentence.lower()
                has_sighting = any(k in s_lower for k in [
                    "saw ", "sees ", "spotted ", "witnessed ", "carrying "
                ])
                if not has_sighting:
                    continue

            event_text = TRANSCRIPT_HEADER.sub("", sentence).strip()
            has_verb = bool(verb_pattern.search(event_text))
            has_log_action = bool(re.search(r"\b(?:ACCESS_GRANTED|ENTRY|EXIT|UNLOCKED|LOCKED|ARMED|DISARMED|MOTION_DETECTED|DOOR_RELEASE|BYPASS|SENSOR_BYPASS)\b", sentence))

            # Must have an action verb, log action, or explicit time + entity
            if not has_verb and not has_log_action and not ts_obj.raw_text:
                continue

            # Identify participants (handling standard names, underscored names, and initialed aliases)
            participants = []
            for person in known_people:
                p_tokens = person.lower().split()
                if re.search(rf"\b{re.escape(person)}\b", sentence, re.IGNORECASE):
                    participants.append(person)
                elif len(p_tokens) >= 2:
                    initial_last = f"{p_tokens[0][0]}\\.?\\s+{p_tokens[-1]}"
                    user_alias = f"{p_tokens[0][0]}{p_tokens[-1]}"
                    joined_under = "_".join(p_tokens)
                    if (re.search(rf"\b{initial_last}\b", sentence, re.IGNORECASE) or
                        re.search(rf"\b{user_alias}\b", sentence, re.IGNORECASE) or
                        re.search(rf"\b{joined_under}\b", sentence, re.IGNORECASE)):
                        participants.append(person)

            if not participants and doc.speaker:
                if sentence.startswith(f"{doc.speaker}:") or "I " in sentence or "my " in sentence:
                    participants.append(doc.speaker)

            # Identify locations
            loc_found = None
            for loc in known_locations:
                if re.search(rf"\b{re.escape(loc)}\b", sentence, re.IGNORECASE):
                    loc_found = loc
                    break
                loc_under = loc.replace(" ", "_")
                if re.search(rf"\b{re.escape(loc_under)}\b", sentence, re.IGNORECASE):
                    loc_found = loc
                    break

            # Identify objects
            obj_found = []
            for obj in known_objects:
                if re.search(rf"\b{re.escape(obj)}\b", sentence, re.IGNORECASE):
                    obj_found.append(obj)
                elif " " in obj or "_" in obj:
                    obj_under = obj.replace(" ", "_")
                    if re.search(rf"\b{re.escape(obj_under)}\b", sentence, re.IGNORECASE):
                        obj_found.append(obj)

            if participants or loc_found or obj_found or ts_obj.raw_text:
                event_counter += 1
                ev_id = f"ev_{doc.document_id}_{event_counter}"

                event = Event(
                    event_id=ev_id,
                    description=event_text,
                    participants=list(set(participants)),
                    location=loc_found,
                    time_str=ts_obj.display_str,
                    parsed_timestamp=ts_obj.parsed_timestamp_iso,
                    uses_objects=list(set(obj_found)),
                    document_id=doc.document_id,
                    document_name=doc.filename,
                    source_sentence=sentence,
                    uncertainty=(ts_obj.confidence < 0.7),
                    parsed_date=ts_obj.parsed_date_iso,
                    parsed_time=ts_obj.parsed_time_iso,
                    timezone=ts_obj.timezone_str,
                    precision=ts_obj.precision,
                    confidence=ts_obj.confidence,
                    is_date_inferred=ts_obj.is_date_inferred,
                    raw_timestamp_text=ts_obj.raw_text,
                )
                events.append(event)

    # Cross-document duplicate detection and merging
    merged_events: List[Event] = []
    for ev in events:
        matched = False
        if ev.parsed_date and ev.parsed_time:
            for m in merged_events:
                if m.parsed_date == ev.parsed_date and m.parsed_time:
                    try:
                        t1 = datetime.strptime(m.parsed_time, "%H:%M:%S")
                        t2 = datetime.strptime(ev.parsed_time, "%H:%M:%S")
                        diff_sec = abs((t1 - t2).total_seconds())
                        common_people = set(m.participants) & set(ev.participants)
                        same_loc = m.location and ev.location and m.location == ev.location
                        if diff_sec <= 180 and (common_people or same_loc) and m.document_name != ev.document_name:
                            # Merge into m
                            m.secondary_sources.append({
                                "document_name": ev.document_name,
                                "document_id": ev.document_id,
                                "source_sentence": ev.source_sentence,
                                "time_str": ev.time_str,
                            })
                            m.participants = list(set(m.participants + ev.participants))
                            m.uses_objects = list(set(m.uses_objects + ev.uses_objects))
                            if ev.confidence > m.confidence:
                                m.confidence = ev.confidence
                            matched = True
                            break
                    except Exception:
                        pass
        if not matched:
            merged_events.append(ev)

    timeline: List[TimelineEntry] = []
    for ev in merged_events:
        sort_key = (
            ev.parsed_date.replace("-", "") + ev.parsed_time.replace(":", "")
            if (ev.parsed_date and ev.parsed_time)
            else "99999999999999"
        )
        clean_desc = summarize_event_to_ground_truth(
            sentence=ev.source_sentence,
            speaker=ev.participants[0] if ev.participants else None,
            participants=ev.participants,
            location=ev.location,
            objects=ev.uses_objects,
            time_str=ev.time_str,
            document_name=ev.document_name,
        )
        tl_entry = TimelineEntry(
            entry_id=f"tl_{ev.event_id}",
            event_id=ev.event_id,
            timestamp_display=ev.time_str or "Time unspecified",
            event_description=clean_desc,
            clean_summary=clean_desc,
            participants=ev.participants,
            location=ev.location,
            document_name=ev.document_name,
            document_type=DocumentType.OTHER,
            document_id=ev.document_id,
            source_sentence=ev.source_sentence,
            is_uncertain=ev.uncertainty,
            sort_key=sort_key,
            parsed_date=ev.parsed_date,
            parsed_time=ev.parsed_time,
            timezone=ev.timezone,
            precision=ev.precision,
            confidence=ev.confidence,
            is_date_inferred=ev.is_date_inferred,
            raw_timestamp_text=ev.raw_timestamp_text,
            secondary_sources=ev.secondary_sources,
        )
        timeline.append(tl_entry)

    # Sort timeline: deterministic chronological sorting where known timestamps come first in order
    timeline.sort(key=lambda x: (x.sort_key, x.timestamp_display))

    # Build temporal links between consecutive timeline events
    for i in range(len(timeline) - 1):
        curr_e = timeline[i]
        next_e = timeline[i + 1]
        rel = TemporalRelation.BEFORE
        if curr_e.sort_key == next_e.sort_key and curr_e.sort_key != "99999999999999":
            rel = TemporalRelation.SAME_TIME
        elif curr_e.sort_key == "99999999999999" or next_e.sort_key == "99999999999999":
            rel = TemporalRelation.UNKNOWN

        temporal_links.append(
            TemporalLink(
                source_event_id=curr_e.event_id,
                target_event_id=next_e.event_id,
                relation=rel,
                source_sentence=f"{curr_e.timestamp_display} -> {next_e.timestamp_display}",
            )
        )

    return merged_events, timeline, temporal_links

    return events, timeline, temporal_links


def build_case_graph(
    documents: List[DocumentMetadata],
    entities: List[Entity],
    events: List[Event],
    temporal_links: List[TemporalLink],
) -> CaseGraph:
    """
    Constructs the NetworkX case graph as specified in Slide 16.
    Nodes:
      - Document (Interview, Email, Report, Log, Other)
      - Entity (Person, Organization, Location, Object)
      - Event (Action)
      - Time (Temporal)
    Edges:
      - Person -> stated_in -> Document
      - Person -> involved_in -> Event
      - Person -> works_for -> Organization
      - Event -> before/after/overlap/same_time -> Event
      - Event -> occurs_at_time -> Time
      - Event -> located_at -> Location
      - Event -> uses -> Object
      - Document -> provides_evidence -> Event
    """
    g = nx.MultiDiGraph()
    graph_nodes: List[CaseGraphNode] = []
    graph_edges: List[CaseGraphEdge] = []
    added_node_ids = set()

    def add_node(node_id: str, label: str, node_type: str, sub_type: Optional[str] = None, props: Optional[Dict[str, Any]] = None):
        if node_id not in added_node_ids:
            props = props or {}
            g.add_node(node_id, label=label, node_type=node_type, sub_type=sub_type, **props)
            graph_nodes.append(CaseGraphNode(id=node_id, label=label, node_type=node_type, sub_type=sub_type, properties=props))
            added_node_ids.add(node_id)

    def add_edge(source: str, target: str, relation: str, evidence: Optional[str] = None):
        edge_id = f"edge_{source}_{relation}_{target}_{len(graph_edges)}"
        g.add_edge(source, target, id=edge_id, relation=relation, evidence_sentence=evidence)
        graph_edges.append(CaseGraphEdge(id=edge_id, source=source, target=target, relation=relation, evidence_sentence=evidence))

    # 1. Document Nodes
    for doc in documents:
        doc_node_id = f"doc_node_{doc.document_id}"
        add_node(
            doc_node_id,
            label=doc.filename,
            node_type="document",
            sub_type=doc.document_type.value,
            props={"filename": doc.filename, "document_type": doc.document_type.value, "speaker": doc.speaker}
        )

    # 2. Entity Nodes
    for ent in entities:
        ent_node_id = f"ent_node_{ent.entity_id}"
        add_node(
            ent_node_id,
            label=ent.name,
            node_type="entity",
            sub_type=ent.entity_type.value,
            props={"mentions": ent.mentions_count, "entity_type": ent.entity_type.value}
        )
        # Person -> stated_in -> Document
        if ent.entity_type == EntityType.PERSON:
            for doc_id in ent.document_ids:
                doc_node_id = f"doc_node_{doc_id}"
                if doc_node_id in added_node_ids:
                    add_edge(ent_node_id, doc_node_id, "stated_in", ent.source_sentences[0] if ent.source_sentences else None)

    # 3. Organization relations (Person -> works_for -> Organization heuristic)
    org_nodes = [e for e in entities if e.entity_type == EntityType.ORGANIZATION]
    person_nodes = [e for e in entities if e.entity_type == EntityType.PERSON]
    for p in person_nodes:
        for org in org_nodes:
            # Check if mentioned together in any sentence
            for sent in p.source_sentences:
                if org.name.lower() in sent.lower():
                    add_edge(f"ent_node_{p.entity_id}", f"ent_node_{org.entity_id}", "works_for", sent)
                    break

    # 4. Event Nodes, Time Nodes & incident edges
    for ev in events:
        ev_node_id = f"ev_node_{ev.event_id}"
        short_label = ev.description[:35] + ("..." if len(ev.description) > 35 else "")
        add_node(
            ev_node_id,
            label=short_label,
            node_type="event",
            sub_type="action",
            props={"description": ev.description, "time": ev.time_str, "location": ev.location}
        )

        # Document -> provides_evidence -> Event
        doc_node_id = f"doc_node_{ev.document_id}"
        if doc_node_id in added_node_ids:
            add_edge(doc_node_id, ev_node_id, "provides_evidence", ev.source_sentence)

        # Person -> involved_in -> Event
        for p_name in ev.participants:
            # find entity id
            p_ent = next((e for e in person_nodes if e.name.lower() == p_name.lower()), None)
            if p_ent:
                add_edge(f"ent_node_{p_ent.entity_id}", ev_node_id, "involved_in", ev.source_sentence)

        # Event -> located_at -> Location
        if ev.location:
            loc_ent = next((e for e in entities if e.entity_type == EntityType.LOCATION and e.name.lower() in ev.location.lower()), None)
            if loc_ent:
                add_edge(ev_node_id, f"ent_node_{loc_ent.entity_id}", "located_at", ev.source_sentence)

        # Event -> uses -> Object
        for obj_name in ev.uses_objects:
            obj_ent = next((e for e in entities if e.entity_type == EntityType.OBJECT and obj_name.lower() in e.name.lower()), None)
            if obj_ent:
                add_edge(ev_node_id, f"ent_node_{obj_ent.entity_id}", "uses", ev.source_sentence)

        # Event -> occurs_at_time -> Time
        if ev.time_str and ev.time_str != "Time unspecified":
            time_node_id = f"time_node_{ev.time_str.replace(' ', '_').replace(':', '')[:20]}"
            add_node(time_node_id, label=ev.time_str, node_type="time", sub_type="temporal")
            add_edge(ev_node_id, time_node_id, "occurs_at_time", ev.source_sentence)

    # 5. Event -> before/after/overlap/same_time -> Event
    for link in temporal_links:
        src = f"ev_node_{link.source_event_id}"
        tgt = f"ev_node_{link.target_event_id}"
        if src in added_node_ids and tgt in added_node_ids and link.relation != TemporalRelation.UNKNOWN:
            add_edge(src, tgt, link.relation.value, link.source_sentence)

    return CaseGraph(nodes=graph_nodes, edges=graph_edges)


def run_extraction_pipeline(
    documents: List[DocumentMetadata]
) -> Tuple[List[Entity], List[Event], List[TimelineEntry], CaseGraph]:
    """
    Full Module 2 extraction pipeline across all case documents.
    """
    raw_entities_map: Dict[str, Dict[str, Any]] = {}

    for doc in documents:
        doc_ents = extract_entities_from_text(doc.cleaned_text, doc.document_id, doc.speaker)
        for key, val in doc_ents.items():
            if key not in raw_entities_map:
                raw_entities_map[key] = {
                    "name": val["name"],
                    "type": val["type"],
                    "mentions": 0,
                    "docs": set(),
                    "sentences": set(),
                }
            raw_entities_map[key]["mentions"] += val["mentions"]
            raw_entities_map[key]["docs"].update(val["docs"])
            raw_entities_map[key]["sentences"].update(val["sentences"])

    # Coreference aliasing: resolve short names to full names (e.g. "Alice" -> "Alice Vance")
    person_full_names = [
        val["name"] for val in raw_entities_map.values()
        if val["type"] == EntityType.PERSON and len(val["name"].split()) >= 2
    ]

    entities_list: List[Entity] = []
    processed_names = set()

    for key, val in raw_entities_map.items():
        name = val["name"]
        ent_type = val["type"]

        if ent_type == EntityType.PERSON:
            # Check if this is a single name that belongs to an already known full name
            matching_full = next((fn for fn in person_full_names if fn != name and name in fn.split()), None)
            if matching_full and len(name.split()) == 1:
                # Merge into matching full name
                full_key = f"{EntityType.PERSON.value}:{matching_full.lower()}"
                if full_key in raw_entities_map:
                    raw_entities_map[full_key]["mentions"] += val["mentions"]
                    raw_entities_map[full_key]["docs"].update(val["docs"])
                    raw_entities_map[full_key]["sentences"].update(val["sentences"])
                    continue

        if name.lower() in processed_names:
            continue
        processed_names.add(name.lower())

        ent_id = f"ent_{uuid.uuid4().hex[:6]}"
        entities_list.append(
            Entity(
                entity_id=ent_id,
                name=name,
                entity_type=ent_type,
                mentions_count=val["mentions"],
                document_ids=list(val["docs"]),
                source_sentences=list(val["sentences"])[:10],
            )
        )

    # Sort entities by mention count
    entities_list.sort(key=lambda x: x.mentions_count, reverse=True)

    known_people = {e.name for e in entities_list if e.entity_type == EntityType.PERSON}
    known_locations = {e.name for e in entities_list if e.entity_type == EntityType.LOCATION}
    known_objects = {e.name for e in entities_list if e.entity_type == EntityType.OBJECT}

    # Extract Events and Timeline
    events, timeline, temporal_links = extract_events_and_timeline(
        documents, known_people, known_locations, known_objects
    )

    # Build Case Graph
    case_graph = build_case_graph(documents, entities_list, events, temporal_links)

    return entities_list, events, timeline, case_graph
