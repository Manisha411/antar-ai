"""
Summary Service: Generate weekly/monthly reflection summaries from sentiment + themes.
Reflection summaries: reflect patterns, describe (not diagnose), highlight awareness (not advice).
API: GET /api/v1/summaries/latest, GET /api/v1/summaries/weekly, daily, monthly.
"""
import json
import os
from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config import ANALYTICS_DB_URL
from llm import chat, is_available
from db import init_db, ReflectionSummary

JWT_SECRET = os.getenv("JWT_SECRET", "your-256-bit-secret-for-jwt-signing-change-in-production")

engine = create_engine(ANALYTICS_DB_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Summary Service", version="1.0.0", lifespan=lifespan)
# Use specific origins so credentials (Authorization header) work; * is not allowed with credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_user_id(authorization: Optional[str] = None, x_user_id: Optional[str] = None) -> str:
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        if token and token != "undefined" and token != "null":
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], options={"verify_exp": True})
                if payload.get("sub"):
                    return str(payload["sub"])
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=401,
                    detail="Token expired. Sign out and sign in again.",
                )
            except jwt.InvalidTokenError:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token. Ensure JWT_SECRET is the same for Auth and Summary services.",
                )
    if x_user_id and x_user_id.strip():
        return x_user_id.strip()
    raise HTTPException(
        status_code=401,
        detail="Authorization required. Send Bearer token or set JWT_SECRET to match Auth service.",
    )


class SummaryResponse(BaseModel):
    summary: str
    period_start: str
    period_end: str
    generated_at: str
    sections: Optional[dict[str, Any]] = None  # structured weekly/monthly: header, emotional_snapshot, recurring_themes, etc.


# Junk / prose themes to exclude from reflection text
_SUMMARY_STOP = {"here are", "recommend", "could be", "e.g.", "such as", "short theme", "journal entry", "words)", "word)"}


def _shorten_theme(t: str, max_words: int = 4, max_chars: int = 28) -> str:
    """One short label for summary use (e.g. 'work stress' not long prose)."""
    s = (t or "").strip()
    if not s:
        return ""
    words = s.split()
    out = " ".join(words[:max_words])
    if len(out) > max_chars:
        out = out[: max_chars - 1].rsplit(" ", 1)[0] or out[:max_chars]
    return out.strip() or s[:max_chars]


def clean_themes_for_summary(themes: list[str]) -> list[str]:
    """Filter and shorten themes so summaries read naturally, not theme dumps."""
    seen: set[str] = set()
    out: list[str] = []
    for t in themes or []:
        if not t or not isinstance(t, str):
            continue
        s = t.strip()
        if len(s) < 2 or len(s) > 60:
            continue
        lower = s.lower()
        if any(lower.startswith(f"{i}.") or lower.startswith(f"{i})") for i in range(10)):
            s = s.lstrip("0123456789.) ").strip()
        if any(phrase in lower for phrase in _SUMMARY_STOP):
            continue
        short = _shorten_theme(s)
        if short and short.lower() not in seen:
            seen.add(short.lower())
            out.append(short)
    return out[:12]


def get_theme_sentiment_buckets(session, user_id: str, start_dt: datetime, end_dt: datetime) -> tuple[list[str], list[str]]:
    """Return (low_themes, high_themes) for the date range. Low = score < -0.2, high = score > 0.2."""
    result = session.execute(
        text("""
            WITH themed AS (
                SELECT tr.entry_id, sr.score, jsonb_array_elements_text(tr.themes) AS theme
                FROM theme_result tr
                JOIN sentiment_result sr ON tr.entry_id = sr.entry_id AND tr.user_id = sr.user_id
                WHERE tr.user_id = :uid AND tr.computed_at >= :start_dt AND tr.computed_at <= :end_dt
            )
            SELECT theme,
                CASE WHEN score < -0.2 THEN 'low' WHEN score > 0.2 THEN 'high' ELSE NULL END AS bucket
            FROM themed
        """),
        {"uid": user_id, "start_dt": start_dt, "end_dt": end_dt},
    )
    rows = result.fetchall()
    low_set: set[str] = set()
    high_set: set[str] = set()
    for theme, bucket in rows:
        if theme and bucket:
            if bucket == "low":
                low_set.add(theme)
            elif bucket == "high":
                high_set.add(theme)
    return (sorted(low_set), sorted(high_set))


