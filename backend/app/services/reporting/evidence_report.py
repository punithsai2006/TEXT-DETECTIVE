"""Render the persisted, verified narrative and fixed findings; never call a model."""
from html import escape
from io import BytesIO
from pathlib import Path


def markdown_report(report):
    sources = {s["chunk_id"]: s for s in report.source_references}
    def cite(ids):
        labels = []
        for source_id in ids:
            source = sources[source_id]
            label = source["filename"]
            if source.get("page_number"):
                label += f", PDF page {source['page_number']}"
            label += f", extracted paragraph {source['paragraph']}"
            labels.append(f"[{label}; {source_id}]")
        return " ".join(labels)
    summary = report.case_summary
    lines = [f"# Text Detective: {report.case_name}",
             "FIXTURE ONLY - scripted workflow outputs; no real-model inference." if report.is_mock else "Model-assisted evidence review - human review required.",
             f"Case ID: {report.case_id}", f"Analysis run: {report.analysis_run_id}",
             f"Model: {report.model_name}", f"Generated: {report.generated_at}",
             "Source claims and investigative leads do not establish what actually happened.",
             "## 1. Executive summary"]
    for assertion in report.llm_narrative.get("executive_summary", []):
        lines.append(assertion["text"] + " " + cite(assertion["source_span_ids"]))
    if not report.llm_narrative.get("executive_summary"):
        lines.append("The evidence does not support a substantive summary. Review the unknowns below.")
    lines += ["## 2. Investigation details", f"Description: {report.case_overview}",
              f"Documents: {len(report.documents_analyzed)}; status: {summary.analysis_status}"]
    lines += ["## 3. Hypothesis Scoring - competing explanations",
              "Evidence-support score - not a probability of guilt.",
              "No leading hypothesis is designated: evidence is inadequate, unresolved or tied." if summary.leading_hypothesis is None
              else f"Most supported qualified interpretation: {summary.leading_hypothesis.title}. This remains an interpretation."]
    hypotheses = ([summary.leading_hypothesis] if summary.leading_hypothesis else []) + summary.alternative_hypotheses
    for hypothesis in hypotheses:
        lines += [f"### {hypothesis.hypothesis_id}: {hypothesis.title}", hypothesis.description + " " + cite(hypothesis.description_source_span_ids),
                  f"Evidence-support score: {hypothesis.evidence_support_score if hypothesis.evidence_support_score is not None else 'Not scored (open alternative)'}",
                  f"Score method: {hypothesis.score_method_version}"]
        if hypothesis.score_breakdown:
            b = hypothesis.score_breakdown
            lines += ["Deterministic components (normalized input x versioned weight = contribution):"]
            for key, contribution in b.weighted_components.items():
                lines.append(f"- {key}: {getattr(b, key):.3f} x {b.weights[key]:g} = {contribution:.3f}")
            lines.append(f"Necessary claims: {b.necessary_claim_count}; distinct text lineages: {b.distinct_lineage_count} (not verified independent authors).")
        for requirement in hypothesis.necessary_claims:
            lines.append(f"Necessary claim {requirement.requirement_id}: {requirement.text}")
            assessed = next((a for a in hypothesis.requirement_assessments if a.requirement_id == requirement.requirement_id), None)
            if assessed:
                lines.append("Assessment: " + assessed.explanation)
                lines.append("Claim support: " + (cite(assessed.supporting_source_span_ids) or "None established"))
                lines.append("Claim opposition: " + (cite(assessed.contrary_source_span_ids) or "None established"))
        lines += ["Supporting passages: " + (cite(hypothesis.supporting_source_span_ids) or "None established"),
                  "Contrary passages: " + (cite(hypothesis.contrary_source_span_ids) or "None established"),
                  "Assumptions: " + ("; ".join(hypothesis.assumptions) or "None reported"),
                  "Missing evidence: " + ("; ".join(hypothesis.missing_evidence) or "Inspect source coverage"),
                  "Timeline events: " + (", ".join(hypothesis.relevant_event_ids) or "None linked"),
                  "Graph nodes: " + (", ".join(hypothesis.relevant_graph_node_ids) or "None linked")]
    lines.append("## 4. Contradictions and human review")
    for finding in report.contradictions:
        lines += [f"### {finding.outcome}: {finding.entity_event_link}", finding.explanation,
                  f"Review: {finding.review_action or 'pending_review'}; reviewer label: {finding.reviewer_id or 'none'}",
                  f"Review notes: {finding.review_notes or 'None'}",
                  "Assumptions: " + "; ".join(finding.assumptions + finding.ambiguities),
                  "Account A: " + finding.statement_a + " " + cite([finding.chunk_a_id]),
                  "Account B: " + finding.statement_b + " " + cite([finding.chunk_b_id])]
    lines.append("## 5. Detailed timeline")
    for event in report.chronological_timeline:
        lines += [f"### {event.timestamp_display}", event.event_description,
                  f"Basis: {event.event_basis}; ordering group: {event.ordering_group}; record time: {event.record_time or 'unknown'}",
                  f"Interval end: {event.event_end or 'unspecified'}; uncertainty: {event.is_uncertain}",
                  cite(event.source_span_ids or [event.chunk_id])]
    lines += ["## 6. Entity relationships", "Edges are derived from their originating passages, not independent evidence."]
    if report.graph_snapshot:
        labels = {n.id: n.label for n in report.graph_snapshot.nodes}
        for edge in report.graph_snapshot.edges:
            lines.append(f"- {labels[edge.source]} -- {edge.relation} --> {labels[edge.target]}. " + cite(edge.source_span_ids))
    lines.append("## 7. Verified model narrative")
    for section in report.llm_narrative.get("sections", []):
        lines.append("### " + section["title"])
        for assertion in section["assertions"]:
            lines.append(assertion["kind"] + ": " + assertion["text"] + " " + cite(assertion["source_span_ids"]))
        lines += ["Unknown: " + text for text in section["unknowns"]]
    lines.append("## 8. Evidence appendix - exact quotations")
    for source in report.source_references:
        lines += ["### " + cite([source["chunk_id"]]), source["quote"],
                  f"Extracted-text offsets [{source['char_start']}, {source['char_end']}); extraction version {source['extraction_version']}."]
    lines.append("## 9. Unanswered questions and limitations")
    lines += ["- " + text for text in summary.unanswered_questions]
    lines += ["- " + item.text for item in summary.limitations]
    lines.append(report.limitations_and_uncertainty)
    lines += ["## 10. Uploaded evidence inventory and extraction information"]
    for doc in report.documents_analyzed:
        lines.append(f"- {doc['filename']}; type {doc['document_type']}; {doc['chunk_count']} source spans; {doc['file_size_bytes']} bytes.")
    if report.graph_snapshot:
        for node in report.graph_snapshot.nodes:
            if node.node_type == "document":
                lines.append(f"- {node.label}; SHA-256 {node.properties.get('document_hash', 'unknown')}; extraction {node.properties.get('extraction_version', 'unknown')}.")
    deliberation = report.agent_deliberations
    if deliberation and deliberation.schema_version == "five-agent-evidence-v1":
        lines += ["## 11. Multi-agent deliberation summary",
                  f"Run {deliberation.run_id}; {deliberation.processing_status}; model {deliberation.model_name}; mock {deliberation.is_mock}.",
                  f"{deliberation.model_calls} model calls; {deliberation.tool_calls} stage tools; configuration {deliberation.configuration}."]
        for state in deliberation.agent_states:
            lines.append(f"- {state.name}: {state.status}; {state.evidence_items} cited items; {state.findings_produced} outputs.")
        lines.append("## 12. Summary investigation timeline")
        for item in deliberation.timeline_milestones:
            lines += [f"### {item.timestamp_range}", item.summary,
                      f"Basis {item.event_basis}; uncertainty {item.uncertainty}; phase {item.phase or 'unclassified'}.", cite(item.source_span_ids)]
        lines.append("## 13. Graph-RAG findings")
        for finding in deliberation.graph_findings:
            lines += [finding.summary, cite(finding.supporting_span_ids)]
            for path in finding.graph_paths:
                lines.append(" -> ".join(path["node_ids"]) + " " + cite(path["source_span_ids"]))
        lines.append("## 14. Adversarial hypothesis arguments")
        for title, items in [("Supporting Advocate", deliberation.supporting_arguments),
                             ("Challenging Advocate", deliberation.challenging_arguments),
                             ("Neutral Evidence Arbiter", deliberation.neutral_assessment)]:
            lines.append("### " + title)
            for item in items:
                lines += [item.summary, cite(item.supporting_span_ids + item.opposing_span_ids),
                          "Unresolved: " + "; ".join(item.unresolved_questions)]
        lines += ["## 15. Agent processing limitations"] + deliberation.warnings + deliberation.unresolved_questions
    lines += ["## 16. Final evidence-based assessment",
              "No actual event, guilt, innocence or source reliability is established by this report. "
              + ("A qualified leading interpretation is available; inspect its support, opposition and limitations." if summary.leading_hypothesis else
                 "No leading interpretation is designated; the available evidence remains inconclusive.")]
    return "\n\n".join(lines)


