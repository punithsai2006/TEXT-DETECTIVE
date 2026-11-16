"""Publish evidence-grounded analysis through the application's existing contracts."""
from app.models.evidence_review import ReviewRequest
from app.models.schemas import (
    AnalysisRunRecord, AskQuestionResponse, CaseGraph, CaseGraphEdge, CaseGraphNode,
    CaseStatus, ContradictionItem, Entity, Event, EvidenceItem, Hypothesis,
    InvestigationReport, ReviewStatus, SupportingEvidenceCard, TimelineEntry,
)
from app.services.hypothesis.evidence_reasoning import reason_case, load_reasoning, build_summary
from app.services.orchestration.evidence_review import EXTRACTION_PROMPT_VERSION
from datetime import datetime, timezone
from app.config import settings
from app.services.extraction.source_graph import build_source_graph


def timeline_order(claim):
    value = claim.get("event_start")
    if value:
        try:
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo is None and claim.get("timezone") == "UTC":
                parsed = parsed.replace(tzinfo=timezone.utc)
            if parsed.tzinfo is not None and not claim.get("approximate"):
                return (0, parsed.astimezone(timezone.utc).isoformat())
        except ValueError:
            pass
    return (1, "")  # Stable input order; no invented dates or order for uncertain events.


def publish(service, case_id, run, score=True):
    """One canonical projection shared by existing pages, reviews and exports."""
    store = service.store
    docs = {d.document_id: d for d in service.documents(case_id)}
    sources = service.sources(case_id)
    case = store.get_case(case_id)
    entities, events, timeline, comparisons = [], [], [], []
    for node in run.get("graph", {}).get("nodes", []):
        if node["type"] == "source_entity_mention":
            typed = next((e for e in run.get("entities", []) if e["name"] == node["label"]
                          and any(sources[s]["document_id"] == node["document_id"] for s in e["source_span_ids"])), None)
            kind = typed["entity_type"] if typed else "unknown"
            kind = {"place": "location", "unknown": "object"}.get(kind, kind)
            entities.append(Entity(entity_id=node["id"], name=node["label"], entity_type=kind,
                                   document_ids=[node["document_id"]], metadata={"identity": "document-scoped mention; type unresolved"}))
    for c in sorted(run["claims"], key=timeline_order):
        source = sources[c["source_span_ids"][0]]
        doc = docs[source["document_id"]]
        description = f"{c['speaker'] or doc.filename} reports: {c['subject']} / {c['predicate']} / {c['object']} (polarity: {c['polarity']}; {c['attribution']})"
        event = Event(event_id="event_" + c["claim_id"], description=description, participants=[c["subject"]],
                      location=c["location"], time_str=c["event_start"], parsed_timestamp=c["event_start"],
                      document_id=doc.document_id, document_name=doc.filename, chunk_id=source["span_id"],
                      source_sentence=source["quote"], char_start=source["char_start"], char_end=source["char_end"],
                      timezone=c["timezone"], precision=c["precision"], uncertainty=bool(c["uncertainty"] or c["approximate"] or not c["event_start"]),
                      confidence=0, raw_timestamp_text=c["event_start"])
        events.append(event)
        timeline.append(TimelineEntry(entry_id=event.event_id, event_id=event.event_id,
                        timestamp_display=f"{c['event_start'] or 'Unknown event time'} ({c['timezone'] or 'timezone unknown'}; {c['precision']})",
                        event_description=description, participants=[c["subject"]], location=c["location"],
                        document_name=doc.filename, document_type=doc.document_type, document_id=doc.document_id,
                        chunk_id=source["span_id"], char_start=source["char_start"], char_end=source["char_end"],
                        source_sentence=source["quote"], is_uncertain=event.uncertainty, precision=c["precision"],
                        timezone=c["timezone"], confidence=0, sort_key=(c["timezone"] or "unknown") + (c["event_start"] or "unknown")))
        timeline[-1].record_time = c["record_time"]
        timeline[-1].event_end = c["event_end"]
        timeline[-1].event_basis = c.get("event_basis", "reported")
        timeline[-1].source_span_ids = c["source_span_ids"]
        timeline[-1].ordering_group = "comparable UTC timestamps" if timeline_order(c)[0] == 0 else "uncertain/unordered"
    claims = {c["claim_id"]: c for c in run["claims"]}
    review_map = {"accept_lead": "confirmed", "reject": "rejected", "explainable_variance": "rejected",
                  "request_context": "needs_further_investigation", "pending_review": "pending_review"}
    for f in run["comparisons"]:
        a, b = sources[f["source_a_ids"][0]], sources[f["source_b_ids"][0]]
        conflict = f["outcome"] == "POTENTIAL_CONTRADICTION"
        compatible = f["outcome"] == "COMPATIBLE"
        history = [e for e in run.get("review_history", []) if e["target_id"] == f["id"]]
        last = history[-1] if history else {}
        comparisons.append(ContradictionItem(
            id=f["id"], case_id=case_id, statement_a=a["quote"], statement_b=b["quote"],
            doc_a_id=a["document_id"], doc_b_id=b["document_id"], doc_a_name=a["filename"], doc_b_name=b["filename"],
            chunk_a_id=a["span_id"], chunk_b_id=b["span_id"],
            entity_event_link=claims[f["claim_a_id"]]["subject"],
            contradiction_type="possible_contradiction" if conflict else "agreement" if compatible else "neutral",
            nli_label="contradiction" if conflict else "entailment" if compatible else "neutral",
            confidence=0, explanation=f["explanation"], detection_engine="contextual_comparison",
            calculation_source=run["model"], outcome=f["outcome"], assumptions=f["assumptions"],
            ambiguities=f["ambiguities"], stale=run["stale"], run_id=run["run_id"],
            review_status=review_map[f["review_status"]], review_action=f["review_status"],
            reviewer_id=last.get("reviewer"), review_notes=last.get("notes"), review_timestamp=last.get("timestamp"),
            source_sentences=[a["quote"], b["quote"]]))
    graph = build_source_graph(run, sources, docs)
    entities = [Entity(entity_id=n.id, name=n.label, entity_type=n.sub_type or "object",
                document_ids=sorted({sources[s]["document_id"] for s in n.properties.get("source_span_ids", [])}),
                source_sentences=[sources[s]["quote"] for s in n.properties.get("source_span_ids", [])],
                metadata={"identity": n.properties.get("identity", "source mention, not independently established identity")})
                for n in graph.nodes if n.node_type == "entity"]
    # Graph claim nodes use claim IDs; timeline events use event_<claim ID>.
    store.save_extraction(case_id, entities, events, timeline, graph)
    store.save_contradictions(case_id, comparisons)
    store.save_summary_timeline(case_id, [])
    store.save_ground_truth_timeline(case_id, [[t.timestamp_display, t.event_description] for t in timeline])
    evidence = [EvidenceItem(evidence_id="evid_" + s["span_id"], case_id=case_id, document_id=s["document_id"],
                document_name=s["filename"], document_type=docs[s["document_id"]].document_type,
                chunk_id=s["span_id"], text=s["quote"], page_number=s["page_number"],
                paragraph=s["paragraph"],
                char_start=s["char_start"], char_end=s["char_end"], score=0, retrieval_method="source_span")
                for s in sources.values()]
    service._index(case_id, list(docs.values()))
    reasoning_run = {**run, "graph": graph.model_dump()}
    artifact = reason_case(service, case_id, reasoning_run) if score else load_reasoning(service, case_id, run)
    if not artifact or artifact["status"] != "completed":
        raise ValueError("Hypothesis/report synthesis is incomplete; retry analysis to resume completed checkpoints")
    summary = build_summary(service, case_id, run, artifact)
    hypotheses = [Hypothesis(hypothesis_id=h["hypothesis_id"], case_id=case_id, title=h["title"], description=h["description"],
        origin="generated", total_score=round(h["evidence_support_score"] or 0), rank=i + 1,
        evidence_support_score=h["evidence_support_score"], score_method_version=h["score_method_version"],
        description_source_span_ids=h["description_source_span_ids"],
        score_breakdown=h["score_breakdown"] or {}, supporting_source_span_ids=h["supporting_source_span_ids"],
        contrary_source_span_ids=h["contrary_source_span_ids"], assumptions=h["assumptions"], missing_evidence=h["missing_evidence"],
        relevant_claim_ids=h["relevant_claim_ids"], relevant_event_ids=h["relevant_event_ids"], relevant_graph_node_ids=h["relevant_graph_node_ids"],
        is_other=h["is_other"], is_proposed_explanation=h["hypothesis_id"] == artifact["leading_hypothesis_id"],
        necessary_claims=h["necessary_claims"], requirement_assessments=h["requirement_assessments"],
        uncertainty_warning="Evidence-support score — not a probability of guilt.") for i, h in enumerate(artifact["hypotheses"])]
    store.save_hypotheses(case_id, hypotheses)
    from app.services.agents.evidence_orchestrator import LeadInvestigatorAgent
    deliberation = LeadInvestigatorAgent().run(service, case_id, run, graph.model_dump(), timeline, artifact)
    if deliberation.processing_status != "completed":
        raise ValueError("Five-agent deliberation incomplete: " + "; ".join(deliberation.warnings))
    store.update_case_status(case_id, CaseStatus.GENERATING_REPORT, "Module 6: Audit Dossier Generation", 95,
                             "Generating the existing dossier with exact citations, review history and uncertainty.")
    report = InvestigationReport(report_id="rep_" + run["run_id"], case_id=case_id, case_name=case.name,
        case_overview=case.description or "Evidence-grounded review of attributed source accounts.",
        documents_analyzed=[{"document_id": d.document_id, "filename": d.filename,
                             "document_type": d.document_type.value, "speaker": d.speaker, "timestamp": d.timestamp,
                             "chunk_count": len(d.source_spans), "file_size_bytes": d.file_size_bytes} for d in docs.values()],
        investigation_summary=summary.summary.text or "The supplied evidence does not support a substantive summary.",
        extracted_entities=entities, important_events=events, chronological_timeline=timeline,
        key_evidence=evidence, agreements=[c for c in comparisons if c.outcome == "COMPATIBLE"],
        contradictions=comparisons, candidate_hypotheses=hypotheses,
        proposed_explanation=next((h for h in hypotheses if h.is_proposed_explanation), None),
        score_breakdown=[{"hypothesis_id": h.hypothesis_id, "title": h.title, "rank": h.rank,
                          "total": h.evidence_support_score, "components": h.score_breakdown} for h in hypotheses],
        unresolved_questions=list(dict.fromkeys([ambiguity for f in run["comparisons"] for ambiguity in f["ambiguities"]] + summary.unanswered_questions)),
        limitations_and_uncertainty="Source claims and accepted leads do not establish actual events. Hypothesis scores are uncalibrated heuristics. "
                                    + ("This analysis is stale; rerun before using it." if run["stale"] else "Inspect original passages.")
                                    + "\n" + "\n".join(item.text for item in summary.limitations),
        source_references=[{"document_id": s["document_id"], "filename": s["filename"], "chunk_id": s["span_id"],
                            "document": s["filename"], "excerpt": s["quote"], "sentence_indices": [],
                            "char_start": s["char_start"], "char_end": s["char_end"], "extraction_version": s["extraction_version"],
                            "page_number": s["page_number"], "paragraph": s["paragraph"], "quote": s["quote"]}
                           for s in sources.values()], analysis_run_id=run["run_id"], case_summary=summary,
        llm_narrative=artifact["report"], graph_snapshot=graph, agent_deliberations=deliberation,
        is_mock=run["is_mock"], model_name=run["model"])
    store.save_report(case_id, report)
    if not store.get_run_record(case_id, run["run_id"]):
        store.save_run_record(case_id, AnalysisRunRecord(run_id=run["run_id"], case_id=case_id, timestamp=run["started_at"],
            parser_version=run["parser_version"], model_provider=run["model_provider"], model_name=run["model"],
            prompt_version=run["prompt_version"], retrieval_settings={**run.get("retrieval_settings", {}), "reasoning_prompt_version": artifact["prompt_version"]},
            document_hashes=run["document_hashes"], scoring_config={"method_version": artifact["score_method_version"], "weights": artifact["weights"]},
            metrics_summary={"is_mock": run["is_mock"], "extraction_comparison_calls": run["model_calls"], "reasoning_calls": artifact["model_calls"]}))
    store.update_case_status(case_id, CaseStatus.OUTDATED if run["stale"] else CaseStatus.COMPLETED,
                             "Complete", 100, "Pipeline completed; findings require human review.")
    return report