def get_top_emotions(session, user_id: str, start_dt: datetime, end_dt: datetime, limit: int = 5) -> list[str]:
    """Return most frequent emotions in the date range."""
    result = session.execute(
        text("""
            SELECT emotions FROM sentiment_result
            WHERE user_id = :uid AND computed_at >= :start_dt AND computed_at <= :end_dt
              AND emotions IS NOT NULL
              AND CASE WHEN jsonb_typeof(emotions) = 'array' THEN jsonb_array_length(emotions) > 0 ELSE false END
        """),
        {"uid": user_id, "start_dt": start_dt, "end_dt": end_dt},
    )
    counter: Counter[str] = Counter()
    for (emotions_json,) in result.fetchall():
        if emotions_json and isinstance(emotions_json, list):
            for e in emotions_json:
                if isinstance(e, str):
                    counter[e] += 1
    return [emotion for emotion, _ in counter.most_common(limit)]


DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_daily_sentiment_week(session, user_id: str, start_dt: datetime, end_dt: datetime) -> list[tuple[str, float]]:
    """Daily (date, avg score) for trend slope. Uses computed_at date in UTC."""
    result = session.execute(
        text("""
            SELECT DATE(computed_at) AS d, AVG(score) AS avg_score
            FROM sentiment_result
            WHERE user_id = :uid AND computed_at >= :start_dt AND computed_at <= :end_dt
            GROUP BY DATE(computed_at)
            ORDER BY d
        """),
        {"uid": user_id, "start_dt": start_dt, "end_dt": end_dt},
    )
    return [(str(row[0]), float(row[1])) for row in result.fetchall()]


def get_theme_counts_with_days(
    session, user_id: str, start_dt: datetime, end_dt: datetime
) -> list[tuple[str, int, list[str]]]:
    """(theme, count, list of day names) for recurring themes. Only themes with count >= 2."""
    result = session.execute(
        text("""
            SELECT jsonb_array_elements_text(tr.themes) AS theme, DATE(tr.computed_at) AS d
            FROM theme_result tr
            WHERE tr.user_id = :uid AND tr.computed_at >= :start_dt AND tr.computed_at <= :end_dt
        """),
        {"uid": user_id, "start_dt": start_dt, "end_dt": end_dt},
    )
    theme_to_dates: dict[str, list[datetime]] = {}
    for theme, d in result.fetchall():
        if not theme or not isinstance(d, datetime):
            continue
        t = _shorten_theme(theme.strip())
        if not t or len(t) > 40:
            continue
        theme_to_dates.setdefault(t, []).append(d)
    out: list[tuple[str, int, list[str]]] = []
    for theme, dates in sorted(theme_to_dates.items(), key=lambda x: -len(x[1]))[:10]:
        if len(dates) < 2:
            continue
        day_names = list({DAY_NAMES[d.weekday()] for d in dates})
        out.append((theme, len(dates), sorted(day_names, key=lambda d: DAY_NAMES.index(d))))
    return out


def get_gentle_connection(
    session, user_id: str, start_dt: datetime, end_dt: datetime
) -> Optional[tuple[str, str]]:
    """One strong correlation: (theme, 'high'|'low') when theme appears mostly on high- or low-sentiment days."""
    result = session.execute(
        text("""
            WITH themed AS (
                SELECT tr.entry_id, sr.score, jsonb_array_elements_text(tr.themes) AS theme
                FROM theme_result tr
                JOIN sentiment_result sr ON tr.entry_id = sr.entry_id AND tr.user_id = sr.user_id
                WHERE tr.user_id = :uid AND tr.computed_at >= :start_dt AND tr.computed_at <= :end_dt
            )
            SELECT theme,
                SUM(CASE WHEN score > 0.2 THEN 1 ELSE 0 END)::int AS high_days,
                SUM(CASE WHEN score < -0.2 THEN 1 ELSE 0 END)::int AS low_days,
                COUNT(*)::int AS total
            FROM themed
            GROUP BY theme
            HAVING COUNT(*) >= 2
        """),
        {"uid": user_id, "start_dt": start_dt, "end_dt": end_dt},
    )
    for row in result.fetchall():
        theme, high_days, low_days, total = row[0], row[1] or 0, row[2] or 0, row[3] or 0
        if not theme:
            continue
        t = _shorten_theme((theme or "").strip())
        if not t or len(t) > 35:
            continue
        if total < 2:
            continue
        if high_days and high_days >= total * 0.6 and low_days <= 1:
            return (t, "high")
        if low_days and low_days >= total * 0.6 and high_days <= 1:
            return (t, "low")
    return None


