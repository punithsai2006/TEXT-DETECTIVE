"""LLM assessments, deterministic versioned aggregation, resumable synthesis.

No model-supplied score is accepted. Passages and graph projections share one
lineage; copying the same passage does not increase support.
"""
import json
import re
from app.config import settings
from app.models.case_analysis import (
    CaseSummary, ConstraintAssessment, HypothesisDraft, HypothesisAssessment,
    RankedHypothesis, ReportDraft, ScoreBreakdown, VerificationBatch,
)
from app.models.schemas import CaseStatus
from app.services.orchestration.evidence_review import Budget, WorkflowError, call_json, digest, now, case_lock

PROMPT_VERSION = "case-reasoning-v3.0"
SCORE_KEYS = ("support", "conflict", "temporal", "relationships", "coverage", "assumptions")


def lineage(source):
    return digest(re.sub(r"\s+", " ", source["quote"]).strip().casefold())


def score_assessment(proposal, assessment, sources, weights=None):
    """Necessary claims count once, regardless of number of duplicate passages."""
    weights = dict(settings.SCORE_WEIGHTS if weights is None else weights)
    if set(weights) != set(SCORE_KEYS) or any(not isinstance(w, (float, int)) or not -100 <= w <= 100 for w in weights.values()):
        raise ValueError("SCORE_WEIGHTS must contain exactly the six documented finite components")
    ids = [c.requirement_id for c in proposal.necessary_claims]
    if any(not set(c.source_span_ids) <= set(sources) for c in (assessment.temporal, assessment.relationships)):
        raise WorkflowError("Constraint assessment references evidence outside the case")
    assessments = {a.requirement_id: a for a in assessment.requirements}
    if len(set(ids)) != len(ids) or set(assessments) != set(ids) or len(assessment.requirements) != len(ids):
        raise WorkflowError("Necessary-claim assessments must match the proposal exactly")
    support = conflict = covered = 0
    lineage_ids = set()
    supporting, contrary = set(), set()
    assumptions = set(proposal.assumptions)
    seen_requirements = set()
    texts = {c.requirement_id: re.sub(r"\s+", " ", c.text).strip().casefold() for c in proposal.necessary_claims}
    for item in assessment.requirements:
        if texts[item.requirement_id] in seen_requirements:
            continue
        seen_requirements.add(texts[item.requirement_id])
        refs = item.supporting_source_span_ids + item.contrary_source_span_ids
        if not set(refs) <= set(sources):
            raise WorkflowError("Assessment references evidence outside the case")
        positive = {lineage(sources[s]) for s in item.supporting_source_span_ids}
        negative = {lineage(sources[s]) for s in item.contrary_source_span_ids}
        # The same lineage cannot count as both positive and negative support.
        overlap = positive & negative
        positive -= overlap
        negative -= overlap
        support += bool(positive)
        conflict += bool(negative)
        covered += bool(positive or negative)
        lineage_ids |= positive | negative
        supporting.update(s for s in item.supporting_source_span_ids if lineage(sources[s]) in positive)
        contrary.update(s for s in item.contrary_source_span_ids if lineage(sources[s]) in negative)
        assumptions.update(item.unresolved_assumptions)
    n = len(seen_requirements)
    constraint_value = {"supported": 1, "conflicting": -1, "unknown": 0}
    values = {"support": support / n, "conflict": conflict / n,
              "temporal": constraint_value[assessment.temporal.status],
              "relationships": constraint_value[assessment.relationships.status],
              "coverage": covered / n, "assumptions": min(len(assumptions), 5) / 5}
    components = {key: round(values[key] * weights[key], 6) for key in SCORE_KEYS}
    breakdown = ScoreBreakdown(**values, weights=weights, weighted_components=components,
        necessary_claim_count=n, supported_claim_count=support, conflicting_claim_count=conflict,
        distinct_lineage_count=len(lineage_ids), lineage_ids=sorted(lineage_ids))
    # Name means distinct canonical text lineages, NOT verified independent authors.
    return round(sum(components.values()), 6), breakdown, sorted(supporting), sorted(contrary), sorted(assumptions)


def choose_leader(hypotheses):
    candidates = sorted((h for h in hypotheses if not h.is_other),
                        key=lambda h: h.evidence_support_score if h.evidence_support_score is not None else -10000, reverse=True)
    if not candidates:
        return None
    top = candidates[0]
    if len(candidates) > 1 and top.evidence_support_score == candidates[1].evidence_support_score:
        return None
    score = top.score_breakdown
    if (not score or score.support < .6 or score.coverage < .6 or score.conflict > 0
            or score.temporal < 0 or score.relationships < 0 or top.assumptions):
        return None
    return top


