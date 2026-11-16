import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GroundTruthEntityGroup(BaseModel):
    persons: List[str] = Field(default_factory=list)
    organizations: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    objects: List[str] = Field(default_factory=list)


class GroundTruthTimelineEvent(BaseModel):
    time: str
    event: str


class GroundTruthContradiction(BaseModel):
    id: Optional[str] = None
    entity: Optional[str] = None
    topic: Optional[str] = None
    doc_a: Optional[str] = None
    speaker_a: Optional[str] = None
    statement_a: str
    doc_b: Optional[str] = None
    speaker_b: Optional[str] = None
    statement_b: str
    type: str = "confirmed_contradiction"


class GroundTruthHypothesis(BaseModel):
    title: str
    description: str
    is_correct: bool = False


class GroundTruthCase(BaseModel):
    case_id: str
    case_name: str
    document_count: int = 0
    is_held_out: bool = False
    true_entities: GroundTruthEntityGroup = Field(default_factory=GroundTruthEntityGroup)
    true_timeline: List[GroundTruthTimelineEvent] = Field(default_factory=list)
    planted_contradictions: List[GroundTruthContradiction] = Field(default_factory=list)
    correct_hypothesis: GroundTruthHypothesis
    decoy_hypotheses: List[GroundTruthHypothesis] = Field(default_factory=list)


def normalize_ground_truth_data(raw_data: Dict[str, Any]) -> GroundTruthCase:
    """
    Adapter that normalizes multiple ground-truth schema formats:
    - Supports decoy_hypotheses as list of dicts or list of strings
    - Supports alternative key names: 'decoys', 'timeline', 'contradictions'
    - Rejects malformed records with descriptive validation errors
    """
    case_id = raw_data.get("case_id")
    if not case_id:
        raise ValueError("Ground-truth record missing required 'case_id' field.")

    case_name = raw_data.get("case_name", case_id)
    doc_count = raw_data.get("document_count", 0)
    is_held_out = raw_data.get("is_held_out", False)

    # 1. Normalize entities
    ent_raw = raw_data.get("true_entities", {})
    entities = GroundTruthEntityGroup(
        persons=[str(p).strip() for p in ent_raw.get("persons", []) if str(p).strip()],
        organizations=[str(o).strip() for o in ent_raw.get("organizations", []) if str(o).strip()],
        locations=[str(l).strip() for l in ent_raw.get("locations", []) if str(l).strip()],
        objects=[str(ob).strip() for ob in ent_raw.get("objects", []) if str(ob).strip()],
    )

    # 2. Normalize timeline
    tl_raw = raw_data.get("true_timeline", raw_data.get("timeline", []))
    timeline = []
    for item in tl_raw:
        if isinstance(item, dict) and "event" in item:
            t = str(item.get("time", "Time unspecified")).strip()
            ev = str(item.get("event", "")).strip()
            if ev:
                timeline.append(GroundTruthTimelineEvent(time=t, event=ev))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            t = str(item[0]).strip()
            ev = str(item[1]).strip()
            if ev:
                timeline.append(GroundTruthTimelineEvent(time=t, event=ev))

    # 3. Normalize contradictions
    c_raw = raw_data.get("planted_contradictions", raw_data.get("contradictions", []))
    contradictions = []
    for c in c_raw:
        if isinstance(c, dict) and "statement_a" in c and "statement_b" in c:
            contradictions.append(
                GroundTruthContradiction(
                    id=c.get("id"),
                    entity=c.get("entity"),
                    topic=c.get("topic"),
                    doc_a=c.get("doc_a"),
                    speaker_a=c.get("speaker_a"),
                    statement_a=str(c.get("statement_a", "")).strip(),
                    doc_b=c.get("doc_b"),
                    speaker_b=c.get("speaker_b"),
                    statement_b=str(c.get("statement_b", "")).strip(),
                    type=c.get("type", "confirmed_contradiction"),
                )
            )

    # 4. Normalize correct hypothesis
    ch_raw = raw_data.get("correct_hypothesis")
    if not ch_raw:
        raise ValueError(f"Ground-truth record for '{case_id}' missing 'correct_hypothesis'.")
    if isinstance(ch_raw, dict):
        title = str(ch_raw.get("title", "Correct Hypothesis")).strip()
        desc = str(ch_raw.get("description", title)).strip()
    elif isinstance(ch_raw, str):
        title = ch_raw.strip()
        desc = ch_raw.strip()
    else:
        raise ValueError(f"Malformed correct_hypothesis in '{case_id}': expected dict or string.")
    correct_hyp = GroundTruthHypothesis(title=title, description=desc, is_correct=True)

    # 5. Normalize decoy hypotheses (handles list of dicts, list of strings, or 'decoys' key)
    dec_raw = raw_data.get("decoy_hypotheses", raw_data.get("decoys", []))
    decoys = []
    for dec in dec_raw:
        if isinstance(dec, dict):
            d_title = str(dec.get("title", "Decoy Hypothesis")).strip()
            d_desc = str(dec.get("description", d_title)).strip()
            decoys.append(GroundTruthHypothesis(title=d_title, description=d_desc, is_correct=False))
        elif isinstance(dec, str):
            clean_str = dec.strip()
            if clean_str:
                decoys.append(GroundTruthHypothesis(title=clean_str, description=clean_str, is_correct=False))

    return GroundTruthCase(
        case_id=case_id,
        case_name=case_name,
        document_count=doc_count,
        is_held_out=is_held_out,
        true_entities=entities,
        true_timeline=timeline,
        planted_contradictions=contradictions,
        correct_hypothesis=correct_hyp,
        decoy_hypotheses=decoys,
    )


def load_ground_truth_case(file_path: Union[str, Path]) -> GroundTruthCase:
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"Ground truth file not found: {p}")
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return normalize_ground_truth_data(data)