def get_weekly_sentiment_month(session, user_id: str, start_dt: datetime, end_dt: datetime) -> list[tuple[int, float]]:
    """(week_index_0_to_3, avg_score) for 4 weeks. Week 0 = first 7 days."""
    result = session.execute(
        text("""
            SELECT FLOOR(EXTRACT(EPOCH FROM (computed_at - :start_dt)) / (7 * 86400))::int AS wk, AVG(score)
            FROM sentiment_result
            WHERE user_id = :uid AND computed_at >= :start_dt AND computed_at <= :end_dt
            GROUP BY FLOOR(EXTRACT(EPOCH FROM (computed_at - :start_dt)) / (7 * 86400))
            ORDER BY wk
        """),
        {"uid": user_id, "start_dt": start_dt, "end_dt": end_dt},
    )
    return [(int(row[0]), float(row[1])) for row in result.fetchall()]


def get_sentiment_variance(session, user_id: str, start_dt: datetime, end_dt: datetime) -> Optional[float]:
    """Std dev of daily scores (or None)."""
    result = session.execute(
        text("""
            SELECT AVG(score), STDDEV(score) FROM sentiment_result
            WHERE user_id = :uid AND computed_at >= :start_dt AND computed_at <= :end_dt
        """),
        {"uid": user_id, "start_dt": start_dt, "end_dt": end_dt},
    )
    row = result.fetchone()
    if row and row[1] is not None:
        return float(row[1])
    return None


def get_theme_evolution(
    session, user_id: str, start_dt: datetime, end_dt: datetime
) -> list[tuple[str, str]]:
    """(theme, 'early'|'late'|'steady') based on first half vs second half frequency."""
    mid = start_dt + (end_dt - start_dt) / 2
    result1 = session.execute(
        text("""
            SELECT jsonb_array_elements_text(themes) AS theme FROM theme_result
            WHERE user_id = :uid AND computed_at >= :start_dt AND computed_at < :mid
        """),
        {"uid": user_id, "start_dt": start_dt, "mid": mid},
    )
    first_half: Counter[str] = Counter()
    for (t,) in result1.fetchall():
        if t:
            first_half[_shorten_theme(t.strip())] += 1
    result2 = session.execute(
        text("""
            SELECT jsonb_array_elements_text(themes) AS theme FROM theme_result
            WHERE user_id = :uid AND computed_at >= :mid AND computed_at <= :end_dt
        """),
        {"uid": user_id, "mid": mid, "end_dt": end_dt},
    )
    second_half: Counter[str] = Counter()
    for (t,) in result2.fetchall():
        if t:
            second_half[_shorten_theme(t.strip())] += 1
    out: list[tuple[str, str]] = []
    all_themes = set(first_half) | set(second_half)
    for theme in list(all_themes)[:12]:
        if len(theme) > 40:
            continue
        a, b = first_half[theme], second_half[theme]
        if a + b < 2:
            continue
        if a >= 2 and b <= 1:
            out.append((theme, "early"))
        elif b >= 2 and a <= 1:
            out.append((theme, "late"))
        elif a >= 1 and b >= 1:
            out.append((theme, "steady"))
    return out[:5]


def generate_summary_llm(
    themes: list[str],
    sentiment_avg: float,
    period_label: str,
    low_themes: Optional[list[str]] = None,
    high_themes: Optional[list[str]] = None,
    top_emotions: Optional[list[str]] = None,
    max_sentences: int = 3,
) -> Optional[str]:
    """Generate a gentle 'connecting the dots' reflection: themes + patterns, non-judgmental."""
    if not is_available():
        return None
    theme_str = ", ".join(themes[:12]) if themes else "none yet"
    structure_parts = [f"Average sentiment (from -1 to 1): {sentiment_avg:.2f}."]
    if low_themes:
        structure_parts.append(f"Themes on tougher days: {', '.join(low_themes[:8])}.")
    if high_themes:
        structure_parts.append(f"Themes on brighter days: {', '.join(high_themes[:8])}.")
    if top_emotions:
        structure_parts.append(f"Frequent emotions: {', '.join(top_emotions[:5])}.")
    structure_str = " ".join(structure_parts)
    summary_timeout = float(os.getenv("SUMMARY_LLM_TIMEOUT", "90"))
    return chat(
        messages=[
            {
                "role": "system",
                "content": "You write a short reflection for the user based on their journal. Output only 2-4 plain sentences in second person (You...). Connect the dots in a gentle, non-judgmental way. Do NOT output numbered lists. Do NOT quote or list themes verbatim; weave topics into natural observations. Good: 'You seemed most energized when writing about time outdoors.' 'Work came up more on tougher days.' Bad: '1. Theme one 2. Theme two' or long theme dumps.",
            },
            {
                "role": "user",
                "content": f"Period: {period_label}. Topics: {theme_str}. {structure_str} Write the reflection.",
            },
        ],
        max_tokens=120,
        timeout=summary_timeout,
    )


