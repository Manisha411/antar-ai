"""
One-line reflection per entry: short, empathetic sentence from LLM.
Uses only the entry text so the model doesn't echo metadata. Non-judgmental.
"""
import re
from typing import Optional

from llm import chat, is_available

# Reject reflections that look like metadata, instructions, or are too long.
BAD_PATTERNS = re.compile(
    r"sentiment|label\s*negative|label\s*positive|theme\s*:|themes?:|entry\s*\(|"
    r"here are|comma-separated|short theme tags|response:|dear readers|"
    r"research has shown|thank you for your inquiry",
    re.IGNORECASE,
)
MAX_REFLECTION_WORDS = 25


def _is_valid_reflection(text: str) -> bool:
    """True if the response looks like one short empathetic sentence, not metadata or garbage."""
    if not text or len(text) < 5:
        return False
    t = text.strip()
    if BAD_PATTERNS.search(t):
        return False
    words = len(t.split())
    if words > MAX_REFLECTION_WORDS:
        return False
    # Should look like a sentence, not a list or label
    if t.startswith("(") or "1." in t[:20] or "Entry (" in t:
        return False
    return True


def generate_reflection(
    content: str,
    score: float,
    label: Optional[str],
    themes: list[str],
    openai_api_key: Optional[str] = None,  # ignored; kept for API compat
) -> Optional[str]:
    """
    Return one short empathetic sentence, or None if no LLM or invalid response.
    We send only the entry text (no sentiment/themes) so the model doesn't echo our metadata.
    """
    if not is_available() or not content or not content.strip():
        return None
    snippet = (content[:300] + "...") if len(content) > 300 else content
    raw = chat(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an empathetic journaling assistant. The user will share a short journal entry. "
                    "Reply with ONLY one short, warm sentence (under 15 words) that acknowledges what they wrote. "
                    "Examples: 'That sounds exhausting.' 'A moment of calm.' 'Glad you had that time with them.' "
                    "Do NOT output sentiment, labels, themes, lists, or multiple sentences. No quotes. No preamble."
                ),
            },
            {
                "role": "user",
                "content": snippet,
            },
        ],
        max_tokens=40,
    )
    if raw and _is_valid_reflection(raw):
        return raw.strip()
    return None