def pdf_report(report):
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
    from reportlab.graphics.shapes import Drawing, Line, Rect, String

    normal, bold = "Helvetica", "Helvetica-Bold"
    fonts = [(Path("C:/Windows/Fonts/segoeui.ttf"), Path("C:/Windows/Fonts/segoeuib.ttf")),
             (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))]
    for regular, heavy in fonts:
        if regular.is_file() and heavy.is_file():
            if "EvidenceSans" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("EvidenceSans", str(regular)))
                pdfmetrics.registerFont(TTFont("EvidenceSansBold", str(heavy)))
            normal, bold = "EvidenceSans", "EvidenceSansBold"
            break
    styles = getSampleStyleSheet()
    body = ParagraphStyle("EvidenceBody", fontName=normal, fontSize=9, leading=13, spaceAfter=6,
                          textColor=colors.HexColor("#253047"), splitLongWords=True, alignment=TA_LEFT)
    h1 = ParagraphStyle("EvidenceTitle", parent=body, fontName=bold, fontSize=19, leading=24, spaceAfter=16)
    h2 = ParagraphStyle("EvidenceSection", parent=body, fontName=bold, fontSize=13, leading=17,
                        spaceBefore=12, spaceAfter=8, keepWithNext=True)
    h3 = ParagraphStyle("EvidenceSubsection", parent=body, fontName=bold, fontSize=10, leading=14,
                        spaceBefore=7, spaceAfter=5, keepWithNext=True)
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=44, rightMargin=44, topMargin=48,
                                 bottomMargin=44, title=report.case_name, author="Text Detective")
    story = []
    for line in markdown_report(report).splitlines():
        if not line.strip():
            continue
        style = h1 if line.startswith("# ") else h2 if line.startswith("## ") else h3 if line.startswith("### ") else body
        text = line.lstrip("# ") if line.startswith("#") else line
        story.append(Paragraph(escape(text), style))
        if line.startswith("## 6.") and report.graph_snapshot and report.graph_snapshot.nodes:
            nodes = report.graph_snapshot.nodes[:12]
            width, height = 500, ((len(nodes) + 3) // 4) * 62 + 15
            drawing = Drawing(width, height)
            positions = {n.id: (15 + (i % 4) * 124, height - 48 - (i // 4) * 62) for i, n in enumerate(nodes)}
            for edge in report.graph_snapshot.edges:
                if edge.source in positions and edge.target in positions:
                    x1, y1 = positions[edge.source]; x2, y2 = positions[edge.target]
                    drawing.add(Line(x1 + 52, y1 + 15, x2 + 52, y2 + 15, strokeColor=colors.HexColor("#99A8BC")))
            for node in nodes:
                x, y = positions[node.id]
                drawing.add(Rect(x, y, 108, 32, rx=5, fillColor=colors.HexColor("#EEF3FA"), strokeColor=colors.HexColor("#8BA2C0")))
                drawing.add(String(x + 5, y + 19, node.node_type, fontName=normal, fontSize=7))
                drawing.add(String(x + 5, y + 7, node.label[:23], fontName=normal, fontSize=7))
            story.append(KeepTogether([drawing, Paragraph(f"Graph snapshot: first {len(nodes)} of {len(report.graph_snapshot.nodes)} nodes. Full relationships and citations follow.", body)]))
    def page_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(normal, 8)
        canvas.setFillColor(colors.HexColor("#59667B"))
        canvas.drawString(44, 24, "Text Detective | " + report.case_id + " | Human review required")
        canvas.drawRightString(A4[0] - 44, 24, str(doc.page))
        canvas.restoreState()
    document.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    return buffer.getvalue()
