"""Explicit, conservative source preview for test mechanics, never AI inference.

No case names, dates, identities or ground-truth answers are embedded here.
Only exact supplied quotations pass the deterministic preview verifier.
"""
import json
import re
from app.services.llm_provider import BaseLLMProvider, LLMResponse

PREFIX = "Source passage (uninterpreted): "


def exact_quote_supported(assertion, sources):
    text = assertion["text"]
    return (assertion.get("kind") == "source_claim" and text.startswith(PREFIX)
            and bool(text[len(PREFIX):])
            and any(text[len(PREFIX):] in s["quote"] for s in sources))


class OfflinePreviewProvider(BaseLLMProvider):
    is_mock = True

    def model_name(self):
        return "offline-source-preview-v1-no-llm"

    def is_available(self):
        return True

    def generate(self, prompt, system_prompt=None):
        data = json.loads(prompt)
        task = system_prompt or ""
        task = re.sub(r'"title"\s*:\s*"([^\"]+)"', lambda m: '"title": "' + m.group(1) + '"', task)
        if '"title": "Extraction"' in task:
            output = {"claims": [{"subject": s["span_id"][:200], "predicate": "contains_source_passage",
                "object": s["quote"][:500], "polarity": "unknown", "entity_identity": "ambiguous",
                "event_start": None, "timezone": None, "precision": "unknown", "event_basis": "reported",
                "source_span_ids": [s["span_id"]], "uncertainty": ["Offline preview: entities and event times have not been interpreted."]}
                for s in data["sources"]], "entities": []}
        elif '"title": "ToolDecision"' in task:
            output = {"action": "compare", "reason": "Offline preview cannot perform contextual interpretation."}
        elif '"title": "Comparison"' in task:
            output = {"outcome": "INSUFFICIENT_EVIDENCE", "conflict_type": "offline_unassessed",
                      "explanation": "Contextual comparison requires a real model and human review.", "assumptions": [], "ambiguities": ["Not assessed in offline preview."]}
        elif '"title": "HypothesisDraft"' in task:
            output = {"hypotheses": [], "unanswered_questions": ["Real-model hypothesis analysis has not been performed."]}
        elif '"title": "ReportDraft"' in task:
            output = {"executive_summary": [{"text": PREFIX + s["quote"][:1400], "kind": "source_claim",
                       "source_span_ids": [s["span_id"]]} for s in data["passages"][:2]],
                      "sections": [], "unanswered_questions": ["No reconstruction or contradiction conclusions are available in offline preview."],
                      "limitations": ["OFFLINE SOURCE PREVIEW ONLY: no generative model or semantic verification ran. Unknown event times remain unknown."]}
        elif '"title": "VerificationBatch"' in task:
            output = {"checks": [{"assertion_id": a["assertion_id"], "supported": exact_quote_supported(a, a["passages"]),
                       "explanation": "Deterministic verbatim-source check only; no semantic model assessment."} for a in data["assertions"]]}
        elif '"title": "DebateDraft"' in task:
            output = {"arguments": [], "unresolved_questions": ["Supporting, challenging and neutral interpretation requires a real LLM."]}
        elif '"title": "AnswerDraft"' in task:
            output = {"assertions": [], "unknowns": ["Offline preview cannot interpret this question. Use Evidence Search to inspect the original passages or configure a real provider."]}
        elif '"title": "SupportDecision"' in task:
            output = {"supported": exact_quote_supported(data["assertion"], data["sources"]),
                      "explanation": "Deterministic quotation check, not semantic support."}
        else:
            raise ValueError("Unsupported offline preview operation")
        return LLMResponse(content=json.dumps(output), provider="offline_preview", model=self.model_name(), is_mock=True,
                           metadata={"usage": {"simulated": True, "billable_tokens": 0}})
