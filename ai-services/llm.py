"""
Generic LLM layer: use any OpenAI-compatible provider (OpenAI, Ollama, Groq, etc.).
Configure via LLM_PROVIDER and provider-specific env vars.

To add a new provider (e.g. groq): add a branch in get_client(), get_model(), and
is_available(), and set env vars (e.g. GROQ_API_KEY, GROQ_BASE_URL). Same OpenAI
client works for any endpoint that speaks the OpenAI chat completions API.
"""
import os
from typing import Any, Optional

# Ollama can be slow (e.g. weekly summary); use a long timeout so requests don't fail mid-stream.
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))

# --- Provider selection ---
# LLM_PROVIDER=openai | ollama (future: groq, gemini, ...)
_raw = (os.getenv("LLM_PROVIDER") or "").strip().lower()
if _raw in ("openai", "ollama"):
    LLM_PROVIDER = _raw
else:
    # Auto-detect: Ollama if base URL points to Ollama, else OpenAI if key set
    _base = os.getenv("OLLAMA_BASE_URL") or os.getenv("OPENAI_BASE_URL") or ""
    if "11434" in _base or os.getenv("OLLAMA_BASE_URL"):
        LLM_PROVIDER = "ollama"
    elif os.getenv("OPENAI_API_KEY"):
        LLM_PROVIDER = "openai"
    else:
        LLM_PROVIDER = "openai"  # default name; is_available() will be False if no key

# --- Provider config (extend when adding new providers) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # optional, e.g. for Groq
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "tinyllama")


def is_available() -> bool:
    """True if an LLM backend is configured and usable."""
    if LLM_PROVIDER == "ollama":
        return True  # Ollama doesn't need a key; we just need the server
    if LLM_PROVIDER == "openai":
        return bool(OPENAI_API_KEY)
    return False


def get_client(timeout: Optional[float] = None):
    """Return an OpenAI-compatible client for the configured provider."""
    from openai import OpenAI
    if LLM_PROVIDER == "ollama":
        return OpenAI(api_key="ollama", base_url=OLLAMA_BASE_URL, timeout=timeout or OLLAMA_TIMEOUT)
    if LLM_PROVIDER == "openai":
        if OPENAI_BASE_URL:
            return OpenAI(api_key=OPENAI_API_KEY or "ollama", base_url=OPENAI_BASE_URL)
        return OpenAI(api_key=OPENAI_API_KEY)
    # Fallback for unknown provider
    return OpenAI(api_key=OPENAI_API_KEY or "ollama", base_url=OPENAI_BASE_URL or None)


def get_model() -> str:
    """Return the model name to use for chat completions."""
    if LLM_PROVIDER == "ollama":
        return OLLAMA_MODEL
    return OPENAI_MODEL


def chat(
    messages: list[dict[str, str]],
    max_tokens: int = 80,
    timeout: Optional[float] = None,
    **kwargs: Any,
) -> Optional[str]:
    """
    Single entry point for chat completion. Uses configured provider and model.
    Returns the assistant message content or None on failure or timeout.
    When timeout is set (e.g. 90), the call gives up after that many seconds (useful for
    weekly summary with Ollama so we can fall back to instant non-LLM summary).
    """
    if not is_available():
        return None
    try:
        client = get_client(timeout=timeout)
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
