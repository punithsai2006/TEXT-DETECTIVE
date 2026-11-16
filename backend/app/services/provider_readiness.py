"""Readiness without generation, billing assumptions or credential disclosure."""
import httpx
from urllib.parse import quote
from app.services.llm_provider import get_llm_provider
from app.config import settings


def provider_readiness(probe=False, provider_factory=None):
    def state(result, status, message, can_analyze=False, ready=False):
        return {**result, "status": status, "message": message, "can_analyze": can_analyze,
                "ready": ready, "retryable": False if not can_analyze else None}
    try:
        provider = (provider_factory or get_llm_provider)()
    except ValueError:
        return state({"model": None, "is_mock": False}, "invalid_provider", "Set LLM_PROVIDER to openai, anthropic, ollama or local in backend environment settings.")
    result = {"provider": settings.LLM_PROVIDER, "model": provider.model_name(), "is_mock": bool(provider.is_mock),
              "ready": False, "status": "not_probed", "generation_tested": False}
    if provider.is_mock:
        return state(result, "explicit_mock_ai_analysis_unavailable",
            "LLM_PROVIDER=mock cannot run real investigation analysis. In Render Environment, select a real LLM_PROVIDER, set LLM_MODEL and its API key, then redeploy. No answers will be invented.")
    if settings.LLM_PROVIDER in {"local", "ollama"}:
        ready = provider.is_available() if probe else False
        return state(result, "ready" if ready else "unavailable" if probe else "not_probed",
            "Local model available." if ready else "Check the installed local model and service; use Check provider to test readiness.", ready or not probe, ready)
    if not provider.is_available():
        return state(result, "missing_credentials", "Set the selected provider's backend API key and LLM_MODEL, then restart/redeploy. Keys must never be entered into case documents.")
    if not probe:
        return state(result, "credentials_present_model_access_unverified", "Credentials are present; model access and generation are not yet verified.", True)
    # Metadata requests only; no evidence is sent and no generation is requested.
    model = quote(provider.model_name(), safe="")
    url, headers = ((f"https://api.openai.com/v1/models/{model}", {"Authorization": "Bearer " + settings.OPENAI_API_KEY})
        if settings.LLM_PROVIDER == "openai" else
        (f"https://api.anthropic.com/v1/models/{model}", {"x-api-key": settings.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"}))
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(url, headers=headers)
        response.raise_for_status()
        return state(result, "model_metadata_accessible_generation_unverified", "Model metadata is accessible; generation remains unverified.", True, True)
    except Exception:
        return state(result, "model_access_or_connectivity_failed", "Model metadata could not be accessed. Check model ID, credentials, provider access and connectivity.")
