"""Simple sentiment: keyword-based score in [-1, 1]. Optional OpenAI for better accuracy."""
import re
from llm import get_client, get_model, is_available

NEGATIVE_WORDS = {
    "stress", "stressed", "anxious", "sad", "angry", "tired", "worried", "frustrated",
    "overwhelm", "bad", "hard", "difficult", "hate", "fail", "failed", "lonely",
    "scared", "afraid", "guilty", "ashamed", "hopeless", "exhausted",
}
POSITIVE_WORDS = {
    "happy", "calm", "grateful", "peaceful", "joy", "good", "great", "love", "loved",
    "thankful", "relaxed", "energized", "hopeful", "proud", "excited", "relief",
    "better", "peace", "content", "blessed", "wonderful", "amazing",
}


def compute_sentiment_simple(content: str) -> tuple[float, str]:
    content_lower = re.sub(r"[^a-z\s]", " ", content.lower())
    words = set(content_lower.split())
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    total = pos + neg
    if total == 0:
        return 0.0, "neutral"
    score = (pos - neg) / total
    score = max(-1.0, min(1.0, score))
    if pos >= 1 and neg >= 1:
        label = "mixed"
    elif score > 0.2:
        label = "positive"
    elif score < -0.2:
        label = "negative"
    else:
        label = "neutral"
    return round(score, 3), label


def compute_sentiment_openai(content: str) -> tuple[float, str] | None:
    if not is_available() or len(content) > 2000:
        return None
    try:
        client = get_client()
        r = client.chat.completions.create(
            model=get_model(),
            messages=[
                {"role": "system", "content": "Reply with only a number from -1 to 1 (sentiment: -1=very negative, 0=neutral, 1=very positive) and one word: positive, negative, neutral, or mixed. Use mixed when the entry clearly has both positive and negative emotions (e.g. bittersweet). Format: score label e.g. 0.5 positive"},
                {"role": "user", "content": content[:2000]},
            ],
            max_tokens=20,
        )
        raw = (r.choices[0].message.content or "").strip()
        parts = raw.split()
        if len(parts) >= 2:
            score = float(parts[0])
            label = parts[1].lower() if parts[1].lower() in ("positive", "negative", "neutral", "mixed") else "neutral"
            return max(-1, min(1, score)), label
    except Exception:
        pass
    return None


def compute_sentiment(content: str) -> tuple[float, str]:
    out = compute_sentiment_openai(content) if is_available() else None
    if out is not None:
        return out
    return compute_sentiment_simple(content)
