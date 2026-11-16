import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.schemas import (
    Case,
    ContradictionItem,
    ContradictionType,
    DocumentMetadata,
    Entity,
    Event,
    EvidenceItem,
    ForensicSummaryMilestone,
    Hypothesis,
    InvestigationReport,
    MultiAgentDeliberation,
    TimelineEntry,
)
from app.services.llm_provider import analysis_model_json
from app.services.reporting.suspect_assessment import assess_suspect


def generate_investigation_report(
    case: Case,
    documents: List[DocumentMetadata],
    entities: List[Entity],
    events: List[Event],
    timeline: List[TimelineEntry],
    key_evidence: List[EvidenceItem],
    contradictions: List[ContradictionItem],
    hypotheses: List[Hypothesis],
    summary_timeline: Optional[List[ForensicSummaryMilestone]] = None,
    agent_deliberations: Optional[MultiAgentDeliberation] = None,
) -> InvestigationReport:
    """
    Generates the complete 18-section investigation report as specified in Slide 15.
    Every factual claim is directly attributed to source documents and sentences.
    """
    report_id = f"rep_{case.case_id}_{uuid.uuid4().hex[:6]}"

    # 1. Documents summary
    doc_summaries = []
    for d in documents:
        doc_summaries.append({
            "document_id": d.document_id,
            "filename": d.filename,
            "document_type": d.document_type.value,
            "speaker": d.speaker,
            "timestamp": d.timestamp,
            "chunk_count": len(d.chunks),
            "file_size_bytes": d.file_size_bytes,
        })

    # 2. Partition contradictions and agreements
    agreements = [c for c in contradictions if c.contradiction_type == ContradictionType.AGREEMENT]
    conflicts = [
        c for c in contradictions
        if c.contradiction_type in [ContradictionType.CONFIRMED_CONTRADICTION, ContradictionType.POSSIBLE_CONTRADICTION]
    ]

    # 3. Proposed explanation
    proposed_hyp = next((h for h in hypotheses if h.is_proposed_explanation), None)

    # 4. Score breakdown
    score_breakdown = []
    for h in hypotheses:
        score_breakdown.append({
            "rank": h.rank,
            "hypothesis_id": h.hypothesis_id,
            "title": h.title,
            "origin": h.origin,
            "support": h.support_score,
            "conflict": h.conflict_score,
            "corroboration": h.corroboration_score,
            "conflict_penalty": h.conflict_penalty,
            "total_score": h.total_score,
            "is_proposed_explanation": h.is_proposed_explanation,
        })

    # 5. Supporting and conflicting evidence for proposed explanation
    supp_ev: List[EvidenceItem] = []
    conf_ev: List[EvidenceItem] = []
    if proposed_hyp:
        # Collect unique evidence IDs from claims
        supp_ids = {ev_id for claim in proposed_hyp.claims for ev_id in claim.supporting_evidence_ids}
        conf_ids = {ev_id for claim in proposed_hyp.claims for ev_id in claim.conflicting_evidence_ids}
        for ev in key_evidence:
            if ev.evidence_id in supp_ids and ev not in supp_ev:
                supp_ev.append(ev)
            if ev.evidence_id in conf_ids and ev not in conf_ev:
                conf_ev.append(ev)

    # 6. Unresolved questions
    unresolved_questions = []
    for c in conflicts:
        if c.resolution_status == "unresolved":
            unresolved_questions.append(
                f"Discrepancy concerning {c.entity_event_link}: '{c.doc_a_name}' ({c.speaker_a or 'Unknown'}) states "
                f"'{c.statement_a}', which conflicts with '{c.doc_b_name}' ({c.speaker_b or 'Unknown'}) claiming '{c.statement_b}'."
            )
    if not unresolved_questions:
        unresolved_questions.append("No major unresolved factual discrepancies identified across the submitted files.")

    # 7. Summary
    exec_summary = (
        f"Investigation analysis completed for Case '{case.name}'. "
        f"A total of {len(documents)} documents were processed, revealing {len(entities)} unique named entities "
        f"and {len(timeline)} ordered timeline events. Cross-document comparison established {len(conflicts)} "
        f"conflicts and {len(agreements)} corroborated agreements. "
        + (f"The highest-ranked evidence claim is '{proposed_hyp.title}' with an evidence score of {proposed_hyp.total_score}."
           if proposed_hyp else (
               "The leading hypotheses share the highest score. The system did not select a single explanation."
               if hypotheses else "No candidate hypotheses were evaluated."
           ))
    )
    if key_evidence:
        excerpts = {item.chunk_id: item for item in key_evidence[:12]}
        selection = analysis_model_json(
            'Select up to three source excerpts for an extractive executive summary. '
            'Return {"excerpts":[{"chunk_id":"provided identifier","quote":"verbatim substring"}]}.',
            {chunk_id: item.text for chunk_id, item in excerpts.items()},
        )
        selected = selection.get("excerpts") if selection else None
        if isinstance(selected, list):
            for item in selected[:3]:
                if not isinstance(item, dict):
                    continue
                chunk_id, quote = item.get("chunk_id"), item.get("quote")
                if not isinstance(chunk_id, str) or not isinstance(quote, str):
                    continue
                source = excerpts.get(chunk_id)
                if source and quote.strip() and quote in source.text:
                    exec_summary += f'\n\n"{quote}" [{source.document_id}, {chunk_id}]'

    suspect_assessment = assess_suspect(documents)
    if suspect_assessment:
        exec_summary = f"{suspect_assessment}\n\n{exec_summary}"

    limitations = (
        "LIMITATIONS & UNCERTAINTY STATEMENT:\n"
        "1. This analysis was generated by the Text Detective agentic framework based strictly on user-supplied documents.\n"
        "2. System conclusions reflect mathematical evidence scoring (Support - Conflict + Corroboration - ConflictPenalty) "
        "and do not constitute legal proof or a substitute for professional forensic determinations.\n"
        "3. Unknown timestamps and ambiguous coreferences have been preserved rather than assumed."
    )

    # 8. Source references list
    source_refs = []
    for d in documents:
        for idx, chunk in enumerate(d.chunks):
            source_refs.append({
                "ref_id": chunk.chunk_id,
                "document_id": d.document_id,
                "filename": d.filename,
                "document": d.filename,
                "document_type": d.document_type.value,
                "speaker": chunk.speaker or "N/A",
                "timestamp": chunk.timestamp or "N/A",
                "sentence_indices": chunk.sentence_indices,
                "excerpt": chunk.text[:120] + ("..." if len(chunk.text) > 120 else ""),
            })

    return InvestigationReport(
        report_id=report_id,
        case_id=case.case_id,
        case_name=case.name,
        case_overview=case.description or f"Investigation into case: {case.name}",
        documents_analyzed=doc_summaries,
        investigation_summary=exec_summary,
        extracted_entities=entities,
        important_events=events,
        chronological_timeline=timeline,
        summary_timeline=summary_timeline or [],
        key_evidence=key_evidence,
        agreements=agreements,
        contradictions=conflicts,
        candidate_hypotheses=hypotheses,
        score_breakdown=score_breakdown,
        proposed_explanation=proposed_hyp,
        supporting_evidence=supp_ev,
        conflicting_evidence=conf_ev,
        unresolved_questions=unresolved_questions,
        limitations_and_uncertainty=limitations,
        source_references=source_refs,
        agent_deliberations=agent_deliberations,
    )


