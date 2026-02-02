"""
Insights API: GET sentiment series and theme aggregates for the authenticated user.
Scoped by userId from JWT (sub) or X-User-Id for demo.
"""
import os
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import jwt
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import sessionmaker

from config import ANALYTICS_DB_URL

# JWT secret must match Auth Service
JWT_SECRET = os.getenv("JWT_SECRET", "your-256-bit-secret-for-jwt-signing-change-in-production")

engine = create_engine(ANALYTICS_DB_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

app = FastAPI(title="Insights API", version="1.0.0")
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
                payload = jwt.decode(
                    token,
                    JWT_SECRET,
                    algorithms=["HS256"],
                    options={"verify_exp": True},
                )
                sub = payload.get("sub")
                if sub:
                    return str(sub)
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=401,
                    detail="Token expired. Sign out and sign in again.",
                )
            except jwt.InvalidTokenError:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token. Ensure JWT_SECRET is the same for Auth and Insights.",
                )
    if x_user_id and x_user_id.strip():
        return x_user_id.strip()
    raise HTTPException(
        status_code=401,
        detail="Authorization required. Send Bearer token or set JWT_SECRET to match Auth service.",
    )


class SentimentPoint(BaseModel):
    date: str
    score: float
    label: Optional[str] = None


class SentimentResponse(BaseModel):
    data: list[SentimentPoint]


class ThemesResponse(BaseModel):
    themes: list[str]


class ThemeWithCount(BaseModel):
    theme: str
    count: int


class ThemesWithCountsResponse(BaseModel):
    themes: list[ThemeWithCount]


class EmotionCount(BaseModel):
    emotion: str
    count: int


class EmotionsOverTimePoint(BaseModel):
    date: str
    emotions: list[EmotionCount]


class EmotionsOverTimeResponse(BaseModel):
    data: list[EmotionsOverTimePoint]


class ThemeSentimentBreakdownItem(BaseModel):
    theme: str
    low: int
    neutral: int
    high: int


class ThemeSentimentBreakdownResponse(BaseModel):
    data: list[ThemeSentimentBreakdownItem]


class ActionableInsightsResponse(BaseModel):
    actions: list[str]


class ThemeSentimentResponse(BaseModel):
    low: list[str]
    neutral: list[str]
    high: list[str]


class WeekCaptionResponse(BaseModel):
    caption: str


class EmotionsResponse(BaseModel):
    emotions: list[str]
    caption: Optional[str] = None


class PatternInsightsResponse(BaseModel):
    insights: list[str]


# Junk themes from old LLM output or seed data: long prose, "Here are...", numbered lists
THEME_STOP_PHRASES = (
    "here are", "recommend", "could be", "comma-separated", "e.g.", "such as",
    "short theme tag", "journal entry", "round out", "fit well", "under consideration",
    "words)", "word)", "phrase", "reply as", "include these", "tags that",
    "and genuinely", "but reflecting",
)
THEME_STOP_WORDS = {
    "about", "around", "bad", "not", "e.g", "i.e", "the", "and", "for", "of", "with",
    "that", "this", "from", "have", "has", "had", "were", "been", "make", "made",
    "take", "ate", "ice", "people", "only", "just", "what", "when", "where", "which",
    "who", "how", "into", "out", "than", "then", "some", "more", "most", "other",
    "such", "very", "too", "so", "if", "because", "until", "while", "after", "before",
    "but", "good", "cream", "game", "life", "forward", "looking", "better", "great",
    "money", "lunch", "videos", "watching", "food", "sweet", "treat", "closure",
    "relaxation", "honestly", "genuinely", "analyzing", "defining", "brainstorming",
}


def is_valid_theme(theme: str) -> bool:
    """Filter out junk themes from old LLM output or seed data."""
    if not theme or not isinstance(theme, str):
        return False
    t = theme.strip()
    if len(t) > 45:
        return False
    if len(t) < 2:
        return False
    lower = t.lower()
    if lower in THEME_STOP_WORDS:
        return False
    words = lower.split()
    if words and words[0] in THEME_STOP_WORDS:
        return False
    if any(lower.startswith(f"{i}.") or lower.startswith(f"{i})") for i in range(10)):
        return False
    if any(phrase in lower for phrase in THEME_STOP_PHRASES):
        return False
    if '"' in t or ("(" in lower and "word" in lower):
        return False
    if t.count(" ") > 4:
        return False
    return True


