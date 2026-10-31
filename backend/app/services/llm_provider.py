import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel
from app.config import settings

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    content: str
    provider: str
    model: str
    is_mock: bool = False
    metadata: Dict[str, Any] = {}


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def model_name(self) -> str:
        pass


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic Mock LLM provider for offline execution, automated testing,
    and self-contained demo environments.
    """
    def __init__(self, model_name_override: Optional[str] = None):
        self._model = model_name_override or "mock-investigator-v1"

    def is_available(self) -> bool:
        return True

    def model_name(self) -> str:
        return self._model

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        p_lower = prompt.lower()

        # Prompt injection & secret revelation defense (Task 4)
        if ("reveal" in p_lower or "show" in p_lower or "what is" in p_lower) and ("api key" in p_lower or "secret" in p_lower or "password" in p_lower):
            return LLMResponse(
                content="ACCESS DENIED: System credentials, API tokens, and internal secrets cannot be revealed under investigation security rules.",
                provider="mock",
                model=self._model,
                is_mock=True,
                metadata={"type": "security_refusal"}
            )

        # 1. Hypothesis claim decomposition
        if "decompose" in p_lower or "claims" in p_lower or "break into claims" in p_lower:
            # Deterministic extraction of claims
            lines = [line.strip() for line in prompt.split("\n") if line.strip()]
            claims = []
            for line in lines:
                if line.startswith("-") or line.startswith("*") or line.startswith("Claim:"):
                    clean = line.lstrip("-* ").replace("Claim:", "").strip()
                    if clean:
                        claims.append(clean)
            if not claims:
                # Default claim decomposition based on hypothesis text
                claims = [
                    "The suspected actor accessed the location during the incident timeframe.",
                    "The unauthorized action was made possible by compromised security controls.",
                    "Digital records and physical logs establish the sequence of actions."
                ]
            return LLMResponse(
                content=json.dumps({"claims": claims}),
                provider="mock",
                model=self._model,
                is_mock=True,
                metadata={"type": "claim_decomposition", "count": len(claims)}
            )

        # 2. Contradiction evaluation / NLI verification
        if "contradiction" in p_lower or "evaluate the following statements" in p_lower:
            is_conflict = "conflict" in p_lower or "denies" in p_lower or "disagrees" in p_lower or "different" in p_lower
            is_agreement = "agrees" in p_lower or "confirms" in p_lower or "both state" in p_lower
            if is_conflict:
                label = "contradiction"
                expl = "Statement A and Statement B present irreconcilable accounts of time, location, or authorization."
            elif is_agreement:
                label = "entailment"
                expl = "Both statements corroborate the same core factual point."
            else:
                label = "neutral"
                expl = "The statements discuss distinct facets of the incident without direct contradiction."
            return LLMResponse(
                content=json.dumps({"label": label, "confidence": 0.92, "explanation": expl}),
                provider="mock",
                model=self._model,
                is_mock=True,
                metadata={"type": "nli_verification"}
            )

        # 3. Question answering from evidence
        if "evidence" in p_lower and ("question" in p_lower or "where" in p_lower or "who" in p_lower or "what" in p_lower):
            answer_text = (
                "Based strictly on the verified case documents, the evidence indicates that "
                "the key actions occurred during the documented incident window. "
                "Cross-referencing the witness statements and server logs reveals specific timeline markers "
                "consistent with the primary findings in the case dossier."
            )
            return LLMResponse(
                content=answer_text,
                provider="mock",
                model=self._model,
                is_mock=True,
                metadata={"type": "question_answering"}
            )

        # 4. Default report synthesis response
        content = (
            "Investigation synthesis complete. The findings reflect rigorous cross-referencing "
            "between witness statements, badge swipe records, and digital audit logs."
        )
        return LLMResponse(
            content=content,
            provider="mock",
            model=self._model,
            is_mock=True,
            metadata={"type": "general"}
        )


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or "claude-3-5-sonnet-20241022"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("sk-ant-"))

    def model_name(self) -> str:
        return self.model

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        if not self.is_available():
            raise ValueError(
                "Anthropic API key is not configured or invalid. "
                "Set ANTHROPIC_API_KEY in .env or switch LLM_PROVIDER=mock."
            )

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            body["system"] = system_prompt

        try:
            with httpx.Client(timeout=45.0) as client:
                res = client.post("https://api.anthropic.com/v1/messages", headers=headers, json=body)
                res.raise_for_status()
                data = res.json()
                text = "".join(block.get("text", "") for block in data.get("content", []))
                return LLMResponse(
                    content=text,
                    provider="anthropic",
                    model=self.model,
                    is_mock=False,
                    metadata={"usage": data.get("usage", {})}
                )
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise RuntimeError(f"Anthropic API call failed: {str(e)}")


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or "gpt-4o"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("sk-"))

    def model_name(self) -> str:
        return self.model

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        if not self.is_available():
            raise ValueError(
                "OpenAI API key is not configured or invalid. "
                "Set OPENAI_API_KEY in .env or switch LLM_PROVIDER=mock."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }

        try:
            with httpx.Client(timeout=45.0) as client:
                res = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
                res.raise_for_status()
                data = res.json()
                text = data["choices"][0]["message"]["content"]
                return LLMResponse(
                    content=text,
                    provider="openai",
                    model=self.model,
                    is_mock=False,
                    metadata={"usage": data.get("usage", {})}
                )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise RuntimeError(f"OpenAI API call failed: {str(e)}")


def get_llm_provider() -> BaseLLMProvider:
    provider = settings.LLM_PROVIDER.lower().strip()
    if provider == "anthropic":
        return AnthropicProvider(
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.LLM_MODEL or "claude-3-5-sonnet-20241022"
        )
    elif provider == "openai":
        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.LLM_MODEL or "gpt-4o"
        )
    elif provider == "mock":
        return MockLLMProvider(model_name_override=settings.LLM_MODEL or "mock-investigator-v1")
    else:
        if settings.DEMO_MODE:
            logger.warning(f"Unknown provider '{provider}'. Falling back to MockLLMProvider in demo mode.")
            return MockLLMProvider()
        raise ValueError(
            f"Unsupported LLM provider '{provider}'. Supported providers are: 'mock', 'anthropic', 'openai'."
        )
