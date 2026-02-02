"""
Generic LLM layer: use any OpenAI-compatible provider (OpenAI, Ollama, etc.).
Same env vars as ai-services (LLM_PROVIDER, OPENAI_*, OLLAMA_*) so one .env works for both.
"""
import os
from typing import Any, Optional

# Ollama can be slow; use a long timeout so follow-up/today prompts don't fail.
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))

_raw = (os.getenv("LLM_PROVIDER") or "").strip().lower()
if _raw in ("openai", "ollama"):
    LLM_PROVIDER = _raw
else:
    _base = os.getenv("OLLAMA_BASE_URL") or os.getenv("OPENAI_BASE_URL") or ""
    if "11434" in _base or os.getenv("OLLAMA_BASE_URL"):
        LLM_PROVIDER = "ollama"
    elif os.getenv("OPENAI_API_KEY"):
        LLM_PROVIDER = "openai"
    else:
        LLM_PROVIDER = "openai"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "tinyllama")


def is_available() -> bool:
    if LLM_PROVIDER == "ollama":
        return True
    if LLM_PROVIDER == "openai":
        return bool(OPENAI_API_KEY)
    return False


def get_client():
    from openai import OpenAI
    if LLM_PROVIDER == "ollama":
        return OpenAI(api_key="ollama", base_url=OLLAMA_BASE_URL, timeout=OLLAMA_TIMEOUT)
    if LLM_PROVIDER == "openai":
        if OPENAI_BASE_URL:
            return OpenAI(api_key=OPENAI_API_KEY or "ollama", base_url=OPENAI_BASE_URL)
        return OpenAI(api_key=OPENAI_API_KEY)
    return OpenAI(api_key=OPENAI_API_KEY or "ollama", base_url=OPENAI_BASE_URL or None)


def get_model() -> str:
    if LLM_PROVIDER == "ollama":
        return OLLAMA_MODEL
    return OPENAI_MODEL


def chat(messages: list[dict[str, str]], max_tokens: int = 80, **kwargs: Any) -> Optional[str]:
    if not is_available():
        return None
    try:
        client = get_client()
        r = client.chat.completions.create(
            model=get_model(),
            messages=messages,
            max_tokens=max_tokens,
            **kwargs,
        )
        text = (r.choices[0].message.content or "").strip()
        return text if text else None
    except Exception:
        return None