def fallback_summary(
    themes: list[str],
    sentiment_avg: float,
    period_label: str,
    low_themes: Optional[list[str]] = None,
    high_themes: Optional[list[str]] = None,
    top_emotions: Optional[list[str]] = None,
) -> str:
    """Fallback when LLM is unavailable: short, natural connecting-the-dots sentences."""
    if not themes:
        return "Keep writing to get a reflection. Your entries are private and only you see these insights."
    topics = ", ".join(themes[:5])
    parts = [f"{period_label.capitalize()} you wrote about {topics}."]
    if high_themes:
        parts.append(f"You mentioned {', '.join(high_themes[:3])} more on brighter days.")
    if low_themes:
        parts.append(f"On tougher days, {', '.join(low_themes[:3])} came up more.")
    if top_emotions:
        parts.append(f"You often felt {', '.join(top_emotions[:5])}.")
    return " ".join(parts)


# --- Tone rules: describe, don't diagnose. "You often mentioned...", "It seems like...". Never "You should...", "You need to...". ---


def _format_date_range(start_dt: datetime, end_dt: datetime) -> str:
    s = f"{start_dt.strftime('%b')} {start_dt.day}"
    e = f"{end_dt.strftime('%b')} {end_dt.day}"
    if s == e:
        return s
    return f"{s}–{e}"


