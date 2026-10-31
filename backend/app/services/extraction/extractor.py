import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx

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
ORG_INDICATORS = ["Corp", "Inc", "LLC", "Ltd", "Technologies", "Tech", "Security", "Department", "Dept", "Police", "Pharma", "Hospital", "Laboratories", "Labs", "Group", "Agency", "Foundation"]
LOCATION_INDICATORS = ["Room", "Office", "Building", "Hall", "Floor", "Suite", "Vault", "Street", "Avenue", "Boulevard", "Lab", "Center", "Server Room", "Warehouse", "Annex"]
OBJECT_INDICATORS = ["Keycard", "Badge", "USB", "Drive", "Laptop", "Server", "File", "Document", "Safe", "Console", "Terminal", "Device", "Hard Drive", "Camera", "Logs"]


def canonicalize_entity_name(name: str) -> str:
    cleaned = name.strip().strip(".,;:\"'()")
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
        if len(c_name) < 2 or c_name.lower() in ["the", "this", "that", "there", "where", "what", "who", "why"]:
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
            if any(w in LOCATION_INDICATORS or w in ORG_INDICATORS or w in OBJECT_INDICATORS for w in words):
                continue
            if words[0] in ["The", "An", "In", "On", "At", "After", "Before", "During", "Since", "While", "Under"]:
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
            obj_matches = re.findall(rf"\b([A-Za-z0-9'-]+(?:\s+[A-Za-z0-9'-]+)*\s+{re.escape(obj_ind)}(?:\s+#[0-9A-Z]+)?)\b", sentence, re.IGNORECASE)
            for obj in obj_matches:
                add_entity(obj.title(), EntityType.OBJECT, sentence)
            alt_obj = re.findall(rf"\b({re.escape(obj_ind)}(?:\s+#[0-9A-Z]+)?)\b", sentence, re.IGNORECASE)
            for obj in alt_obj:
                add_entity(obj.title(), EntityType.OBJECT, sentence)

    return entities


def parse_timestamp_from_text(text: str) -> Tuple[Optional[str], Optional[datetime], bool]:
    """
    Parses timestamps (clock times, ISO dates, relative times).
    Returns (raw_time_str, parsed_dt_if_exact, is_uncertain).
    """
    # 1. ISO or explicit date + time: "2024-10-12 21:15:00" or "10/12/2024 09:15 PM"
    iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?)\b", text)
    if iso_match:
        s = iso_match.group(1).replace("T", " ")
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                dt = datetime.strptime(s, fmt)
                return s, dt, False
            except ValueError:
                pass
        return s, None, False

    # 2. Clock times: e.g. "10:15 PM", "22:15", "9:30 AM"
    time_match = re.search(r"\b(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)\b", text)
    if time_match:
        t_str = time_match.group(1).strip()
        # Parse standard 12-hour or 24-hour time
        for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M:%S", "%H:%M"):
            try:
                dt_time = datetime.strptime(t_str.upper(), fmt)
                # Assign arbitrary base date for relative sorting
                dt = datetime(2024, 1, 1, dt_time.hour, dt_time.minute, dt_time.second)
                return t_str, dt, False
            except ValueError:
                pass
        return t_str, None, False

    # 3. Relative or approximate time phrases
    approx_match = re.search(r"\b(around|approximately|shortly before|shortly after|between)\s+([A-Za-z0-9: ]+?(?:AM|PM|hours|midnight|noon))\b", text, re.IGNORECASE)
    if approx_match:
        return approx_match.group(0).strip(), None, True

    return None, None, True


def extract_events_and_timeline(
    documents: List[DocumentMetadata],
    known_people: Set[str],
    known_locations: Set[str],
    known_objects: Set[str],
) -> Tuple[List[Event], List[TimelineEntry], List[TemporalLink]]:
    events: List[Event] = []
    timeline: List[TimelineEntry] = []
    temporal_links: List[TemporalLink] = []

    # Action verbs commonly marking investigation events
    EVENT_VERBS = [
        "accessed", "entered", "swiped", "logged", "transferred", "downloaded",
        "saw", "spoke", "met", "discovered", "reported", "left", "arrived",
        "opened", "locked", "unlocked", "noticed", "found", "deleted", "alerted"
    ]
    verb_pattern = re.compile(rf"\b({'|'.join(EVENT_VERBS)})\b", re.IGNORECASE)

    event_counter = 0

    for doc in documents:
        sentences = [s.strip() for s in doc.cleaned_text.split("\n") if s.strip()]
        for sentence in sentences:
            has_verb = bool(verb_pattern.search(sentence))
            time_str, dt, is_uncertain = parse_timestamp_from_text(sentence)

            # Check if this sentence represents an event (either has an event verb, or has a time stamp and entity)
            if not has_verb and not time_str:
                continue

            # Identify participants
            participants = []
            for person in known_people:
                if re.search(rf"\b{re.escape(person)}\b", sentence, re.IGNORECASE):
                    participants.append(person)
            if not participants and doc.speaker:
                # If interview/statement dialogue, speaker is participant
                if sentence.startswith(f"{doc.speaker}:") or f"I " in sentence or f"my " in sentence:
                    participants.append(doc.speaker)

            # Identify locations
            loc_found = None
            for loc in known_locations:
                if re.search(rf"\b{re.escape(loc)}\b", sentence, re.IGNORECASE):
                    loc_found = loc
                    break

            # Identify objects
            obj_found = []
            for obj in known_objects:
                if re.search(rf"\b{re.escape(obj)}\b", sentence, re.IGNORECASE):
                    obj_found.append(obj)

            # If it has at least one participant, location, object, or explicit timestamp
            if participants or loc_found or obj_found or time_str:
                event_counter += 1
                ev_id = f"ev_{doc.document_id}_{event_counter}"

                display_time = time_str or (doc.timestamp if doc.timestamp else "Time unspecified")
                sort_key = dt.strftime("%Y%m%d%H%M%S") if dt else "99999999999999"

                event = Event(
                    event_id=ev_id,
                    description=sentence,
                    participants=list(set(participants)),
                    location=loc_found,
                    time_str=display_time,
                    parsed_timestamp=dt.isoformat() if dt else None,
                    uses_objects=list(set(obj_found)),
                    document_id=doc.document_id,
                    document_name=doc.filename,
                    source_sentence=sentence,
                    uncertainty=is_uncertain,
                )
                events.append(event)

                timeline_entry = TimelineEntry(
                    entry_id=f"tl_{ev_id}",
                    event_id=ev_id,
                    timestamp_display=display_time,
                    event_description=sentence,
                    participants=event.participants,
                    location=loc_found,
                    document_name=doc.filename,
                    document_type=doc.document_type,
                    source_sentence=sentence,
                    is_uncertain=is_uncertain,
                    sort_key=sort_key,
                )
                timeline.append(timeline_entry)

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