def filter_themes(themes: list[str]) -> list[str]:
    return [t for t in themes if is_valid_theme(t)]


@app.get("/api/v1/insights/theme-sentiment", response_model=ThemeSentimentResponse)
def get_theme_sentiment(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    days: int = Query(30, ge=1, le=90),
    hour_from: Optional[int] = Query(None, ge=0, le=23),
    hour_to: Optional[int] = Query(None, ge=0, le=23),
):
    """Return themes grouped by sentiment bucket: low (score < -0.2), neutral, high (score > 0.2). Optional time-of-day filter."""
    user_id = get_user_id(authorization, x_user_id)
    to_dt = datetime.utcnow()
    from_dt = to_dt - timedelta(days=days)
    time_sql = ""
    time_params: dict = {}
    if hour_from is not None and hour_to is not None:
        time_sql = " AND sr.entry_created_at IS NOT NULL AND EXTRACT(HOUR FROM sr.entry_created_at) BETWEEN :hour_from AND :hour_to"
        time_params = {"hour_from": hour_from, "hour_to": hour_to}
    session = Session()
    try:
        result = session.execute(
            text(f"""
                WITH themed AS (
                    SELECT tr.entry_id, sr.score, jsonb_array_elements_text(tr.themes) AS theme
                    FROM theme_result tr
                    JOIN sentiment_result sr ON tr.entry_id = sr.entry_id AND tr.user_id = sr.user_id
                    WHERE tr.user_id = :uid AND tr.computed_at >= :from_dt AND tr.computed_at <= :to_dt{time_sql}
                )
                SELECT theme,
                    CASE WHEN score < -0.2 THEN 'low' WHEN score > 0.2 THEN 'high' ELSE 'neutral' END AS bucket
                FROM themed
            """),
            {"uid": user_id, "from_dt": from_dt, "to_dt": to_dt, **time_params},
        )
        rows = result.fetchall()
        low_set: set[str] = set()
        neutral_set: set[str] = set()
        high_set: set[str] = set()
        for theme, bucket in rows:
            if theme and is_valid_theme(theme):
                if bucket == "low":
                    low_set.add(theme)
                elif bucket == "high":
                    high_set.add(theme)
                else:
                    neutral_set.add(theme)
        return ThemeSentimentResponse(
            low=sorted(filter_themes(low_set)),
            neutral=sorted(filter_themes(neutral_set)),
            high=sorted(filter_themes(high_set)),
        )
    except ProgrammingError:
        return ThemeSentimentResponse(low=[], neutral=[], high=[])
    finally:
        session.close()


