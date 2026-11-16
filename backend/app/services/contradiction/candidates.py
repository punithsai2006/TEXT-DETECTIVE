"""Conservative blocking proposes comparisons; similarity never establishes identity.

Enhanced with entity normalization, alias detection, shared location/object matching,
and semantic similarity with graceful fallback.
"""
import re
from difflib import SequenceMatcher
from itertools import combinations
from typing import Any, Dict, Iterator, List, Optional, Tuple

TITLES = {"dr", "mr", "mrs", "ms", "officer", "agent", "inspector", "detective", "director", "chief", "prof"}
STATE_VALUES = {
    "locked", "open", "unlocked", "closed", "present", "absent",
    "true", "false", "on", "off", "none", "empty", "full", "active", "inactive"
}


def normalized(value: Optional[str]) -> str:
    tokens = re.findall(r"\w+", (value or "").casefold())
    # Strip common title prefixes from entities
    if tokens and tokens[0] in TITLES:
        tokens = tokens[1:]
    return " ".join(tokens)


def subjects_compatible(subj_a: str, subj_b: str) -> bool:
    """Check if subjects match exactly or match as common alias (e.g. A. Rao vs Anita Rao)."""
    norm_a = normalized(subj_a)
    norm_b = normalized(subj_b)
    if not norm_a or not norm_b:
        return False
    if norm_a == norm_b:
        return True

    # Check for initial + surname alias (e.g. "a rao" vs "anita rao")
    parts_a = norm_a.split()
    parts_b = norm_b.split()
    if len(parts_a) >= 2 and len(parts_b) >= 2:
        surname_a, surname_b = parts_a[-1], parts_b[-1]
        if surname_a == surname_b:
            first_a, first_b = parts_a[0], parts_b[0]
            if first_a[0] == first_b[0]:
                return True
    return False


def locations_compatible(loc_a: Optional[str], loc_b: Optional[str]) -> bool:
    """Check if two claims reference the same key location."""
    norm_a = normalized(loc_a)
    norm_b = normalized(loc_b)
    if not norm_a or not norm_b:
        return False
    if norm_a == norm_b:
        return True
    return SequenceMatcher(None, norm_a, norm_b).ratio() >= 0.80


def objects_compatible(obj_a: Optional[str], obj_b: Optional[str]) -> bool:
    """Check if two claims reference the same specific target object or device."""
    norm_a = normalized(obj_a)
    norm_b = normalized(obj_b)
    if not norm_a or not norm_b:
        return False
    if norm_a == norm_b:
        return True
    return SequenceMatcher(None, norm_a, norm_b).ratio() >= 0.80


def candidate_pairs(claims: List[Dict[str, Any]], embedding_model: Any = None) -> Iterator[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Generate candidate claim pairs for contradiction analysis.

    Conservative filtering: pairs must share an entity/alias, or share a specific physical object,
    exhibiting predicate overlap, shared event scope, or semantic affinity.
    """
    vectors = {}
    if embedding_model is not None:
        try:
            import numpy as np
            predicates = sorted({normalized(c["predicate"]) for c in claims if c.get("predicate")})
            if predicates:
                matrix = embedding_model.encode(predicates, convert_to_numpy=True)
                vectors = {p: v / max(float(np.linalg.norm(v)), 1e-9) for p, v in zip(predicates, matrix)}
        except Exception:
            vectors = {}

    for a, b in combinations(claims, 2):
        subj_match = subjects_compatible(a.get("subject", ""), b.get("subject", ""))
        loc_match = locations_compatible(a.get("location"), b.get("location"))
        obj_match = objects_compatible(a.get("object"), b.get("object"))

        # If object is merely a state/status value (e.g. "locked", "open"), it does not constitute a shared entity anchor
        norm_obj_a = normalized(a.get("object"))
        norm_obj_b = normalized(b.get("object"))
        if norm_obj_a in STATE_VALUES or norm_obj_b in STATE_VALUES:
            obj_match = False

        # Must have at least a compatible subject or a shared specific physical object
        if not (subj_match or obj_match):
            continue

        same_scope = bool(a.get("event_scope")) and normalized(a.get("event_scope")) == normalized(b.get("event_scope"))

        norm_pred_a = normalized(a.get("predicate"))
        norm_pred_b = normalized(b.get("predicate"))
        predicate_similarity = SequenceMatcher(None, norm_pred_a, norm_pred_b).ratio()

        semantic = False
        if bool(vectors) and norm_pred_a in vectors and norm_pred_b in vectors:
            sim = float(vectors[norm_pred_a] @ vectors[norm_pred_b])
            semantic = sim >= 0.75

        # 1. Subject-anchored match: same subject (or alias) with similar action/state, scope, or semantic predicate
        if subj_match and (predicate_similarity >= 0.60 or same_scope or semantic):
            yield a, b
            continue

        # 2. Object-anchored match: two claims acting on/describing the exact same physical object or asset
        if obj_match and (loc_match or same_scope or predicate_similarity >= 0.70 or semantic):
            yield a, b
            continue