def current_artifact(service, case_id, run):
    config = digest([PROMPT_VERSION, settings.SCORE_METHOD_VERSION, settings.SCORE_WEIGHTS,
                     run["source_fingerprint"], run["model"], run["prompt_version"]])
    # The path also contains the immutable extraction run ID, which binds its
    # provider and mock/real mode. Cross-run model caches additionally key mode.
    path = service.directory(case_id) / f"reasoning_{run['run_id']}_{config[:16]}.json"
    return path, config


def load_reasoning(service, case_id, run):
    path, _ = current_artifact(service, case_id, run)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def verify_batch(service, provider, assertions, sources, budget, actions, run_id):
    if not assertions:
        return {}
    for assertion in assertions:
        if not assertion["source_span_ids"] or not set(assertion["source_span_ids"]) <= set(sources):
            raise WorkflowError("Citation existence check failed before semantic verification")
        for s in assertion["source_span_ids"]:
            service.cite(sources[s]["case_id"], s)
    checks = {}
    for offset in range(0, len(assertions), 20):
        group = assertions[offset:offset + 20]
        result = call_json(provider, VerificationBatch,
            "Verify each assertion against ONLY its cited passages, including attribution, negation, "
            "time, scope and uncertainty. An interpretation must be explicitly qualified. Never treat "
            "a cited allegation as truth, a log as automatically reliable, or a missing record as absence. "
            "For a contradiction assessment, verify that the cited passage actually opposes the stated "
            "necessary claim. Return exactly one check for each assertion_id; no invented IDs.",
            {"assertions": [{**a, "passages": [sources[s] for s in a["source_span_ids"]]} for a in group]},
            budget, actions, "verification_reporting_agent", run_id)
        if {c.assertion_id for c in result.checks} != {a["assertion_id"] for a in group} or len(result.checks) != len(group):
            raise WorkflowError("Support verification did not cover each assertion exactly once")
        checks.update({c.assertion_id: c.supported for c in result.checks})
    return checks


