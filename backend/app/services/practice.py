"""Persists attempts and keeps the spaced-repetition memory up to date."""

from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.content.repository import ContentRepository
from app.db.models import Attempt, SrsCard
from app.services import srs
from app.services.evaluation import Evaluation
from app.services.exercises import Exercise, ExerciseType, build_exercise
from app.services.feedback import Feedback


class SrsUpdate(BaseModel):
    card_id: str
    kind: str
    next_due_at: datetime
    interval_days: float


def _get_card(db: Session, user_id: str, kind: str, ex: Exercise) -> SrsCard:
    card = db.scalar(select(SrsCard).where(
        SrsCard.user_id == user_id, SrsCard.kind == kind,
        SrsCard.scenario_id == ex.scenario_id, SrsCard.phrase_id == ex.phrase_id))
    if not card:
        card = SrsCard(user_id=user_id, kind=kind, scenario_id=ex.scenario_id, phrase_id=ex.phrase_id,
                       focus_words=[], ease=2.5, interval_days=0.0, repetitions=0, lapses=0)
        db.add(card)
    return card


def _apply(card: SrsCard, quality: int, score: float) -> SrsUpdate:
    state = srs.SrsState(ease=card.ease, interval_days=card.interval_days,
                         repetitions=card.repetitions, lapses=card.lapses)
    new, due = srs.schedule(state, quality)
    card.ease, card.interval_days, card.repetitions, card.lapses = (
        new.ease, new.interval_days, new.repetitions, new.lapses)
    card.due_at, card.last_score = due, score
    return SrsUpdate(card_id=card.id or "", kind=card.kind, next_due_at=due, interval_days=new.interval_days)


def record_attempt(db: Session, user_id: str, ex: Exercise, ev: Evaluation, fb: Feedback) -> list[SrsUpdate]:
    db.add(Attempt(user_id=user_id, exercise_id=ex.id, exercise_type=ex.type.value, scenario_id=ex.scenario_id,
                   transcript=ev.transcript[:1000], score=ev.score, passed=ev.passed,
                   feedback=fb.model_dump(mode="json")))
    quality = srs.score_to_quality(ev.score, ex.pass_threshold)
    phrase_card = _get_card(db, user_id, "phrase", ex)
    cards = [(phrase_card, quality)]

    # Feedback memory: words the learner struggled with become their own review card.
    existing_fb = db.scalar(select(SrsCard).where(
        SrsCard.user_id == user_id, SrsCard.kind == "feedback",
        SrsCard.scenario_id == ex.scenario_id, SrsCard.phrase_id == ex.phrase_id))
    if fb.focus_words:
        fb_card = existing_fb or _get_card(db, user_id, "feedback", ex)
        fb_card.focus_words = sorted(set(fb.focus_words))
        cards.append((fb_card, min(quality, 2)))
    elif existing_fb:
        cards.append((existing_fb, quality))

    db.flush()
    updates = [_apply(c, q, ev.score) for c, q in cards]
    db.flush()
    for u, (c, _) in zip(updates, cards, strict=True):
        u.card_id = c.id
    db.commit()
    return updates


class ReviewItem(BaseModel):
    card_id: str
    kind: str
    due_at: datetime
    exercise: Exercise


def card_to_exercise(repo: ContentRepository, card: SrsCard) -> Exercise | None:
    scenario, phrase = repo.get(card.scenario_id), repo.phrase(card.scenario_id, card.phrase_id)
    if not scenario or not phrase:
        return None
    if card.kind == "feedback":  # re-teach with full support, highlighting the problem words
        return build_exercise(scenario, phrase, ExerciseType.RECALL, focus_words=list(card.focus_words))
    kind = ExerciseType.COMPLETION if card.repetitions >= 3 else ExerciseType.GUIDED
    return build_exercise(scenario, phrase, kind)


def due_items(db: Session, repo: ContentRepository, user_id: str, limit: int = 20) -> list[ReviewItem]:
    now = datetime.now(UTC)
    cards = db.scalars(select(SrsCard).where(SrsCard.user_id == user_id, SrsCard.due_at <= now)
                       .order_by(SrsCard.kind.desc(), SrsCard.due_at).limit(limit)).all()
    items = []
    for c in cards:
        ex = card_to_exercise(repo, c)
        if ex:
            items.append(ReviewItem(card_id=c.id, kind=c.kind, due_at=c.due_at, exercise=ex))
    return items


class Progress(BaseModel):
    attempts: int
    passed: int
    average_score: float
    scenarios_practised: int
    cards_total: int
    cards_due: int


def progress(db: Session, user_id: str) -> Progress:
    now = datetime.now(UTC)
    attempts = db.scalar(select(func.count()).select_from(Attempt).where(Attempt.user_id == user_id)) or 0
    passed = db.scalar(select(func.count()).select_from(Attempt)
                       .where(Attempt.user_id == user_id, Attempt.passed.is_(True))) or 0
    avg = db.scalar(select(func.avg(Attempt.score)).where(Attempt.user_id == user_id)) or 0.0
    scen = db.scalar(select(func.count(func.distinct(Attempt.scenario_id))).where(Attempt.user_id == user_id)) or 0
    total = db.scalar(select(func.count()).select_from(SrsCard).where(SrsCard.user_id == user_id)) or 0
    due = db.scalar(select(func.count()).select_from(SrsCard)
                    .where(SrsCard.user_id == user_id, SrsCard.due_at <= now)) or 0
    return Progress(attempts=attempts, passed=passed, average_score=round(float(avg), 3),
                    scenarios_practised=scen, cards_total=total, cards_due=due)
