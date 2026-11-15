"""Conservative presence assessment for timed homicide case records."""

import re
from typing import Sequence

from app.models.schemas import DocumentMetadata
from app.services.contradiction.detector import CLOCK_TIME, TRANSCRIPT_HEADER, clock_minutes


TIME = r"\d{1,2}:\d{2}\s*(?:AM|PM)"
WINDOW = re.compile(
    rf"\bfatal (?:encounter|incident) between ({TIME}) and ({TIME})", re.IGNORECASE
)
MOVEMENT = re.compile(
    rf"\b([A-Z][a-z]+(?: [A-Z][a-z]+)+) (entered|left) ([^.!?]+?) at ({TIME})\b"
)


def assess_suspect(documents: Sequence[DocumentMetadata]) -> str:
    windows = {}
    movements = {}
    restricted_locations = set()
    incident_locations = set()
    for doc in documents:
        for chunk in doc.chunks:
            text = TRANSCRIPT_HEADER.sub("", chunk.text.strip())
            citation = f"[{doc.filename}, {chunk.chunk_id}]"
            incident_locations.update(
                match.casefold() for match in re.findall(
                    r"\bfound unresponsive in ([^.!?]+?) at \d", text, re.IGNORECASE
                )
            )
            for match in WINDOW.finditer(text):
                windows[match.groups()] = citation
            for match in MOVEMENT.finditer(text):
                name, action, location, time = match.groups()
                minute = clock_minutes(CLOCK_TIME.fullmatch(time))
                movements.setdefault((name, location), []).append(
                    (action, minute, time, doc.document_id, citation)
                )
                if action == "left" and "no other visitor" in text.casefold():
                    restricted_locations.add((name, location, minute))

    if not windows:
        return ""
    unresolved = "Suspect assessment: the records do not establish a unique person present during the fatal window."
    if len(windows) != 1:
        return unresolved
    (start_text, end_text), window_source = next(iter(windows.items()))
    start, end = (clock_minutes(CLOCK_TIME.fullmatch(t)) for t in (start_text, end_text))
    if start >= end:
        return unresolved

    candidates = []
    competing_names = set()
    for (name, location), records in movements.items():
        if location.casefold() not in incident_locations:
            continue
        entries = [record for record in records if record[0] == "entered"]
        exits = [record for record in records if record[0] == "left"]
        for exit_record in exits:
            for entry in entries:
                if not entry[1] <= start < end <= exit_record[1]:
                    continue
                corroboration = {
                    record[3]: record[4] for record in entries if record[1] == entry[1]
                }
                competing_names.add(name)
                if len(corroboration) >= 2 and (name, location, exit_record[1]) in restricted_locations:
                    candidates.append((name, location, entry, exit_record, corroboration))
    if not candidates or len(competing_names) != 1:
        return unresolved
    name, location, entry, exit_record, sources = candidates[0]
    return (
        f"Suspect assessment: {name} is the leading suspect based on documented opportunity. "
        f"Two records place {name} entering {location} at {entry[2]} "
        f"{' '.join(list(sources.values())[:2])}. The exit review records departure at "
        f"{exit_record[2]} and reports no other visitor during the interval {exit_record[4]}. "
        f"The estimated fatal window was {start_text} to {end_text} {window_source}. "
        "This supports presence during the estimated window. Responsibility remains an inference."
    )