def run_pipeline(service, case_id):
    previous = service.load(case_id)
    provider = service.provider_factory()
    if (previous and not previous["stale"] and previous["status"] == "completed"
            and previous["model_provider"] == type(provider).__name__
            and previous["model"] == provider.model_name() and previous["is_mock"] == bool(provider.is_mock)
            and previous["prompt_version"] == EXTRACTION_PROMPT_VERSION):
        if previous.get("scoring_configuration") != {"version": settings.SCORE_METHOD_VERSION, "weights": settings.SCORE_WEIGHTS}:
            previous = None
    if (previous and not previous["stale"] and previous["status"] == "completed"
            and previous["model_provider"] == type(provider).__name__
            and previous["model"] == provider.model_name() and previous["is_mock"] == bool(provider.is_mock)
            and previous["prompt_version"] == EXTRACTION_PROMPT_VERSION):
        run = previous
    else:
        run = service.run(case_id)
        # Resumable candidate batching: iterate remaining comparison batches
        max_batches = 25
        batch_num = 0
        while run["status"] == "partial" and run.get("pending_comparisons", 0) > 0 and batch_num < max_batches:
            batch_num += 1
            prev_comparisons = len(run.get("comparisons", []))
            run = service.run(case_id, allow_fixture=run.get("is_mock", False))
            if len(run.get("comparisons", [])) <= prev_comparisons:
                break

    # If partial due solely to pending candidate comparisons (e.g. bounded budget), allow publication with warnings
    is_partial_comparison = run["status"] == "partial" and all("Partial analysis" in f for f in run.get("failures", []))
    if run["stale"] or (run["status"] not in ("completed", "partial") or (run["status"] == "partial" and not is_partial_comparison)):
        message = "; ".join(run["failures"]) or "Analysis is incomplete or stale"
        service.store.update_case_status(case_id, CaseStatus.FAILED, "Evidence analysis blocked", 15, message, error=message)
        raise ValueError(message)
    return publish(service, case_id, run)