@app.get("/api/v1/insights/week-caption", response_model=WeekCaptionResponse)
def get_week_caption(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """Return one rule-based empathetic caption for the last 7 days sentiment."""
    user_id = get_user_id(authorization, x_user_id)
    to_dt = datetime.utcnow()
    from_dt = to_dt - timedelta(days=7)
    session = Session()
    try:
        result = session.execute(
            text("""
                SELECT AVG(score) AS avg_score
                FROM sentiment_result
                WHERE user_id = :uid AND computed_at >= :from_dt AND computed_at <= :to_dt
            """),
            {"uid": user_id, "from_dt": from_dt, "to_dt": to_dt},
        )
        row = result.fetchone()
        if row is None or row[0] is None:
            return WeekCaptionResponse(caption="Keep writing to see your week in reflection.")
        avg_score = float(row[0])
        if avg_score < -0.2:
            caption = "This week was heavy. It's okay to have low periods; writing about them is a step."
        elif avg_score > 0.2:
            caption = "You've had several brighter days in a row."
        else:
            caption = "Your week had a mix of ups and downs. Noticing that is part of the process."
        return WeekCaptionResponse(caption=caption)
    finally:
        session.close()


@app.get("/api/v1/insights/emotions", response_model=EmotionsResponse)
def get_emotions(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    days: int = Query(7, ge=1, le=90),
):
    """Return most frequent emotions over the date range and an optional caption."""
    user_id = get_user_id(authorization, x_user_id)
    to_dt = datetime.utcnow()
    from_dt = to_dt - timedelta(days=days)
    session = Session()
    try:
        result = session.execute(
            text("""
                SELECT emotions FROM sentiment_result
                WHERE user_id = :uid AND computed_at >= :from_dt AND computed_at <= :to_dt
                  AND emotions IS NOT NULL
                  AND CASE WHEN jsonb_typeof(emotions) = 'array' THEN jsonb_array_length(emotions) > 0 ELSE false END
            """),
            {"uid": user_id, "from_dt": from_dt, "to_dt": to_dt},
        )
        rows = result.fetchall()
        counter: Counter[str] = Counter()
        for (emotions_json,) in rows:
            if emotions_json and isinstance(emotions_json, list):
                for e in emotions_json:
                    if isinstance(e, str):
                        counter[e] += 1
        top = [emotion for emotion, _ in counter.most_common(5)]
        caption = None
        if top:
            caption = f"This week you often felt: {', '.join(top)}."
        return EmotionsResponse(emotions=top, caption=caption)
    except ProgrammingError:
        return EmotionsResponse(emotions=[], caption=None)
    finally:
        session.close()


DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


@app.get("/api/v1/insights/patterns", response_model=PatternInsightsResponse)
def get_pattern_insights(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    days: int = Query(30, ge=7, le=90),
):
    """Return 1-2 pattern insights: day-of-week (e.g. lower on Mondays), theme-sentiment correlation."""
    user_id = get_user_id(authorization, x_user_id)
    to_dt = datetime.utcnow()
    from_dt = to_dt - timedelta(days=days)
    session = Session()
    insights: list[str] = []
    try:
        overall = session.execute(
            text("""
                SELECT AVG(score) FROM sentiment_result
                WHERE user_id = :uid AND computed_at >= :from_dt AND computed_at <= :to_dt
            """),
            {"uid": user_id, "from_dt": from_dt, "to_dt": to_dt},
        )
        row = overall.fetchone()
        overall_avg = float(row[0]) if row and row[0] is not None else 0.0
        dow_result = session.execute(
            text("""
                SELECT EXTRACT(DOW FROM computed_at)::int AS dow, AVG(score) AS avg_score, COUNT(*)
                FROM sentiment_result
                WHERE user_id = :uid AND computed_at >= :from_dt AND computed_at <= :to_dt
                GROUP BY EXTRACT(DOW FROM computed_at)
            """),
            {"uid": user_id, "from_dt": from_dt, "to_dt": to_dt},
        )
        for dow, avg_score, cnt in dow_result.fetchall():
            if cnt and cnt >= 2 and avg_score is not None:
                diff = overall_avg - float(avg_score)
                if diff > 0.2:
                    day_name = DAY_NAMES[int(dow)] if 0 <= int(dow) < 7 else "one day"
                    insights.append(f"Your entries tend to have lower average sentiment on {day_name}s.")
                    break
        theme_corr = session.execute(
            text("""
                WITH themed AS (
                    SELECT tr.entry_id, sr.score, jsonb_array_elements_text(tr.themes) AS theme
                    FROM theme_result tr
                    JOIN sentiment_result sr ON tr.entry_id = sr.entry_id AND tr.user_id = sr.user_id
                    WHERE tr.user_id = :uid AND tr.computed_at >= :from_dt AND tr.computed_at <= :to_dt
                ),
                theme_avg AS (
                    SELECT theme, AVG(score) AS theme_score, COUNT(*) AS n
                    FROM themed WHERE theme IS NOT NULL AND theme != ''
                    GROUP BY theme HAVING COUNT(*) >= 2
                )
                SELECT theme, theme_score FROM theme_avg
                WHERE theme_score > :overall_plus
                ORDER BY theme_score DESC LIMIT 2
            """),
            {"uid": user_id, "from_dt": from_dt, "to_dt": to_dt, "overall_plus": overall_avg + 0.2},
        )
        for theme, theme_score in theme_corr.fetchall():
            if theme and is_valid_theme(theme):
                insights.append(f"Entries mentioning '{theme}' correlate with higher sentiment.")
        return PatternInsightsResponse(insights=insights[:3])
    except ProgrammingError:
        return PatternInsightsResponse(insights=[])
    finally:
        session.close()


@app.get("/api/v1/insights/sentiment", response_model=SentimentResponse)
def get_sentiment(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    days: int = Query(30, ge=1, le=90),
):
    user_id = get_user_id(authorization, x_user_id)
    session = Session()
    try:
        if from_date and to_date:
            try:
                from_dt = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
                to_dt = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid from/to date")
        else:
            to_dt = datetime.utcnow()
            from_dt = to_dt - timedelta(days=days)
        result = session.execute(
            text("""
                SELECT DATE(computed_at) AS d, AVG(score) AS avg_score, MAX(label) AS label
                FROM sentiment_result
                WHERE user_id = :uid AND computed_at >= :from_dt AND computed_at <= :to_dt
                GROUP BY DATE(computed_at)
                ORDER BY d
            """),
            {"uid": user_id, "from_dt": from_dt, "to_dt": to_dt},
        )
        rows = result.fetchall()
        data = [
            SentimentPoint(date=str(row[0]), score=round(float(row[1]), 3), label=row[2])
            for row in rows
        ]
        return SentimentResponse(data=data)
    finally:
        session.close()


class EntryInsightResponse(BaseModel):
    reflection: Optional[str] = None


@app.get("/api/v1/insights/entry/{entry_id}", response_model=EntryInsightResponse)
def get_entry_insight(
    entry_id: UUID,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """Return one-line reflection (and optionally sentiment/themes) for an entry. Scoped to current user."""
    user_id = get_user_id(authorization, x_user_id)
    session = Session()
    try:
        result = session.execute(
            text("""
                SELECT reflection FROM entry_reflection
                WHERE entry_id = :eid AND user_id = :uid
            """),
            {"eid": str(entry_id), "uid": user_id},
        )
        row = result.fetchone()
        reflection = row[0] if row and row[0] else None
        return EntryInsightResponse(reflection=reflection)
    except ProgrammingError:
        return EntryInsightResponse(reflection=None)
    finally:
        session.close()


@app.get("/api/v1/insights/themes", response_model=ThemesResponse)
def get_themes(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    limit: int = Query(20, ge=1, le=50),
):
    user_id = get_user_id(authorization, x_user_id)
    session = Session()
    try:
        result = session.execute(
            text("""
                SELECT theme FROM (
                    SELECT jsonb_array_elements_text(themes) AS theme
                    FROM theme_result
                    WHERE user_id = :uid
                ) t
                GROUP BY theme
                ORDER BY COUNT(*) DESC
                LIMIT :limit
            """),
            {"uid": user_id, "limit": limit},
        )
        themes = [row[0] for row in result.fetchall()]
        return ThemesResponse(themes=themes)
    finally:
        session.close()


@app.get("/api/v1/insights/themes/with-counts", response_model=ThemesWithCountsResponse)
def get_themes_with_counts(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    days: int = Query(30, ge=7, le=90),
    limit: int = Query(20, ge=1, le=50),
):
    """Return top themes with recurrence counts for the date range."""
    user_id = get_user_id(authorization, x_user_id)
    to_dt = datetime.utcnow()
    from_dt = to_dt - timedelta(days=days)
    session = Session()
    try:
        result = session.execute(
            text("""
                SELECT theme, COUNT(*) AS cnt
                FROM (
                    SELECT jsonb_array_elements_text(tr.themes) AS theme
                    FROM theme_result tr
                    WHERE tr.user_id = :uid AND tr.computed_at >= :from_dt AND tr.computed_at <= :to_dt
                ) t
                WHERE theme IS NOT NULL AND theme != ''
                GROUP BY theme
                ORDER BY cnt DESC
                LIMIT :limit
            """),
            {"uid": user_id, "from_dt": from_dt, "to_dt": to_dt, "limit": limit},
        )
        themes = [ThemeWithCount(theme=row[0], count=row[1]) for row in result.fetchall() if is_valid_theme(row[0])]
        return ThemesWithCountsResponse(themes=themes)
    except ProgrammingError:
        return ThemesWithCountsResponse(themes=[])
    finally:
        session.close()


@app.get("/api/v1/insights/emotions/over-time", response_model=EmotionsOverTimeResponse)
def get_emotions_over_time(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    days: int = Query(30, ge=7, le=90),
):
    """Return emotion counts per day for stress/emotion chart."""
    user_id = get_user_id(authorization, x_user_id)
    to_dt = datetime.utcnow()
    from_dt = to_dt - timedelta(days=days)
    session = Session()
    by_date: dict[str, Counter[str]] = {}
    try:
        result = session.execute(
            text("""
                SELECT DATE(computed_at) AS d, emotions
                FROM sentiment_result
                WHERE user_id = :uid AND computed_at >= :from_dt AND computed_at <= :to_dt
                  AND emotions IS NOT NULL
                  AND CASE WHEN jsonb_typeof(emotions) = 'array' THEN jsonb_array_length(emotions) > 0 ELSE false END
            """),
            {"uid": user_id, "from_dt": from_dt, "to_dt": to_dt},
        )
        for row in result.fetchall():
            d_str = str(row[0])
            if d_str not in by_date:
                by_date[d_str] = Counter()
            em = row[1]
            if em and isinstance(em, list):
                for e in em:
                    if isinstance(e, str):
                        by_date[d_str][e] += 1
        data = [
            EmotionsOverTimePoint(
                date=d_str,
                emotions=[EmotionCount(emotion=e, count=c) for e, c in by_date[d_str].most_common(10)],
            )
            for d_str in sorted(by_date.keys())
        ]
        return EmotionsOverTimeResponse(data=data)
    except ProgrammingError:
        return EmotionsOverTimeResponse(data=[])
    finally:
        session.close()


@app.get("/api/v1/insights/theme-sentiment-breakdown", response_model=ThemeSentimentBreakdownResponse)
def get_theme_sentiment_breakdown(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    days: int = Query(30, ge=7, le=90),
    limit: int = Query(15, ge=1, le=30),
):
    """Return per-theme counts in low/neutral/high sentiment buckets."""
    user_id = get_user_id(authorization, x_user_id)
    to_dt = datetime.utcnow()
    from_dt = to_dt - timedelta(days=days)
    session = Session()
    try:
        result = session.execute(
            text("""
                WITH themed AS (
                    SELECT tr.entry_id, sr.score, jsonb_array_elements_text(tr.themes) AS theme
                    FROM theme_result tr
                    JOIN sentiment_result sr ON tr.entry_id = sr.entry_id AND tr.user_id = sr.user_id
                    WHERE tr.user_id = :uid AND tr.computed_at >= :from_dt AND tr.computed_at <= :to_dt
                ),
                bucketed AS (
                    SELECT theme,
                        CASE WHEN score < -0.2 THEN 'low' WHEN score > 0.2 THEN 'high' ELSE 'neutral' END AS bucket
                    FROM themed WHERE theme IS NOT NULL AND theme != ''
                )
                SELECT theme,
                    COUNT(*) FILTER (WHERE bucket = 'low') AS low,
                    COUNT(*) FILTER (WHERE bucket = 'neutral') AS neutral,
                    COUNT(*) FILTER (WHERE bucket = 'high') AS high
                FROM bucketed
                GROUP BY theme
                ORDER BY (low + neutral + high) DESC
                LIMIT :limit
            """),
            {"uid": user_id, "from_dt": from_dt, "to_dt": to_dt, "limit": limit},
        )
        data = [
            ThemeSentimentBreakdownItem(theme=row[0], low=row[1] or 0, neutral=row[2] or 0, high=row[3] or 0)
            for row in result.fetchall()
            if is_valid_theme(row[0])
        ]
        return ThemeSentimentBreakdownResponse(data=data)
    except ProgrammingError:
        return ThemeSentimentBreakdownResponse(data=[])
    finally:
        session.close()


@app.get("/api/v1/insights/actionable", response_model=ActionableInsightsResponse)
def get_actionable_insights(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    days: int = Query(30, ge=7, le=90),
):
    """Return short, actionable suggestions based on themes, sentiment, and patterns."""
    user_id = get_user_id(authorization, x_user_id)
    to_dt = datetime.utcnow()
    from_dt = to_dt - timedelta(days=days)
    session = Session()
    actions: list[str] = []
    try:
        # Low-sentiment themes → suggest self-care
        low_themes = session.execute(
            text("""
                WITH themed AS (
                    SELECT jsonb_array_elements_text(tr.themes) AS theme, sr.score
                    FROM theme_result tr
                    JOIN sentiment_result sr ON tr.entry_id = sr.entry_id AND tr.user_id = sr.user_id
                    WHERE tr.user_id = :uid AND tr.computed_at >= :from_dt AND tr.computed_at <= :to_dt
                )
                SELECT theme FROM themed
                WHERE theme IS NOT NULL AND theme != '' AND score < -0.2
                GROUP BY theme HAVING COUNT(*) >= 2
                ORDER BY COUNT(*) DESC LIMIT 3
            """),
            {"uid": user_id, "from_dt": from_dt, "to_dt": to_dt},
        )
        low_list = [r[0] for r in low_themes.fetchall() if is_valid_theme(r[0])]
        if low_list:
            actions.append(f"When you write about {low_list[0]}, you might find a short break or a small kindness for yourself helpful afterward — only if it feels right.")
        else:
            # Fallback: we have low-sentiment entries but no valid theme name → generic gentle suggestion
            low_count_row = session.execute(
                text("""
                    SELECT COUNT(*) FROM sentiment_result
                    WHERE user_id = :uid AND computed_at >= :from_dt AND computed_at <= :to_dt AND score < -0.2
                """),
                {"uid": user_id, "from_dt": from_dt, "to_dt": to_dt},
            ).fetchone()
            if low_count_row and (low_count_row[0] or 0) >= 2:
                actions.append("After writing about difficult topics, a short break or a small kindness for yourself might help — only if it feels right.")
        # Day-of-week pattern
        overall = session.execute(
            text("SELECT AVG(score) FROM sentiment_result WHERE user_id = :uid AND computed_at >= :from_dt AND computed_at <= :to_dt"),
            {"uid": user_id, "from_dt": from_dt, "to_dt": to_dt},
        )
        row = overall.fetchone()
        overall_avg = float(row[0]) if row and row[0] is not None else 0.0
        dow = session.execute(
            text("""
                SELECT EXTRACT(DOW FROM computed_at)::int, AVG(score), COUNT(*)
                FROM sentiment_result
                WHERE user_id = :uid AND computed_at >= :from_dt AND computed_at <= :to_dt
                GROUP BY EXTRACT(DOW FROM computed_at)
                HAVING COUNT(*) >= 2 AND AVG(score) < :threshold
            """),
            {"uid": user_id, "from_dt": from_dt, "to_dt": to_dt, "threshold": overall_avg - 0.2},
        )
        for dow_row in dow.fetchall():
            day_name = DAY_NAMES[int(dow_row[0])] if 0 <= int(dow_row[0]) < 7 else "weekday"
            actions.append(f"Your mood tends to be lower on {day_name}s. Consider a light ritual (e.g. walk, call a friend) on those days.")
            break
        # High-sentiment theme → encourage
        high_themes = session.execute(
            text("""
                WITH themed AS (
                    SELECT jsonb_array_elements_text(tr.themes) AS theme, sr.score
                    FROM theme_result tr
                    JOIN sentiment_result sr ON tr.entry_id = sr.entry_id AND tr.user_id = sr.user_id
                    WHERE tr.user_id = :uid AND tr.computed_at >= :from_dt AND tr.computed_at <= :to_dt
                )
                SELECT theme FROM themed
                WHERE theme IS NOT NULL AND theme != '' AND score > 0.2
                GROUP BY theme HAVING COUNT(*) >= 2
                ORDER BY COUNT(*) DESC LIMIT 1
            """),
            {"uid": user_id, "from_dt": from_dt, "to_dt": to_dt},
        )
        high_row = high_themes.fetchone()
        if high_row and is_valid_theme(high_row[0]) and not any("brighter" in a for a in actions):
            actions.append(f"When you write about '{high_row[0]}', your entries often reflect brighter moments. You might lean into that when it feels natural.")
        return ActionableInsightsResponse(actions=actions[:5])
    except ProgrammingError:
        return ActionableInsightsResponse(actions=[])
    finally:
        session.close()


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8001")))
