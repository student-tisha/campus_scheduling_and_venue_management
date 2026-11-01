import logging

import httpx

from app.config import settings

log = logging.getLogger("llm")


def llm_available() -> bool:
    return bool(settings.llm_api_key and settings.llm_model)


def call_llm(system: str, user: str) -> str | None:
    """Returns the model's text, or None on any failure (callers must have a fallback)."""
    if not llm_available():
        return None
    try:
        if settings.llm_provider == "anthropic":
            r = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": settings.llm_api_key,
                         "anthropic-version": "2023-06-01"},
                json={"model": settings.llm_model, "max_tokens": 900, "system": system,
                      "messages": [{"role": "user", "content": user}]},
                timeout=25,
            )
            r.raise_for_status()
            return r.json()["content"][0]["text"]
        base = settings.llm_base_url.rstrip("/")
        r = httpx.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json={"model": settings.llm_model, "temperature": 0,
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": user}]},
            timeout=25,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:  # noqa: BLE001
        log.warning("LLM call failed: %s", e)
        return None
