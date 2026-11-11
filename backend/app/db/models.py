import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.db.session import Base


class UTCDateTime(TypeDecorator):
    """Stores naive UTC (portable across SQLite/Postgres) and always returns aware UTC datetimes."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is not None:
            value = value.astimezone(UTC).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        return value.replace(tzinfo=UTC) if value is not None else None


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str | None] = mapped_column(String(255))
    cefr_level: Mapped[str] = mapped_column(String(2), default="A1")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=_now)


class Attempt(Base):
    __tablename__ = "attempts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    exercise_id: Mapped[str] = mapped_column(String(200), index=True)
    exercise_type: Mapped[str] = mapped_column(String(20))
    scenario_id: Mapped[str] = mapped_column(String(100), index=True)
    transcript: Mapped[str] = mapped_column(String(1000))
    score: Mapped[float] = mapped_column(Float)
    passed: Mapped[bool] = mapped_column(Boolean)
    feedback: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=_now)


class SrsCard(Base):
    __tablename__ = "srs_cards"
    __table_args__ = (UniqueConstraint("user_id", "kind", "scenario_id", "phrase_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # phrase | feedback
    scenario_id: Mapped[str] = mapped_column(String(100))
    phrase_id: Mapped[str] = mapped_column(String(100))
    focus_words: Mapped[list] = mapped_column(JSON, default=list)
    ease: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[float] = mapped_column(Float, default=0.0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    lapses: Mapped[int] = mapped_column(Integer, default=0)
    last_score: Mapped[float | None] = mapped_column(Float)
    due_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=_now, index=True)


class RoleplaySession(Base):
    __tablename__ = "roleplay_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    scenario_id: Mapped[str] = mapped_column(String(100))
    turn_index: Mapped[int] = mapped_column(Integer, default=0)  # index of the pending user turn
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | completed
    history: Mapped[list] = mapped_column(JSON, default=list)
    scores: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=_now)