def reason_case(service, case_id, run):
    with case_lock(case_id):
        if run["stale"] or run["status"] != "completed":
            raise WorkflowError("Current completed extraction/comparison is required")
        path, config = current_artifact(service, case_id, run)
        artifact = load_reasoning(service, case_id, run) or {
            "run_id": run["run_id"], "case_id": case_id, "configuration_hash": config,
            "prompt_version": PROMPT_VERSION, "score_method_version": settings.SCORE_METHOD_VERSION,
            "weights": settings.SCORE_WEIGHTS, "stages": {}, "actions": [], "status": "running", "started_at": now(),
            "is_mock": run["is_mock"], "model": run["model"], "failures": []}
        if artifact["status"] == "completed":
            return artifact
        provider = service.provider_factory()
        if provider.model_name() != run["model"] or bool(provider.is_mock) != run["is_mock"]:
            raise WorkflowError("Model configuration changed; start a new analysis run")
        sources = service.sources(case_id)
        budget = Budget(calls=30, seconds=240)
        stages, actions = artifact["stages"], artifact["actions"]
        artifact["status"] = "running"
        artifact["failures"] = []
        active_stage = None
        def checkpoint(name, schema, operation):
            nonlocal active_stage
            active_stage = name
            if name in stages:
                actions.append({"role": "hypothesis_analysis_agent", "run_id": run["run_id"], "tool": "reuse_stage_checkpoint", "stage": name, "timestamp": now()})
                return schema.model_validate(stages[name])
            result = operation()
            stages[name] = result.model_dump()
            service.store._atomic_write_json(path, artifact)
            return result
        try:
            service.store.update_case_status(case_id, CaseStatus.SCORING_HYPOTHESES, "Hypothesis generation and scoring", 75,
                                             "Generating competing interpretations and investigating necessary claims.")
            initial = service.retrieve(case_id, " ".join(c["subject"] for c in run["claims"][:8]), run["claims"], actions, run["run_id"], 10)
            proposals = checkpoint("hypotheses", HypothesisDraft, lambda: call_json(provider, HypothesisDraft,
                "Generate a SMALL set of competing case explanations using only the claims, timeline, graph and original passages. "
                "They must explain the evidence jointly, not merely restate each source as a hypothesis. Use qualified language. "
                "Identify necessary claims, supporting source references, assumptions and missing evidence. "
                "Do not invent a person/event/date or a guilt conclusion. If inadequate, return no hypotheses and explain missing evidence. "
                "The application always adds an insufficient-evidence/other-explanation alternative. No scores or probabilities.",
                {"claims": run["claims"][:80], "timeline": run.get("timeline", [])[:80], "graph": run.get("graph", {}),
                 "comparisons": run["comparisons"][:40], "passages": initial,
                 "context_limit": "At most 80 claims and 40 comparisons are shown; investigate missing context via retrieval."},
                budget, actions, "hypothesis_analysis_agent", run["run_id"]))
            ids = [p.hypothesis_id for p in proposals.hypotheses]
            if len(ids) != len(set(ids)):
                raise WorkflowError("Duplicate hypothesis IDs")
            ranked = []
            claim_ids = {c["claim_id"] for c in run["claims"]}
            for proposal in proposals.hypotheses:
                if not set(proposal.source_span_ids) <= set(sources) or not set(proposal.relevant_claim_ids) <= claim_ids:
                    raise WorkflowError("Hypothesis references an unavailable claim/source")
                # This is an actual case-scoped tool call, not a renamed fixed model prompt.
                context = service.retrieve(case_id, proposal.description, run["claims"], actions, run["run_id"], 8)
                permitted = {s["span_id"] for s in context} | set(proposal.source_span_ids)
                available = {s: sources[s] for s in permitted}
                assessment = checkpoint("assessment_" + proposal.hypothesis_id, HypothesisAssessment, lambda: call_json(
                    provider, HypothesisAssessment,
                    "Investigate each necessary claim of the proposed explanation against the supplied evidence. "
                    "Return support and contrary source IDs separately. Assess temporal feasibility and relationship/access "
                    "constraints, using unknown if the sources do not establish them. A log is a source claim, not privileged truth. "
                    "Absence of a record is not proof of absence without known completeness. Record approximations, clock uncertainty, "
                    "missing evidence and assumptions explicitly. Do not supply a final numerical score.",
                    {"hypothesis": proposal.model_dump(), "passages": list(available.values()),
                     "claims": [c for c in run["claims"] if c["claim_id"] in proposal.relevant_claim_ids],
                     "timeline": run.get("timeline", []), "graph": run.get("graph", {}), "comparisons": run["comparisons"]},
                    budget, actions, "hypothesis_analysis_agent", run["run_id"]))
                expected_requirements = {r.requirement_id for r in proposal.necessary_claims}
                if {r.requirement_id for r in assessment.requirements} != expected_requirements or len(assessment.requirements) != len(expected_requirements):
                    raise WorkflowError("Assessment omitted or duplicated necessary claims; retry this stage")
                requirement_text = {r.requirement_id: r.text for r in proposal.necessary_claims}
                assertions = [{"assertion_id": "description", "text": "Proposed interpretation: " + proposal.description,
                               "source_span_ids": proposal.source_span_ids, "kind": "interpretation"}]
                for item in assessment.requirements:
                    if item.requirement_id not in requirement_text:
                        raise WorkflowError("Unknown necessary claim in assessment")
                    for kind, refs in [("support", item.supporting_source_span_ids), ("contrary", item.contrary_source_span_ids)]:
                        if refs:
                            assertions.append({"assertion_id": item.requirement_id + "_" + kind,
                                "text": ("These sources support the necessary claim: " if kind == "support" else "These sources conflict with the necessary claim: ") + requirement_text[item.requirement_id],
                                "source_span_ids": refs, "kind": "interpretation"})
                    combined_refs = list(dict.fromkeys(item.supporting_source_span_ids + item.contrary_source_span_ids))
                    if combined_refs:
                        assertions.append({"assertion_id": item.requirement_id + "_explanation", "text": item.explanation,
                                           "source_span_ids": combined_refs, "kind": "interpretation"})
                for name in ("temporal", "relationships"):
                    constraint = getattr(assessment, name)
                    if constraint.source_span_ids:
                        assertions.append({"assertion_id": name, "text": constraint.explanation,
                                           "source_span_ids": constraint.source_span_ids, "kind": "interpretation"})
                if not set(s for a in assertions for s in a["source_span_ids"]) <= permitted:
                    raise WorkflowError("Assessment used evidence not supplied to its context")
                verification_key = "verified_" + proposal.hypothesis_id
                active_stage = verification_key
                if verification_key not in stages:
                    stages[verification_key] = verify_batch(service, provider, assertions, sources, budget, actions, run["run_id"])
                    service.store._atomic_write_json(path, artifact)
                verified = stages[verification_key]
                if not verified.get("description"):
                    continue
                clean = assessment.model_copy(deep=True)
                for item in clean.requirements:
                    if not verified.get(item.requirement_id + "_support"):
                        item.supporting_source_span_ids = []
                    if not verified.get(item.requirement_id + "_contrary"):
                        item.contrary_source_span_ids = []
                    if not verified.get(item.requirement_id + "_explanation"):
                        item.explanation = "The detailed model explanation was withheld; review the source assessments and unresolved assumptions."
                for name in ("temporal", "relationships"):
                    if not verified.get(name):
                        setattr(clean, name, ConstraintAssessment(status="unknown", explanation="Not established by verified evidence", source_span_ids=[]))
                score, breakdown, positive, negative, assumptions = score_assessment(proposal, clean, sources)
                ranked.append(RankedHypothesis(hypothesis_id=proposal.hypothesis_id, title=proposal.title, description=proposal.description,
                    description_source_span_ids=proposal.source_span_ids,
                    evidence_support_score=score, score_method_version=settings.SCORE_METHOD_VERSION, score_breakdown=breakdown,
                    supporting_source_span_ids=positive, contrary_source_span_ids=negative, assumptions=assumptions,
                    missing_evidence=proposal.missing_evidence + clean.additional_missing_evidence,
                    relevant_claim_ids=proposal.relevant_claim_ids,
                    relevant_event_ids=["event_" + c for c in proposal.relevant_claim_ids], relevant_graph_node_ids=proposal.relevant_claim_ids,
                    necessary_claims=proposal.necessary_claims, requirement_assessments=clean.requirements,
                    limitations=[{"code": "model_assessment", "text": "Support judgments are model assessments requiring human review."}]))
            ranked.sort(key=lambda h: (-(h.evidence_support_score or 0), h.hypothesis_id))
            ranked.append(RankedHypothesis(hypothesis_id="other_insufficient", title="Insufficient evidence / other explanation",
                description="The available sources may be incomplete, mistaken or consistent with explanations not captured here.",
                evidence_support_score=None, score_method_version=settings.SCORE_METHOD_VERSION, score_breakdown=None,
                supporting_source_span_ids=[], contrary_source_span_ids=[], assumptions=[],
                missing_evidence=proposals.unanswered_questions, relevant_claim_ids=[], relevant_event_ids=[], relevant_graph_node_ids=[],
                limitations=[{"code": "open_world", "text": "The generated alternatives are not exhaustive."}], is_other=True))
            artifact["hypotheses"] = [h.model_dump() for h in ranked]
            leader = choose_leader(ranked)
            artifact["leading_hypothesis_id"] = leader.hypothesis_id if leader else None
            service.store._atomic_write_json(path, artifact)
            service.store.update_case_status(case_id, CaseStatus.GENERATING_REPORT, "Evidence verification and report generation", 90,
                                             "Synthesizing and verifying a cited report from persisted findings and fixed scores.")
            report_sources = set(s for h in ranked for s in h.supporting_source_span_ids + h.contrary_source_span_ids)
            report_sources |= {s["span_id"] for s in initial}
            draft = checkpoint("report_draft", ReportDraft, lambda: call_json(provider, ReportDraft,
                "Write the investigation report narrative from this persisted analysis ONLY. Executive summary and every "
                "case-specific assertion need citations. Distinguish source statements, qualified interpretations and unknowns. "
                "Explain alternatives, contradictory accounts and missing evidence; never assert guilt, lying or actual truth. "
                "Do not change or invent scores/findings. Do not describe mutable human review status; it is rendered separately. "
                "Never declare a leading explanation when leading_hypothesis_id is null.",
                {"case_name": service.store.get_case(case_id).name, "analysis_run_id": run["run_id"],
                 "hypotheses": artifact["hypotheses"], "leading_hypothesis_id": artifact["leading_hypothesis_id"],
                 "comparisons": run["comparisons"], "timeline": run.get("timeline", []), "graph": run.get("graph", {}),
                 "passages": [sources[s] for s in sorted(report_sources)]},
                budget, actions, "verification_reporting_agent", run["run_id"]))
            all_assertions = list(draft.executive_summary) + [a for section in draft.sections for a in section.assertions]
            assertions = [{"assertion_id": f"report_{i}", **a.model_dump()} for i, a in enumerate(all_assertions)]
            if not set(s for a in assertions for s in a["source_span_ids"]) <= report_sources:
                raise WorkflowError("Report cited evidence outside its supplied context")
            if "report_verification" not in stages:
                active_stage = "report_verification"
                stages["report_verification"] = verify_batch(service, provider, assertions, sources, budget, actions, run["run_id"])
                service.store._atomic_write_json(path, artifact)
            rejected = [a for a in assertions if not stages["report_verification"].get(a["assertion_id"])]
            if rejected:
                # Never silently publish a different narrative after verification failed.
                stages.pop("report_draft", None)
                stages.pop("report_verification", None)
                raise WorkflowError(f"Report support verification rejected {len(rejected)} assertion(s); retry report synthesis")
            artifact["report"] = draft.model_dump()
            artifact["status"] = "completed"
            artifact["finished_at"] = now()
        except Exception as exc:
            if active_stage and isinstance(exc, WorkflowError):
                stages.pop(active_stage, None)
                if active_stage.startswith("assessment_"):
                    stages.pop("verified_" + active_stage.removeprefix("assessment_"), None)
            artifact["status"] = "failed"
            actions.append({"role": "verification_reporting_agent", "run_id": run["run_id"], "tool": "stage_failure",
                            "stage": active_stage, "status": "failed", "error_type": type(exc).__name__, "timestamp": now()})
            artifact["failures"] = [str(exc) if isinstance(exc, (WorkflowError, ValueError)) else type(exc).__name__]
            raise
        finally:
            artifact["model_calls"] = artifact.get("model_calls", 0) + budget.calls
            artifact["usage"] = artifact.get("usage", []) + budget.usage
            artifact["cost"] = None
            service.store._atomic_write_json(path, artifact)
        return artifact