def build_weekly_sections(
    session,
    user_id: str,
    start_dt: datetime,
    end_dt: datetime,
) -> dict[str, Any]:
    """Structured weekly reflection: header, emotional_snapshot, recurring_themes, gentle_connections, reflection_prompt."""
    sentiment_avg_row = session.execute(
        text("SELECT AVG(score) FROM sentiment_result WHERE user_id = :uid AND computed_at >= :start_dt AND computed_at <= :end_dt"),
        {"uid": user_id, "start_dt": start_dt, "end_dt": end_dt},
    ).fetchone()
    sentiment_avg = float(sentiment_avg_row[0]) if sentiment_avg_row and sentiment_avg_row[0] is not None else 0.0
    daily = get_daily_sentiment_week(session, user_id, start_dt, end_dt)
    top_emotions = get_top_emotions(session, user_id, start_dt, end_dt)
    recurring = get_theme_counts_with_days(session, user_id, start_dt, end_dt)
    connection = get_gentle_connection(session, user_id, start_dt, end_dt)
    low_themes, high_themes = get_theme_sentiment_buckets(session, user_id, start_dt, end_dt)
    low_themes = clean_themes_for_summary(low_themes)
    high_themes = clean_themes_for_summary(high_themes)

    date_range_str = _format_date_range(start_dt, end_dt)
    header_title = "Your Week in Reflection"
    header_subtitle = f"Based on your journal entries from {date_range_str}"

    # Emotional snapshot (1–2 lines): trend + emotions. Describe, don't judge.
    if len(daily) >= 2:
        first_half_avg = sum(s for _, s in daily[: len(daily) // 2]) / max(1, len(daily) // 2)
        second_half_avg = sum(s for _, s in daily[len(daily) // 2 :]) / max(1, len(daily) - len(daily) // 2)
        trend = "improved" if second_half_avg > first_half_avg + 0.1 else "eased" if second_half_avg < first_half_avg - 0.1 else "steady"
    else:
        trend = "steady"
    if sentiment_avg > 0.2:
        snapshot = "This week leaned positive, with moments of calm."
    elif sentiment_avg < -0.2:
        snapshot = "This week leaned stressful at times; it might help to notice what brought relief."
    else:
        snapshot = "This week had a mix of ups and downs, with some steadiness in between."
    if top_emotions:
        emotion_str = ", ".join(top_emotions[:3])
        snapshot += f" You often noted: {emotion_str}."

    # Recurring themes (2–3 bullets): only themes that appear multiple times
    recurring_bullets: list[str] = []
    for theme, count, days in recurring[:3]:
        days_str = ", ".join(days[:3]) if days else ""
        if days_str:
            recurring_bullets.append(f"**{theme}** came up often, especially on {days_str}.")
        else:
            recurring_bullets.append(f"**{theme}** appeared several times this week.")

    # Gentle connection: one "tended to" observation when signal is strong
    gentle_connections = ""
    if connection:
        theme, bucket = connection
        if bucket == "high":
            gentle_connections = f"On days you mentioned {theme}, your entries tended to feel lighter."
        else:
            gentle_connections = f"When {theme} came up, your entries often reflected tougher moments."
    if not gentle_connections and high_themes:
        gentle_connections = f"You often mentioned {', '.join(high_themes[:2])} more on brighter days."

    # Reflection prompt: questions, not advice
    reflection_prompt = [
        "What helped you feel more at ease on those lighter days?",
        "Is there something from this week you'd like to carry into next week?",
    ]

    return {
        "header_title": header_title,
        "header_subtitle": header_subtitle,
        "emotional_snapshot": snapshot.strip(),
        "recurring_themes": recurring_bullets,
        "gentle_connections": gentle_connections.strip() or None,
        "reflection_prompt": reflection_prompt,
    }


def build_monthly_sections(
    session,
    user_id: str,
    start_dt: datetime,
    end_dt: datetime,
) -> dict[str, Any]:
    """Structured monthly reflection: header, overall_tone, theme_evolution, notable_patterns, progress_highlight, looking_ahead."""
    sentiment_avg_row = session.execute(
        text("SELECT AVG(score) FROM sentiment_result WHERE user_id = :uid AND computed_at >= :start_dt AND computed_at <= :end_dt"),
        {"uid": user_id, "start_dt": start_dt, "end_dt": end_dt},
    ).fetchone()
    sentiment_avg = float(sentiment_avg_row[0]) if sentiment_avg_row and sentiment_avg_row[0] is not None else 0.0
    variance = get_sentiment_variance(session, user_id, start_dt, end_dt)
    weekly_scores = get_weekly_sentiment_month(session, user_id, start_dt, end_dt)
    evolution = get_theme_evolution(session, user_id, start_dt, end_dt)
    low_themes, high_themes = get_theme_sentiment_buckets(session, user_id, start_dt, end_dt)
    low_themes = clean_themes_for_summary(low_themes)
    high_themes = clean_themes_for_summary(high_themes)
    top_emotions = get_top_emotions(session, user_id, start_dt, end_dt)

    month_str = start_dt.strftime("%B %Y")
    header_title = "Your Month in Reflection"
    header_subtitle = month_str

    # Overall tone
    if weekly_scores and len(weekly_scores) >= 2:
        first_avg = sum(s for _, s in weekly_scores[: len(weekly_scores) // 2]) / max(1, len(weekly_scores) // 2)
        last_avg = sum(s for _, s in weekly_scores[len(weekly_scores) // 2 :]) / max(1, len(weekly_scores) - len(weekly_scores) // 2)
        if last_avg > first_avg + 0.15:
            overall_tone = "This month had ups and downs; overall your entries became more steady toward the end."
        elif last_avg < first_avg - 0.15:
            overall_tone = "This month had a range of moments; earlier weeks felt a bit lighter than later ones."
        else:
            overall_tone = "This month had a mix of moments, with some consistency across weeks."
    else:
        overall_tone = "This month had a mix of moments. It might be useful to look at what showed up most."

    # Theme evolution (before → after)
    evolution_bullets: list[str] = []
    for theme, when in evolution[:3]:
        if when == "early":
            evolution_bullets.append(f"**{theme}** appeared frequently early in the month, and less often later.")
        elif when == "late":
            evolution_bullets.append(f"**{theme}** became more present in the second half of the month.")
        else:
            evolution_bullets.append(f"**{theme}** showed up steadily throughout the month.")

    # Notable patterns (descriptive, not conclusions)
    notable_bullets: list[str] = []
    if high_themes:
        notable_bullets.append(f"You often mentioned {', '.join(high_themes[:3])} on brighter days.")
    if top_emotions:
        notable_bullets.append(f"Moments of {', '.join(top_emotions[:2])} appeared even during busier weeks.")
    if not notable_bullets:
        notable_bullets.append("Your entries reflected a range of experiences this month.")

    # Progress highlight (strength-based)
    entry_count_row = session.execute(
        text("SELECT COUNT(*) FROM sentiment_result WHERE user_id = :uid AND computed_at >= :start_dt AND computed_at <= :end_dt"),
        {"uid": user_id, "start_dt": start_dt, "end_dt": end_dt},
    ).fetchone()
    entry_count = int(entry_count_row[0]) if entry_count_row and entry_count_row[0] else 0
    low_count_row = session.execute(
        text("SELECT COUNT(*) FROM sentiment_result WHERE user_id = :uid AND computed_at >= :start_dt AND computed_at <= :end_dt AND score < -0.2"),
        {"uid": user_id, "start_dt": start_dt, "end_dt": end_dt},
    ).fetchone()
    low_count = int(low_count_row[0]) if low_count_row and low_count_row[0] else 0
    if entry_count >= 3 and low_count >= 1:
        progress_highlight = "You returned to journaling even on difficult days."
    elif entry_count >= 5:
        progress_highlight = "You showed up for your practice consistently this month."
    else:
        progress_highlight = "You took time to reflect in your entries this month."

    looking_ahead = "As you move into the next month, what would you like to be more mindful of?"

    return {
        "header_title": header_title,
        "header_subtitle": header_subtitle,
        "overall_tone": overall_tone,
        "theme_evolution": evolution_bullets,
        "notable_patterns": notable_bullets,
        "progress_highlight": progress_highlight,
        "looking_ahead": looking_ahead,
    }


def _sections_to_flat(sections: dict[str, Any]) -> str:
    """Flatten sections into one string for backward compatibility / display when no structured UI."""
    parts = []
    if sections.get("header_title"):
        parts.append(sections["header_title"])
        if sections.get("header_subtitle"):
            parts.append(sections["header_subtitle"])
    for key in ("emotional_snapshot", "overall_tone"):
        if sections.get(key):
            parts.append(sections[key])
    for key in ("recurring_themes", "theme_evolution", "notable_patterns"):
        if sections.get(key):
            for line in sections[key]:
                parts.append(line.replace("**", ""))
    if sections.get("gentle_connections"):
        parts.append(sections["gentle_connections"])
    if sections.get("progress_highlight"):
        parts.append(sections["progress_highlight"])
    if sections.get("reflection_prompt"):
        parts.append(sections["reflection_prompt"][0] if isinstance(sections["reflection_prompt"], list) else sections["reflection_prompt"])
    if sections.get("looking_ahead"):
        parts.append(sections["looking_ahead"])
    return "\n\n".join(parts)


@app.get("/api/v1/summaries/latest", response_model=SummaryResponse)
def get_latest_summary(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    period: Optional[str] = Query(None, description="Filter by period: daily, weekly, or monthly"),
):
    user_id = get_user_id(authorization, x_user_id)
    session = Session()
    try:
        if period in ("daily", "weekly", "monthly"):
            result = session.execute(
                text("""
                    SELECT summary_text, period_start, period_end, generated_at
                    FROM reflection_summary
                    WHERE user_id = :uid AND (period_type = :pt OR (period_type IS NULL AND :pt = 'weekly'))
                    ORDER BY generated_at DESC
                    LIMIT 1
                """),
                {"uid": user_id, "pt": period},
            )
        else:
            result = session.execute(
                text("""
                    SELECT summary_text, period_start, period_end, generated_at
                    FROM reflection_summary
                    WHERE user_id = :uid
                    ORDER BY generated_at DESC
                    LIMIT 1
                """),
                {"uid": user_id},
            )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No summary yet. Write entries and generate a summary.")
        summary_text = row[0]
        sections = None
        try:
            if isinstance(summary_text, str) and summary_text.strip().startswith("{"):
                sections = json.loads(summary_text)
                summary_text = _sections_to_flat(sections)
        except (json.JSONDecodeError, TypeError):
            pass
        return SummaryResponse(
            summary=summary_text,
            period_start=row[1].isoformat() if hasattr(row[1], "isoformat") else str(row[1]),
            period_end=row[2].isoformat() if hasattr(row[2], "isoformat") else str(row[2]),
            generated_at=row[3].isoformat() if hasattr(row[3], "isoformat") else str(row[3]),
            sections=sections,
        )
    finally:
        session.close()


@app.get("/api/v1/summaries/weekly", response_model=SummaryResponse)
def get_or_create_weekly_summary(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """Weekly reflection: header, emotional snapshot, recurring themes, gentle connections, reflection prompt."""
    user_id = get_user_id(authorization, x_user_id)
    session = Session()
    try:
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - timedelta(days=7)
        sections = build_weekly_sections(session, user_id, start_dt, end_dt)
        summary_text = json.dumps(sections)
        summary = ReflectionSummary(
            user_id=user_id,
            period_start=start_dt,
            period_end=end_dt,
            period_type="weekly",
            summary_text=summary_text,
        )
        session.add(summary)
        session.commit()
        flat = _sections_to_flat(sections)
        return SummaryResponse(
            summary=flat,
            period_start=start_dt.isoformat(),
            period_end=end_dt.isoformat(),
            generated_at=summary.generated_at.isoformat() if summary.generated_at else end_dt.isoformat(),
            sections=sections,
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _generate_summary_for_period(
    session,
    user_id: str,
    start_dt: datetime,
    end_dt: datetime,
    period_label: str,
    period_type: str,
) -> ReflectionSummary:
    result = session.execute(
        text("""
            SELECT AVG(score) FROM sentiment_result
            WHERE user_id = :uid AND computed_at >= :start_dt AND computed_at <= :end_dt
        """),
        {"uid": user_id, "start_dt": start_dt, "end_dt": end_dt},
    )
    row = result.fetchone()
    sentiment_avg = float(row[0]) if row and row[0] is not None else 0.0
    result2 = session.execute(
        text("""
            SELECT jsonb_array_elements_text(themes) AS theme
            FROM theme_result
            WHERE user_id = :uid AND computed_at >= :start_dt AND computed_at <= :end_dt
        """),
        {"uid": user_id, "start_dt": start_dt, "end_dt": end_dt},
    )
    themes_raw = list({r[0] for r in result2.fetchall()})[:20]
    low_raw, high_raw = get_theme_sentiment_buckets(session, user_id, start_dt, end_dt)
    top_emotions = get_top_emotions(session, user_id, start_dt, end_dt)
    themes = clean_themes_for_summary(themes_raw)
    low_themes = clean_themes_for_summary(low_raw)
    high_themes = clean_themes_for_summary(high_raw)
    summary_text = (
        generate_summary_llm(themes, sentiment_avg, period_label, low_themes=low_themes, high_themes=high_themes, top_emotions=top_emotions)
        or fallback_summary(themes, sentiment_avg, period_label, low_themes=low_themes, high_themes=high_themes, top_emotions=top_emotions)
    )
    return ReflectionSummary(
        user_id=user_id,
        period_start=start_dt,
        period_end=end_dt,
        period_type=period_type,
        summary_text=summary_text,
    )


@app.get("/api/v1/summaries/daily", response_model=SummaryResponse)
def generate_daily_summary(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """Generate an insightful reflection for today (entries from start of today UTC)."""
    user_id = get_user_id(authorization, x_user_id)
    session = Session()
    try:
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        summary = _generate_summary_for_period(
            session, user_id, start_dt, end_dt, "today", "daily"
        )
        session.add(summary)
        session.commit()
        return SummaryResponse(
            summary=summary.summary_text,
            period_start=summary.period_start.isoformat(),
            period_end=summary.period_end.isoformat(),
            generated_at=summary.generated_at.isoformat() if summary.generated_at else end_dt.isoformat(),
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.get("/api/v1/summaries/monthly", response_model=SummaryResponse)
def generate_monthly_summary(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """Monthly reflection: header, overall tone, theme evolution, notable patterns, progress highlight, looking ahead."""
    user_id = get_user_id(authorization, x_user_id)
    session = Session()
    try:
        end_dt = datetime.now(timezone.utc)
        start_dt = end_dt - timedelta(days=30)
        sections = build_monthly_sections(session, user_id, start_dt, end_dt)
        summary_text = json.dumps(sections)
        summary = ReflectionSummary(
            user_id=user_id,
            period_start=start_dt,
            period_end=end_dt,
            period_type="monthly",
            summary_text=summary_text,
        )
        session.add(summary)
        session.commit()
        flat = _sections_to_flat(sections)
        return SummaryResponse(
            summary=flat,
            period_start=start_dt.isoformat(),
            period_end=end_dt.isoformat(),
            generated_at=summary.generated_at.isoformat() if summary.generated_at else end_dt.isoformat(),
            sections=sections,
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8002")))
