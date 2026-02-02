"""Consume EntryCreated from Kafka; compute sentiment and themes; store in Analytics DB."""
import json
import sys
import uuid
from datetime import datetime, timezone
from kafka import KafkaConsumer
from sqlalchemy.orm import Session

from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_ENTRY_CREATED
from db import init_db, Session as DBSession, SentimentResult, ThemeResult
from emotions import compute_emotions
from sentiment import compute_sentiment
from themes import extract_themes


def _parse_entry_created_at(data: dict):
    """Parse createdAt from event (ISO string or epoch ms). Return datetime or None."""
    raw = data.get("createdAt")
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        try:
            ts = raw / 1000.0 if raw > 1e12 else raw
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (ValueError, OSError):
            return None
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def process_message(data: dict) -> None:
    entry_id = uuid.UUID(data["entryId"]) if isinstance(data.get("entryId"), str) else data.get("entryId")
    user_id = data.get("userId")
    content = data.get("content") or ""
    if not user_id or not entry_id:
        return
    entry_created_at = _parse_entry_created_at(data)
    session: Session = DBSession()
    try:
        score, label = compute_sentiment(content)
        emotions = compute_emotions(content)
        session.add(SentimentResult(entry_id=entry_id, user_id=user_id, score=score, label=label, emotions=emotions or None, entry_created_at=entry_created_at))
        themes = extract_themes(content)
        session.add(ThemeResult(entry_id=entry_id, user_id=user_id, themes=themes, entry_created_at=entry_created_at))
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def run_consumer():
    init_db()
    consumer = KafkaConsumer(
        KAFKA_TOPIC_ENTRY_CREATED,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","),
        group_id="journal-ai-consumer",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")) if m else None,
    )
    print("Consumer started. Waiting for entry.created events...", flush=True)
    for message in consumer:
        try:
            if message.value:
                process_message(message.value)
        except Exception as e:
            print(f"Error processing message: {e}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    run_consumer()