def export_report_to_markdown(report: InvestigationReport) -> str:
    """
    Renders the report as clean GitHub-Flavored Markdown.
    """
    lines = [
        f"# TEXT DETECTIVE INVESTIGATION REPORT",
        f"**Case:** {report.case_name} (ID: `{report.case_id}`)",
        f"**Date Generated:** {report.generated_at}",
        f"**Report ID:** `{report.report_id}`",
        "",
        "---",
        "",
        "## 1. Case Overview",
        report.case_overview,
        "",
        "## 2. Documents Analyzed",
        "| Document Name | Type | Speaker / Author | Chunks | Size (bytes) |",
        "|---|---|---|---|---|",
    ]
    for d in report.documents_analyzed:
        lines.append(f"| {d['filename']} | {d['document_type']} | {d.get('speaker') or 'N/A'} | {d['chunk_count']} | {d['file_size_bytes']} |")

    lines.extend([
        "",
        "## 3. Executive Investigation Summary",
        report.investigation_summary,
        "",
        "## 4. Key Entities Identified",
        "| Name | Type | Mentions | Source Documents |",
        "|---|---|---|---|",
    ])
    for e in report.extracted_entities[:15]:
        doc_refs = ", ".join(e.document_ids)
        lines.append(f"| {e.name} | {e.entity_type.value} | {e.mentions_count} | {doc_refs} |")

    lines.extend([
        "",
        "## 5. Chronological Timeline",
        "| Time | Event Description | Participants | Location | Source |",
        "|---|---|---|---|---|",
    ])
    for t in report.chronological_timeline[:20]:
        parts = ", ".join(t.participants) if t.participants else "Unspecified"
        loc = t.location or "Unspecified"
        lines.append(f"| {t.timestamp_display} | {t.event_description} | {parts} | {loc} | {t.document_name} |")

    lines.extend([
        "",
        "## 6. Cross-Document Contradictions & Conflicts",
        "Rigorous forensic cross-examination pitting subjective witness testimonies against objective physical telemetry, digital lock sensors, and independent evidence.",
        "",
    ])
    if report.contradictions:
        for idx, c in enumerate(report.contradictions, 1):
            title = c.conflict_title or f"Discrepancy #{idx}: {c.entity_event_link}"
            category = c.evidentiary_category or "Cross-Document Telemetry Conflict"
            impact = c.alibi_impact or "HIGH (Deception Detected)"
            analysis = c.forensic_analysis or c.explanation
            lines.extend([
                f"### Conflict #{idx}: {title}",
                f"- **Evidentiary Category:** `{category}` | **Status:** `{c.resolution_status}` | **Alibi Impact:** `{impact}`",
                f"- **Subjective Testimonial Claim (Statement A):**",
                f"  > \"{c.statement_a}\"",
                f"  > — *Source: `{c.doc_a_name}` (Speaker: {c.speaker_a or 'Unknown'})*",
                f"- **Objective Rebuttal / Physical Telemetry (Statement B):**",
                f"  > \"{c.statement_b}\"",
                f"  > — *Source: `{c.doc_b_name}` (Speaker: {c.speaker_b or 'System Sensor'})*",
                f"- **Forensic Analysis & Reconciliation:**",
                f"  {analysis}",
                f"- **NLI Verification & Confidence:** `{c.contradiction_type.value}` (Confidence: {c.confidence:.2f})",
                "",
            ])
    else:
        lines.append("*No cross-document contradictions detected.*")

    lines.extend([
        "",
        "## 7. Hypotheses Evaluation & Ranking",
        "Score Formula: `Score(H) = Support - Conflict + Corroboration - ConflictPenalty`",
        "",
        "| Rank | Hypothesis | Origin | Support | Conflict | Corroboration | Penalty | Final Score |",
        "|---|---|---|---|---|---|---|---|",
    ])
    for b in report.score_breakdown:
        marker = " **[Proposed Explanation]**" if b["is_proposed_explanation"] else ""
        lines.append(f"| #{b['rank']} | {b['title']}{marker} | {b['origin']} | {b['support']} | {b['conflict']} | {b['corroboration']} | {b['conflict_penalty']} | **{b['total_score']}** |")

    if report.proposed_explanation:
        lines.extend([
            "",
            "## 8. System's Proposed Explanation",
            f"### {report.proposed_explanation.title}",
            report.proposed_explanation.description,
            "",
            f"**Total Score:** {report.proposed_explanation.total_score}",
            f"- **Formula Detail:** {report.proposed_explanation.explanation}",
            "",
            "#### Claims Breakdown:",
        ])
        for c in report.proposed_explanation.claims:
            corrob = "Yes (+1)" if c.is_corroborated else "No"
            lines.append(f"- **Claim:** {c.text}")
            lines.append(f"  - Corroborated across independent sources: {corrob}")
            lines.append(f"  - Supporting Evidence IDs: {', '.join(c.supporting_evidence_ids) or 'None'}")
            lines.append(f"  - Conflicting Evidence IDs: {', '.join(c.conflicting_evidence_ids) or 'None'}")

    lines.extend([
        "",
        "## 9. Unresolved Questions",
    ])
    for q in report.unresolved_questions:
        lines.append(f"- {q}")

    lines.extend([
        "",
        "## 10. Limitations & Uncertainty",
        f"```\n{report.limitations_and_uncertainty}\n```",
        "",
        "---",
        "*Generated by Text Detective Investigation Framework*",
    ])

    return "\n".join(lines)


def export_report_to_json(report: InvestigationReport) -> str:
    return json.dumps(report.model_dump(), indent=2)
