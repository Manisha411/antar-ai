"""Theme extraction: simple keyword extraction (meaningful words). Optional OpenAI."""
import re
from collections import Counter
from llm import get_client, get_model, is_available

STOP = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "as", "is", "was", "are", "were", "been", "be", "have",
    "has", "had", "do", "does", "did", "will", "would", "could", "should", "may",
    "might", "must", "can", "this", "that", "these", "those", "i", "you", "he",
    "she", "it", "we", "they", "my", "your", "his", "her", "its", "our", "their",
    "me", "him", "them", "what", "which", "who", "when", "where", "why", "how",
    "all", "each", "every", "both", "few", "more", "most", "other", "some",
    "than", "too", "very", "just", "so", "if", "then", "than", "into", "out",
}

# Reject LLM output that looks like prose or instructions instead of short tags
LLM_JUNK_PHRASES = (
    "here are", "recommend", "comma-separated", "e.g.", "short theme",
    "journal entry", "reply as", "include", "tags that", "could be", "such as",
)


def extract_themes_simple(content: str, top_n: int = 5) -> list[str]:
    content_lower = re.sub(r"[^a-z\s]", " ", content.lower())
    words = [w for w in content_lower.split() if len(w) > 2 and w not in STOP]
    if not words:
        return []
    counts = Counter(words)
    return [w for w, _ in counts.most_common(top_n)]


def extract_themes_openai(content: str, top_n: int = 5) -> list[str] | None:
    if not is_available() or len(content) > 2000:
        return None
    try:
        client = get_client()
        r = client.chat.completions.create(
            model=get_model(),
            messages=[
                {"role": "system", "content": f"List up to {top_n} short theme tags (1-3 words each) for this journal entry. Reply as comma-separated values only, e.g. work stress, family, gratitude."},
                {"role": "user", "content": content[:2000]},
            ],
            max_tokens=80,
        )
        text = (r.choices[0].message.content or "").strip()
        raw = [t.strip() for t in text.split(",") if t.strip()]
        themes = []
        for t in raw:
            if len(themes) >= top_n:
                break
            t = t.strip().strip('"').strip()
            if len(t) > 45 or len(t) < 2:
                continue
            lower = t.lower()
            if any(lower.startswith(f"{i}.") or lower.startswith(f"{i})") for i in range(10)):
                continue
            if any(phrase in lower for phrase in LLM_JUNK_PHRASES):
                continue
            if t.count(" ") > 4:
                continue
            if lower in STOP:
                continue
            themes.append(t)
        if themes:
            return themes
    except Exception:
        pass
    return None


def extract_themes(content: str, top_n: int = 5) -> list[str]:
    out = extract_themes_openai(content, top_n) if is_available() else None
    if out:
        return out
    return extract_themes_simple(content, top_n)
