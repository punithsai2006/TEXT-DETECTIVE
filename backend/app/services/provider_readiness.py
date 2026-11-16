"""Readiness without generation, billing assumptions or credential disclosure."""
import httpx
from urllib.parse import quote
from app.services.llm_provider import get_llm_provider
from app.config import settings


def provider_readiness(probe=False):
    try:
        provider = get_llm_provider()
    except ValueError:
        return {"ready": False, "status": "invalid_provider", "model": None, "is_mock": False}
    result = {"provider": settings.LLM_PROVIDER, "model": provider.model_name(), "is_mock": bool(provider.is_mock),
              "ready": False, "status": "not_probed", "generation_tested": False}
    if provider.is_mock:
        return {**result, "status": "explicit_mock_ai_analysis_unavailable"}
    if settings.LLM_PROVIDER in {"local", "ollama"}:
        ready = provider.is_available() if probe else False
        return {**result, "ready": ready, "status": "ready" if ready else "unavailable" if probe else "not_probed"}
    if not provider.is_available():
        return {**result, "status": "missing_credentials"}
    if not probe:
        return {**result, "status": "credentials_present_model_access_unverified"}
    # Metadata requests only; no evidence is sent and no generation is requested.
    model = quote(provider.model_name(), safe="")
    url, headers = ((f"https://api.openai.com/v1/models/{model}", {"Authorization": "Bearer " + settings.OPENAI_API_KEY})
        if settings.LLM_PROVIDER == "openai" else
        (f"https://api.anthropic.com/v1/models/{model}", {"x-api-key": settings.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"}))
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(url, headers=headers)
        response.raise_for_status()
        return {**result, "ready": True, "status": "model_metadata_accessible_generation_unverified"}
    except Exception:
        return {**result, "status": "model_access_or_connectivity_failed"}
