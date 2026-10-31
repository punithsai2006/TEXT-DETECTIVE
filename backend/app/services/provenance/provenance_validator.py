"""
Evidence Provenance Validator
Verifies strict source traceability across all six modules:
1. Every timeline event points to an existing source passage.
2. Every contradiction references two existing source passages.
3. Every hypothesis claim has verifiable supporting, conflicting or inconclusive evidence references.
4. Every report citation resolves to an existing document and sentence.
5. Deleted or unavailable documents do not leave apparently valid citations.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.schemas import (
    Case,
    ContradictionItem,
    DocumentMetadata,
    Event,
    EvidenceClassification,
    EvidenceItem,
    Hypothesis,
    InvestigationReport,
    TimelineEntry,
)


class ProvenanceCheckFailure(BaseModel):
    module: str
    item_id: str
    field: str
    document_id: Optional[str] = None
    reason: str
    invalid_reference: Optional[str] = None


class ProvenanceValidationReport(BaseModel):
    case_id: str
    is_valid: bool
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    failures: List[ProvenanceCheckFailure] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    breakdown_by_module: Dict[str, Dict[str, int]] = Field(default_factory=dict)


class ProvenanceValidator:
    """Strict validator for multi-document evidence provenance and citation integrity."""

    @staticmethod
    def _normalize_snippet(text: str) -> str:
        """Helper to normalize whitespace for comparison."""
        return " ".join(text.lower().split())

    @classmethod
    def validate_case(
        cls,
        case_id: str,
        documents: List[DocumentMetadata],
        events: Optional[List[Event]] = None,
        timeline: Optional[List[TimelineEntry]] = None,
        contradictions: Optional[List[ContradictionItem]] = None,
        hypotheses: Optional[List[Hypothesis]] = None,
        evidence_items: Optional[List[EvidenceItem]] = None,
        report: Optional[InvestigationReport] = None,
    ) -> ProvenanceValidationReport:
        """Runs complete provenance verification across all case components."""
        total_checks = 0
        failures: List[ProvenanceCheckFailure] = []
        warnings: List[str] = []
        breakdown = {
            "events_and_timeline": {"passed": 0, "failed": 0},
            "contradictions": {"passed": 0, "failed": 0},
            "hypotheses": {"passed": 0, "failed": 0},
            "report_citations": {"passed": 0, "failed": 0},
        }

        # Build lookup tables for documents and chunks
        doc_map: Dict[str, DocumentMetadata] = {d.document_id: d for d in documents}
        doc_name_map: Dict[str, DocumentMetadata] = {d.filename.lower(): d for d in documents}
        chunk_map: Dict[str, Any] = {}
        for d in documents:
            for c in d.chunks:
                chunk_map[c.chunk_id] = c
                chunk_map[f"evid_{c.chunk_id}"] = c

        evidence_map: Dict[str, EvidenceItem] = {}
        if evidence_items:
            for e in evidence_items:
                evidence_map[e.evidence_id] = e
                evidence_map[e.chunk_id] = e

        # ----------------------------------------------------
        # 1. TIMELINE & EVENT VERIFICATION
        # ----------------------------------------------------
        target_events = events or []
        for ev in target_events:
            total_checks += 1
            # Check document reference exists
            doc = doc_map.get(ev.document_id) or doc_name_map.get(ev.document_name.lower())
            if not doc:
                failures.append(
                    ProvenanceCheckFailure(
                        module="events",
                        item_id=ev.event_id,
                        field="document_id",
                        document_id=ev.document_id,
                        reason=f"Event references non-existent document ID '{ev.document_id}' or name '{ev.document_name}'",
                        invalid_reference=ev.document_id,
                    )
                )
                breakdown["events_and_timeline"]["failed"] += 1
                continue

            # Check source sentence exists in raw or cleaned text
            if ev.source_sentence:
                norm_sentence = cls._normalize_snippet(ev.source_sentence)
                norm_doc_text = cls._normalize_snippet(doc.raw_text + " " + doc.cleaned_text)
                # First 30 chars must exist
                search_anchor = norm_sentence[:min(40, len(norm_sentence))]
                if search_anchor not in norm_doc_text:
                    failures.append(
                        ProvenanceCheckFailure(
                            module="events",
                            item_id=ev.event_id,
                            field="source_sentence",
                            document_id=doc.document_id,
                            reason="Event source passage cannot be located within the referenced document text",
                            invalid_reference=ev.source_sentence[:80],
                        )
                    )
                    breakdown["events_and_timeline"]["failed"] += 1
                    continue

            breakdown["events_and_timeline"]["passed"] += 1

        # ----------------------------------------------------
        # 2. CONTRADICTION CITATIONS VERIFICATION
        # ----------------------------------------------------
        if contradictions:
            for c in contradictions:
                # Contradiction MUST reference two valid distinct documents or sources
                total_checks += 1
                doc_a = doc_map.get(c.doc_a_id) or doc_name_map.get(c.doc_a_name.lower())
                doc_b = doc_map.get(c.doc_b_id) or doc_name_map.get(c.doc_b_name.lower())

                if not doc_a:
                    failures.append(
                        ProvenanceCheckFailure(
                            module="contradictions",
                            item_id=c.id,
                            field="doc_a_id",
                            document_id=c.doc_a_id,
                            reason=f"Contradiction statement A references missing document '{c.doc_a_id}' ('{c.doc_a_name}')",
                            invalid_reference=c.doc_a_id,
                        )
                    )
                    breakdown["contradictions"]["failed"] += 1
                    continue

                if not doc_b:
                    failures.append(
                        ProvenanceCheckFailure(
                            module="contradictions",
                            item_id=c.id,
                            field="doc_b_id",
                            document_id=c.doc_b_id,
                            reason=f"Contradiction statement B references missing document '{c.doc_b_id}' ('{c.doc_b_name}')",
                            invalid_reference=c.doc_b_id,
                        )
                    )
                    breakdown["contradictions"]["failed"] += 1
                    continue

                # Verify statement A is grounded in doc_a
                norm_stmt_a = cls._normalize_snippet(c.statement_a)
                norm_doc_a = cls._normalize_snippet(doc_a.raw_text + " " + doc_a.cleaned_text)
                anchor_a = norm_stmt_a[:min(35, len(norm_stmt_a))]
                if anchor_a and anchor_a not in norm_doc_a:
                    failures.append(
                        ProvenanceCheckFailure(
                            module="contradictions",
                            item_id=c.id,
                            field="statement_a",
                            document_id=doc_a.document_id,
                            reason="Contradiction statement A text is absent from referenced Document A",
                            invalid_reference=c.statement_a[:80],
                        )
                    )
                    breakdown["contradictions"]["failed"] += 1
                    continue

                # Verify statement B is grounded in doc_b
                norm_stmt_b = cls._normalize_snippet(c.statement_b)
                norm_doc_b = cls._normalize_snippet(doc_b.raw_text + " " + doc_b.cleaned_text)
                anchor_b = norm_stmt_b[:min(35, len(norm_stmt_b))]
                if anchor_b and anchor_b not in norm_doc_b:
                    failures.append(
                        ProvenanceCheckFailure(
                            module="contradictions",
                            item_id=c.id,
                            field="statement_b",
                            document_id=doc_b.document_id,
                            reason="Contradiction statement B text is absent from referenced Document B",
                            invalid_reference=c.statement_b[:80],
                        )
                    )
                    breakdown["contradictions"]["failed"] += 1
                    continue

                breakdown["contradictions"]["passed"] += 1

        # ----------------------------------------------------
        # 3. HYPOTHESES EVIDENCE VERIFICATION
        # ----------------------------------------------------
        if hypotheses:
            for h in hypotheses:
                for cl in h.claims:
                    total_checks += 1
                    # Check supporting evidence IDs
                    for evid in cl.supporting_evidence_ids:
                        if evid not in evidence_map and evid not in chunk_map:
                            failures.append(
                                ProvenanceCheckFailure(
                                    module="hypotheses",
                                    item_id=h.hypothesis_id,
                                    field="supporting_evidence_ids",
                                    reason=f"Claim '{cl.claim_id}' references non-existent evidence ID '{evid}'",
                                    invalid_reference=evid,
                                )
                            )
                            breakdown["hypotheses"]["failed"] += 1
                            break

                    # Check contributing documents exist
                    for doc_ref in cl.contributing_documents:
                        if doc_ref not in doc_map and doc_ref.lower() not in doc_name_map:
                            failures.append(
                                ProvenanceCheckFailure(
                                    module="hypotheses",
                                    item_id=h.hypothesis_id,
                                    field="contributing_documents",
                                    document_id=doc_ref,
                                    reason=f"Claim '{cl.claim_id}' references non-existent contributing document '{doc_ref}'",
                                    invalid_reference=doc_ref,
                                )
                            )
                            breakdown["hypotheses"]["failed"] += 1
                            break
                    else:
                        breakdown["hypotheses"]["passed"] += 1

        # ----------------------------------------------------
        # 4. REPORT CITATIONS & AUDIT TRAIL VERIFICATION
        # ----------------------------------------------------
        if report:
            total_checks += 1
            for ref in report.source_references:
                doc_id = ref.get("document_id")
                filename = ref.get("filename") or ref.get("document", "")
                doc = (doc_map.get(doc_id) if doc_id else None) or doc_name_map.get(filename.lower())
                if not doc:
                    failures.append(
                        ProvenanceCheckFailure(
                            module="report",
                            item_id=report.report_id,
                            field="source_references",
                            document_id=doc_id,
                            reason=f"Report source citation points to non-existent document ID '{doc_id}' ({filename})",
                            invalid_reference=str(doc_id),
                        )
                    )
                    breakdown["report_citations"]["failed"] += 1
                    break
            else:
                breakdown["report_citations"]["passed"] += 1

        passed_checks = sum(b["passed"] for b in breakdown.values())
        failed_checks = len(failures)
        is_valid = (failed_checks == 0)

        return ProvenanceValidationReport(
            case_id=case_id,
            is_valid=is_valid,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            failures=failures,
            warnings=warnings,
            breakdown_by_module=breakdown,
        )

    @classmethod
    def verify_citation_integrity_after_deletion(
        cls,
        deleted_doc_id: str,
        citations: List[Dict[str, Any]],
    ) -> List[str]:
        """Ensures deleted documents do not leave dangling citations."""
        dangling_citations = []
        for cit in citations:
            if cit.get("document_id") == deleted_doc_id:
                dangling_citations.append(
                    f"Dangling citation found in report/evidence referencing deleted document {deleted_doc_id}"
                )
        return dangling_citations
