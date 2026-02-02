"""
Prompt Service: returns a context-aware "today" prompt for journaling.
Fetches recent entries from Journal Service and uses LLM (or fallback) to generate one prompt.
"""
import os
import random
import re
from typing import Optional

import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from llm import chat as llm_chat, is_available as llm_available

app = FastAPI(title="Prompt Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOURNAL_SERVICE_URL = os.getenv("JOURNAL_SERVICE_URL", "http://localhost:8080")


class PromptResponse(BaseModel):
    prompt: str


class SuggestionsResponse(BaseModel):
    suggestions: list[str]


SUGGESTION_PROMPTS = [
    "What's one thing you're grateful for right now?",
    "What was today's win?",
    "One worry to let go of.",
    "How did you find moments of calm today?",
    "What would you like to reflect on today?",
]

FOLLOW_UP_PROMPTS = [
    "How did that make you feel?",
    "What would help you tomorrow?",
    "Anything else on your mind?",
    "What's one small step you could take from here?",
]

def fallback_follow_up(last_entry: str) -> str:
    """Context-aware follow-up without LLM: pick one question based on keywords in the entry."""
    pair = _fallback_follow_up_pair(last_entry)
    return pair[0] if pair else random.choice(FOLLOW_UP_PROMPTS)


def _fallback_follow_up_pair(last_entry: str) -> Optional[list[str]]:
    """Return 2 context-aware follow-ups for the entry (different angles), or None."""
    if not last_entry or not last_entry.strip():
        return None
    content = last_entry.lower().strip()[:800]
    if any(w in content for w in ["stress", "stressed", "overwhelm", "anxious", "worried", "work pressure"]):
        return ["How did you find moments of calm today?", "What one thing at work could you do differently tomorrow?"]
    if any(w in content for w in ["angry", "frustrated", "annoyed", "mad"]):
        return ["What would help you feel a bit lighter about that?", "What's one small step you could take from here?"]
    if any(w in content for w in ["sad", "down", "lonely", "miss"]):
        return ["What's one small thing that could bring you comfort?", "Who could you reach out to today?"]
    if any(w in content for w in ["grateful", "thankful", "good", "happy", "relieved"]):
        return ["What's one more thing you're grateful for right now?", "How did it feel to be heard?"]
    if any(w in content for w in ["sleep", "tired", "exhausted", "rest"]):
        return ["How are you feeling after rest (or lack of it)?", "What would help you wind down tonight?"]
    if any(w in content for w in ["trip", "travel", "vacation", "holiday", "europe", "traveling", "getaway"]):
        return ["What's one thing you're most looking forward to about the trip?", "Which place do you want to see first?"]
    if any(w in content for w in ["tomorrow", "next step", "goal"]):
        return ["What's one small step you could take from here?", "What would make tomorrow a bit better?"]
    return None


def get_recent_entries(token: str, limit: int = 10) -> list[dict]:
    """Fetch recent entries from Journal Service."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if not token:
        return []
    try:
        r = httpx.get(
            f"{JOURNAL_SERVICE_URL}/api/v1/entries/recent",
            params={"limit": limit},
            headers=headers,
            timeout=10.0,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def generate_prompt_with_llm(entries: list[dict]) -> Optional[str]:
    """
    Pre-entry nudge: suggest a prompt that references something they've written about
    often (e.g. "You've mentioned work a few times this week. Want to write about how it felt today?").
    """
    if not llm_available() or not entries:
        return None
    snippets = [
        (e.get("content", "")[:200] + "..." if len(e.get("content", "")) > 200 else e.get("content", ""))
        for e in entries[:7]
    ]
    context = "\n".join(f"- {s}" for s in snippets if s)
    text = llm_chat(
        messages=[
            {
                "role": "system",
                "content": """You suggest a short pre-entry nudge for journaling. The user will paste their recent journal entries (this week). Your job is to suggest ONE short prompt that:
1) References something they've written about more than once (e.g. work, family, stress, sleep, a trip, a person).
2) Invites them to write about it today. Example: "You've mentioned work a few times this week. Want to write about how it felt today?" or "Family has come up in your entries. How did it feel to spend time with them today?"
3) Sounds like a caring nudge, not a command. Under 20 words.
Output ONLY the nudge. No quotes, no preamble.""",
            },
            {"role": "user", "content": f"Recent entries:\n{context}" if context else "No entries yet."},
        ],
        max_tokens=60,
    )
    return text.strip() if text else None


def _recurring_theme_nudge(entries: list[dict]) -> Optional[str]:
    """Build a nudge from recurring themes in recent entries (no LLM). E.g. 'You've mentioned work a few times recently. Want to write about how it felt today?'"""
    if not entries or len(entries) < 2:
        return None
    recent = entries[:7]
    def entries_mention(*words):
        return sum(1 for e in recent if any(w in ((e.get("content") or "").lower()) for w in words)) >= 2
    if entries_mention("work", "job", "boss", "meeting"):
        return "You've mentioned work a few times recently. Want to write about how it felt today?"
    if entries_mention("stress", "stressed", "overwhelm"):
        return "You've written about stress lately. Want to write about how it felt today?"
    if entries_mention("family", "kids", "child", "parent"):
        return "Family has come up in your entries. How did it feel to spend time with them today?"
    if entries_mention("sleep", "tired", "rest", "exhausted"):
        return "You've mentioned sleep or tiredness recently. Want to write about how you're resting?"
    if entries_mention("trip", "travel", "vacation", "europe"):
        return "You've been writing about the trip. What are you most looking forward to?"
    if entries_mention("grateful", "thankful", "happy"):
        return "You've written about gratitude lately. What's one thing you're grateful for right now?"
    return None