def build_summary(service, case_id, run, artifact):
    ranked = [RankedHypothesis(**h) for h in artifact["hypotheses"]]
    leader = next((h for h in ranked if h.hypothesis_id == artifact["leading_hypothesis_id"]), None)
    report = ReportDraft(**artifact["report"])
    disparities = [{"contradiction_id": f["id"], "classification": f["outcome"], "description": f["explanation"],
                    "claim_ids": [f["claim_a_id"], f["claim_b_id"]], "source_span_ids": list(dict.fromkeys(f["source_a_ids"] + f["source_b_ids"])),
                    "unresolved_assumptions": f["assumptions"] + f["ambiguities"], "review_status": f["review_status"]} for f in run["comparisons"]]
    return CaseSummary(case_id=case_id, case_name=service.store.get_case(case_id).name,
        analysis_run_id=run["run_id"], document_count=len(run["document_versions"]),
        analysis_status="outdated" if run["stale"] else artifact["status"],
        summary={"text": "\n\n".join(a.text for a in report.executive_summary),
                 "source_span_ids": sorted({s for a in report.executive_summary for s in a.source_span_ids})},
        leading_hypothesis=leader, alternative_hypotheses=[h for h in ranked if not leader or h.hypothesis_id != leader.hypothesis_id],
        detected_contradictions=[d for d in disparities if d["classification"] == "POTENTIAL_CONTRADICTION"],
        minor_discrepancies=[d for d in disparities if d["classification"] != "POTENTIAL_CONTRADICTION"],
        timeline=[{"event_id": "event_" + c["claim_id"], "time_start": c["event_start"], "time_end": c["event_end"],
                   "timezone": c["timezone"], "time_precision": c["precision"],
                   "description": f"{c['subject']} / {c['predicate']} / {c['object']} (polarity: {c['polarity']})",
                   "attribution": c["speaker"] or c.get("originating_source") or "Originating source", "event_basis": c.get("event_basis", "reported"),
                   "source_span_ids": c["source_span_ids"]} for c in run["claims"]],
        unanswered_questions=report.unanswered_questions,
        limitations=[{"code": "report_limit", "text": t} for t in report.limitations] + [
            {"code": "score_not_probability", "text": "Evidence-support score — not a probability of guilt."},
            {"code": "human_review", "text": "Model assessments and source claims require human review."}])