def answer_existing(service, case_id, question, top_k):
    result = service.answer(case_id, question, top_k)
    ids = list(dict.fromkeys(s for a in result["assertions"] for s in a["source_span_ids"]))
    sources = service.sources(case_id)
    docs = {d.document_id: d for d in service.documents(case_id)}
    evidence = [EvidenceItem(evidence_id="answer_" + s, case_id=case_id, document_id=sources[s]["document_id"],
                document_name=sources[s]["filename"], document_type=docs[sources[s]["document_id"]].document_type,
                chunk_id=s, text=sources[s]["quote"], page_number=sources[s]["page_number"], score=0,
                paragraph=sources[s]["paragraph"],
                retrieval_method="verified_case_rag") for s in ids]
    text = "\n\n".join(a["text"] for a in result["assertions"]) or "Insufficient evidence to answer this question."
    return AskQuestionResponse(question=question, answer=text, direct_answer=text,
        evidence_sufficiency="source_supported_unreviewed" if result["assertions"] else "insufficient_evidence",
        evidence=evidence, supporting_evidence=[SupportingEvidenceCard(source=e.document_name, quote=e.text) for e in evidence],
        unresolved_questions=result["unknowns"], important_limitations=result["limitation"],
        sources=[{"source_num": i + 1, "document_id": e.document_id, "filename": e.document_name, "chunk_id": e.chunk_id}
                 for i, e in enumerate(evidence)], model_used=result["model"], is_mock=result["is_mock"])
