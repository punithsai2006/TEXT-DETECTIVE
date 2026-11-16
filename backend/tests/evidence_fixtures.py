"""Scripted provider for contract/integration tests ONLY, never a real-model benchmark.

This module is outside uploaded sample cases. It returns known records so tests
can exercise persistence, tool routing and verification without credentials.
"""
import json
from app.services.llm_provider import BaseLLMProvider, LLMResponse


class FixtureProvider(BaseLLMProvider):
    is_mock = True

    def __init__(self, claims_by_quote=None, supported=True, malformed=False):
        self.claims_by_quote = claims_by_quote or {}
        self.supported = supported
        self.malformed = malformed
        self.prompts = []

    def model_name(self):
        return "fixture-evidence-review-contract-only"

    def is_available(self):
        return True

    def generate(self, prompt, system_prompt=None):
        self.prompts.append((prompt, system_prompt))
        if self.malformed:
            return LLMResponse(content="not JSON", provider="fixture", model=self.model_name(), is_mock=True)
        data = json.loads(prompt)
        if '"title": "Extraction"' in system_prompt:
            claims = []
            for source in data["sources"]:
                for fields in self.claims_by_quote.get(source["quote"], []):
                    claims.append({**fields, "source_span_ids": [source["span_id"]]})
            output = {"claims": claims}
        elif '"title": "ToolDecision"' in system_prompt:
            output = {"action": "retrieve_context", "query": data["claim_a"]["subject"],
                      "reason": "Retrieve surrounding source context before comparing the accounts."}
        elif '"title": "Comparison"' in system_prompt:
            a, b = data["claim_a"], data["claim_b"]
            output = {"outcome": "POTENTIAL_CONTRADICTION" if a["object"] != b["object"] else "COMPATIBLE",
                      "conflict_type": "fixture_state_comparison", "explanation": "Scripted contract comparison; not model reasoning.",
                      "assumptions": ["Fixture specifies a shared observation time"], "ambiguities": []}
        elif '"title": "AnswerDraft"' in system_prompt:
            if data.get("persisted_computed_assessments") and "hypothes" in data["question"].lower():
                context = data["persisted_computed_assessments"]
                output = {"assertions": [{"text": "The persisted candidate hypotheses are tied; no leading explanation is designated."
                            if context["leading_hypothesis_id"] is None else "The persisted leading interpretation remains a qualified suggestion.",
                            "kind": "interpretation", "source_span_ids": [s["span_id"] for s in data["evidence"][:2]]}],
                          "unknowns": ["Additional evidence is needed to distinguish the competing interpretations."]}
            elif "who opened" in data["question"].lower():
                output = {"assertions": [], "unknowns": ["The supplied sources do not identify who opened the door."]}
            else:
                source = data["evidence"][0]
                output = {"assertions": [{"text": "A source states: " + source["quote"],
                                           "kind": "source_claim", "source_span_ids": [source["span_id"]]}], "unknowns": []}
        elif '"title": "SupportDecision"' in system_prompt:
            output = {"supported": self.supported, "explanation": "Scripted support decision for testing."}
        elif '"title": "HypothesisDraft"' in system_prompt:
            claims = data["claims"]
            output = {"hypotheses": [{"hypothesis_id": f"H{i + 1}",
                "title": f"Candidate interpretation of account {i + 1}",
                "description": f"The {c['object']}-door account may describe the observation; the other account may be mistaken.",
                "necessary_claims": [{"requirement_id": "R1", "text": f"The archive door was {c['object']} at the reported time."}],
                "relevant_claim_ids": [c["claim_id"]], "source_span_ids": c["source_span_ids"],
                "assumptions": ["Source clocks and event identity require review"],
                "missing_evidence": ["Independent confirmation of the door state and clock alignment"]}
                for i, c in enumerate(claims[:2])], "unanswered_questions": ["Which observation, if either, is accurate?"]}
        elif '"title": "HypothesisAssessment"' in system_prompt:
            proposal = data["hypothesis"]
            refs = proposal["source_span_ids"]
            others = [s["span_id"] for s in data["passages"] if s["span_id"] not in refs]
            output = {"requirements": [{"requirement_id": "R1", "supporting_source_span_ids": refs,
                "contrary_source_span_ids": others[:1], "explanation": "Scripted fixture assessment, not real inference.",
                "unresolved_assumptions": ["Source clocks and event identity require review"]}],
                "temporal": {"status": "unknown", "explanation": "Clock alignment not independently established", "source_span_ids": []},
                "relationships": {"status": "unknown", "explanation": "Access constraints not established", "source_span_ids": []},
                "additional_missing_evidence": []}
        elif '"title": "ReportDraft"' in system_prompt:
            passages = data["passages"]
            output = {"executive_summary": [{"text": "A supplied source states: " + passages[0]["quote"],
                "kind": "source_claim", "source_span_ids": [passages[0]["span_id"]]}] if passages else [],
                "sections": [{"title": "Competing accounts", "assertions": [],
                              "unknowns": ["The fixture does not determine which account is accurate."]}],
                "unanswered_questions": ["What additional evidence can resolve the competing accounts?"],
                "limitations": ["FIXTURE ONLY: scripted test output; no real-model inference."]}
        elif '"title": "DebateDraft"' in system_prompt:
            refs = [s["span_id"] for s in data["sources"][:2]]
            output = {"arguments": [{"text": "The supplied accounts differ; the available sources do not establish which account is accurate.",
                "kind": "interpretation", "source_span_ids": refs}] if refs else [],
                "unresolved_questions": ["Independent observation and clock alignment remain missing."]}
        elif '"title": "VerificationBatch"' in system_prompt:
            output = {"checks": [{"assertion_id": a["assertion_id"], "supported": self.supported,
                                   "explanation": "Scripted fixture verification, not a real-model result."}
                                  for a in data["assertions"]]}
        else:
            raise AssertionError("Unexpected fixture request schema")
        return LLMResponse(content=json.dumps(output), provider="fixture", model=self.model_name(), is_mock=True,
                           metadata={"usage": {"fixture": True}})


DOOR_A = "At 2026-11-01 20:00 UTC, the archive door was locked."
DOOR_B = "At 2026-11-01 20:00 UTC, the archive door was open."


def door_claim(value):
    return {"subject": "archive door", "predicate": "state", "object": value,
            "polarity": "positive", "entity_identity": "explicit", "event_scope": "archive door observation",
            "event_start": "2026-11-01T20:00:00+00:00", "timezone": "UTC", "precision": "minute"}


def door_provider(**kwargs):
    return FixtureProvider({DOOR_A: [door_claim("locked")], DOOR_B: [door_claim("open")]}, **kwargs)