def fallback_prompt(entries: list[dict]) -> str:
    """Generate a context-aware prompt from recent entries (nudge style when possible, no LLM)."""
    if not entries:
        return "What's on your mind today?"
    nudge = _recurring_theme_nudge(entries)
    if nudge:
        return nudge
    content = " ".join(e.get("content", "") for e in entries[:5]).lower()
    if any(w in content for w in ["stress", "stressed", "work", "busy", "overwhelm"]):
        return "How did you find moments of calm today?"
    if any(w in content for w in ["grateful", "thank", "good", "happy"]):
        return "What's one thing you're grateful for right now?"
    if any(w in content for w in ["sleep", "tired", "rest"]):
        return "How are you feeling after rest (or lack of it)?"
    return "What would you like to reflect on today?"


@app.get("/api/v1/prompts/today", response_model=PromptResponse)
def get_today_prompt(authorization: Optional[str] = Header(None)):
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Authorization required")
    entries = get_recent_entries(token)
    prompt = generate_prompt_with_llm(entries)
    if not prompt:
        prompt = fallback_prompt(entries)
    # Sanitize: single line, no extra quotes
    prompt = re.sub(r"\s+", " ", prompt).strip()
    return PromptResponse(prompt=prompt)


@app.get("/api/v1/prompts/suggestions", response_model=SuggestionsResponse)
def get_suggestions(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        pass
    else:
        raise HTTPException(status_code=401, detail="Authorization required")
    return SuggestionsResponse(suggestions=SUGGESTION_PROMPTS[:5])


def get_contextual_follow_ups(last_entry: str, count: int = 2) -> list[str]:
    """
    Return 2 conversational, context-aware follow-up prompts based on what the user wrote.
    Uses the LLM when available; fills with keyword-based fallback when needed.
    """
    if not last_entry or not last_entry.strip():
        return [random.choice(FOLLOW_UP_PROMPTS) for _ in range(count)]
    snippet = (last_entry[:800] + "...") if len(last_entry) > 800 else last_entry
    pair = _fallback_follow_up_pair(last_entry)
    fallback_one = pair[0] if pair else random.choice(FOLLOW_UP_PROMPTS)
    fallback_two = pair[1] if pair and len(pair) > 1 else random.choice([p for p in FOLLOW_UP_PROMPTS if p != fallback_one] or FOLLOW_UP_PROMPTS)
    if not llm_available():
        return [fallback_one, fallback_two]
    system = """You suggest the next journal prompts. The user will paste their last journal entry. Reply with exactly TWO short follow-up questions (each under 15 words) that:
1) Refer to something SPECIFIC they wrote (e.g. work, trip, family, sleep, a person, a worry).
2) Could only make sense if you read their entry (no generic questions like "How did that make you feel?").
3) Are different angles (e.g. one about feeling, one about action or next step).

Format: output exactly two lines. Line 1: first question. Line 2: second question. No numbering, no quotes, no preamble."""
    user_content = f"""Their journal entry:

---
{snippet}
---

Write TWO short follow-up questions (different angles) that refer to something specific in the entry above. One per line."""
    text = llm_chat(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        max_tokens=100,
    )
    if not text or not text.strip():
        return [fallback_one, fallback_two]
    lines = [ln.strip() for ln in text.strip().split("\n") if ln.strip()]
    # Remove leading "1." "2." or "-" if present
    cleaned = []
    for ln in lines:
        ln = re.sub(r"^[\d]+[\.\)]\s*", "", ln).strip()
        ln = re.sub(r"^[-–—]\s*", "", ln).strip()
        if ln and len(ln) > 5:
            cleaned.append(ln)
    if len(cleaned) >= 2:
        return cleaned[:2]
    if len(cleaned) == 1:
        return [cleaned[0], fallback_one if cleaned[0] != fallback_one else fallback_two]
    return [fallback_one, fallback_two]


def _follow_up_prompts(last_entry: Optional[str]) -> list[str]:
    if last_entry and last_entry.strip():
        return get_contextual_follow_ups(last_entry.strip(), 2)
    return [random.choice(FOLLOW_UP_PROMPTS), random.choice(FOLLOW_UP_PROMPTS)]


class FollowUpResponse(BaseModel):
    prompt: Optional[str] = None  # first prompt, for backward compat
    prompts: list[str] = []  # 2 reflection prompts


@app.get("/api/v1/prompts/follow-up", response_model=FollowUpResponse)
def get_follow_up(
    authorization: Optional[str] = Header(None),
    last_entry: Optional[str] = None,
):
    if authorization and authorization.startswith("Bearer "):
        pass
    else:
        raise HTTPException(status_code=401, detail="Authorization required")
    prompts = _follow_up_prompts(last_entry)
    return FollowUpResponse(prompt=prompts[0] if prompts else None, prompts=prompts[:2])


class FollowUpRequest(BaseModel):
    last_entry: Optional[str] = None


@app.post("/api/v1/prompts/follow-up", response_model=FollowUpResponse)
def post_follow_up(authorization: Optional[str] = Header(None), body: Optional[FollowUpRequest] = None):
    if authorization and authorization.startswith("Bearer "):
        pass
    else:
        raise HTTPException(status_code=401, detail="Authorization required")
    last = (body.last_entry if body else None) or ""
    prompts = _follow_up_prompts(last)
    return FollowUpResponse(prompt=prompts[0] if prompts else None, prompts=prompts[:2])


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
