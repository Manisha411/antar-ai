"""
Emotion tags: map entry content to a fixed taxonomy (1-3 emotions per entry).
Keyword-based; can be extended with LLM for richer detection.
"""
EMOTION_TAXONOMY = [
    "anxious", "sad", "frustrated", "grateful", "calm", "hopeful", "tired", "content",
]

# Keywords (lowercase) -> emotion. One word can map to multiple emotions.
KEYWORD_TO_EMOTIONS: dict[str, list[str]] = {
    "anxious": ["anxious"],
    "anxiety": ["anxious"],
    "worried": ["anxious"],
    "worry": ["anxious"],
    "nervous": ["anxious"],
    "stress": ["anxious"],
    "stressed": ["anxious"],
    "overwhelm": ["anxious"],
    "overwhelmed": ["anxious"],
    "sad": ["sad"],
    "sadness": ["sad"],
    "depressed": ["sad"],
    "lonely": ["sad"],
    "down": ["sad"],
    "unhappy": ["sad"],
    "grief": ["sad"],
    "frustrated": ["frustrated"],
    "frustration": ["frustrated"],
    "angry": ["frustrated"],
    "anger": ["frustrated"],
    "annoyed": ["frustrated"],
    "irritated": ["frustrated"],
    "stuck": ["frustrated"],
    "grateful": ["grateful"],
    "gratitude": ["grateful"],
    "thankful": ["grateful"],
    "thanks": ["grateful"],
    "appreciate": ["grateful"],
    "blessed": ["grateful"],
    "calm": ["calm"],
    "peaceful": ["calm"],
    "peace": ["calm"],
    "relaxed": ["calm"],
    "serene": ["calm"],
    "hopeful": ["hopeful"],
    "hope": ["hopeful"],
    "optimistic": ["hopeful"],
    "excited": ["hopeful"],
    "looking forward": ["hopeful"],
    "tired": ["tired"],
    "exhausted": ["tired"],
    "drained": ["tired"],
    "sleepy": ["tired"],
    "rest": ["tired"],
    "content": ["content"],
    "happy": ["content"],
    "joy": ["content"],
    "satisfied": ["content"],
    "good": ["content"],
    "fine": ["content"],
    "okay": ["content"],
    "ok": ["content"],
}


def compute_emotions(content: str) -> list[str]:
    """
    Return 1-3 emotions from the fixed taxonomy based on keyword presence.
    Deduplicates and limits to 3.
    """
    if not content or not content.strip():
        return []
    seen: set[str] = set()
    result: list[str] = []
    lower = content.lower()
    words = lower.replace(".", " ").replace(",", " ").split()
    # Also check 2-grams for phrases like "looking forward"
    for emotion, keywords in [
        ("anxious", ["anxious", "anxiety", "worried", "worry", "nervous", "stress", "stressed", "overwhelm", "overwhelmed"]),
        ("sad", ["sad", "sadness", "depressed", "lonely", "down", "unhappy", "grief"]),
        ("frustrated", ["frustrated", "frustration", "angry", "anger", "annoyed", "irritated", "stuck"]),
        ("grateful", ["grateful", "gratitude", "thankful", "thanks", "appreciate", "blessed"]),
        ("calm", ["calm", "peaceful", "peace", "relaxed", "serene"]),
        ("hopeful", ["hopeful", "hope", "optimistic", "excited", "looking forward"]),
        ("tired", ["tired", "exhausted", "drained", "sleepy", "rest"]),
        ("content", ["content", "happy", "joy", "satisfied", "good", "fine", "okay", "ok"]),
    ]:
        if emotion in seen:
            continue
        for kw in keywords:
            if kw in lower or kw in words:
                seen.add(emotion)
                result.append(emotion)
                break
        if len(result) >= 3:
            break
    return result[:3]
