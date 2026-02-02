from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import uuid

from config import ANALYTICS_DB_URL

engine = create_engine(ANALYTICS_DB_URL, pool_pre_ping=True)
Base = declarative_base()
Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class SentimentResult(Base):
    __tablename__ = "sentiment_result"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    score = Column(Float, nullable=False)  # -1 to 1
    label = Column(String(50), nullable=True)  # e.g. positive, negative, neutral, mixed
    emotions = Column(JSONB, nullable=True)  # list of strings from fixed taxonomy
    entry_created_at = Column(DateTime, nullable=True)  # from journal entry for time-of-day filter
    computed_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index("idx_sentiment_user_computed", "user_id", "computed_at"),)


class ThemeResult(Base):
    __tablename__ = "theme_result"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    themes = Column(JSONB, nullable=False)  # list of strings
    entry_created_at = Column(DateTime, nullable=True)  # from journal entry for time-of-day filter
    computed_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index("idx_theme_user_computed", "user_id", "computed_at"),)


class EntryReflection(Base):
    __tablename__ = "entry_reflection"
    entry_id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)
    reflection = Column(Text, nullable=True)  # one short empathetic sentence
    computed_at = Column(DateTime, default=datetime.utcnow)


class ReflectionSummary(Base):
    __tablename__ = "reflection_summary"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String(20), nullable=True)  # 'daily' | 'weekly' | 'monthly'
    summary_text = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)
