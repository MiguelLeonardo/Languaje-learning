from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import RepoDep, SettingsDep, SpeechDep, transcribe_answer
from app.content.repository import ContentRepository
from app.core.config import Settings
from app.core.security import get_current_user, speech_rate_limit
from app.db.models import SrsCard, User
from app.db.session import get_db
from app.services import practice, srs
from app.services.evaluation import Evaluation, evaluate
from app.services.exercises import Exercise, resolve_exercise
from app.services.feedback import Feedback, build_feedback
from app.services.translator import TranslationCard, translate_selection
from app.speech.base import SpeechProvider

router = APIRouter(prefix="/v1", tags=["practice"])


class AttemptResult(BaseModel):
    exercise: Exercise
    evaluation: Evaluation
    feedback: Feedback
    srs: list[practice.SrsUpdate]


class TranslateIn(BaseModel):
    selected_text: str | None = None
    text: str | None = None
    phrase_text: str | None = None
    context_phrase: str | None = None
    scenario_id: str | None = None
    phrase_id: str | None = None


class BookmarkIn(BaseModel):
    scenario_id: str
    phrase_id: str | None = None
    focus_word: str | None = None


class BookmarkOut(practice.SrsUpdate):
    saved: bool = True
    focus_words: list[str] = []


async def _grade(ex: Exercise, audio, debug_transcript, settings, provider, db, user, repo) -> AttemptResult:
    speech = await transcribe_answer(audio, ex.expected_text, debug_transcript, settings, provider)
    ev = evaluate(ex.expected_text, speech.transcript, ex.pass_threshold, speech.confidence)
    fb = build_feedback(ev, repo.phrase(ex.scenario_id, ex.phrase_id))
    updates = practice.record_attempt(db, user.id, ex, ev, fb)
    return AttemptResult(exercise=ex, evaluation=ev, feedback=fb, srs=updates)


@router.post("/translate", response_model=TranslationCard, tags=["translate"])
def translate_word_or_phrase(
    body: TranslateIn,
    _user: User = Depends(get_current_user),
    repo: ContentRepository = RepoDep,
) -> TranslationCard:
    query = body.selected_text or body.text or body.phrase_text or ""
    ctx_phrase = body.phrase_text or body.context_phrase
    return translate_selection(repo, query, ctx_phrase, body.scenario_id, body.phrase_id)


@router.post("/review/bookmark", response_model=BookmarkOut, tags=["review"])
def bookmark_for_review(
    body: BookmarkIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    repo: ContentRepository = RepoDep,
) -> BookmarkOut:
    scenario = repo.get(body.scenario_id)
    if not scenario:
        raise HTTPException(404, "scenario not found")
    phrase = repo.phrase(body.scenario_id, body.phrase_id) if body.phrase_id else scenario.phrases[0]
    if not phrase:
        raise HTTPException(404, "phrase not found")
    kind = "feedback" if body.focus_word else "phrase"
    card = db.scalar(
        select(SrsCard).where(
            SrsCard.user_id == user.id,
            SrsCard.kind == kind,
            SrsCard.scenario_id == scenario.id,
            SrsCard.phrase_id == phrase.id,
        )
    )
    if not card:
        card = SrsCard(
            user_id=user.id,
            kind=kind,
            scenario_id=scenario.id,
            phrase_id=phrase.id,
            focus_words=[body.focus_word] if body.focus_word else [],
            ease=2.5,
            interval_days=0.0,
            repetitions=0,
            lapses=0,
        )
        db.add(card)
    elif body.focus_word and body.focus_word not in card.focus_words:
        card.focus_words = sorted({*card.focus_words, body.focus_word})
    _, due = srs.schedule(srs.SrsState(), quality=2)
    card.due_at = due
    db.flush()
    db.commit()
    return BookmarkOut(
        saved=True,
        card_id=card.id,
        kind=card.kind,
        focus_words=list(card.focus_words or []),
        next_due_at=due,
        interval_days=0.01,
    )


@router.post("/exercises/{exercise_id}/attempts", response_model=AttemptResult)
async def submit_attempt(
    exercise_id: str,
    audio: UploadFile = File(...),
    debug_transcript: str | None = Form(None),
    user: User = Depends(speech_rate_limit),
    db: Session = Depends(get_db),
    repo: ContentRepository = RepoDep,
    settings: Settings = SettingsDep,
    provider: SpeechProvider = SpeechDep,
):
    ex = resolve_exercise(repo, exercise_id)
    if not ex:
        raise HTTPException(404, "exercise not found")
    return await _grade(ex, audio, debug_transcript, settings, provider, db, user, repo)


@router.get("/review/due", response_model=list[practice.ReviewItem], tags=["review"])
def review_due(limit: int = 20, user: User = Depends(get_current_user), db: Session = Depends(get_db),
               repo: ContentRepository = RepoDep):
    return practice.due_items(db, repo, user.id, max(1, min(limit, 100)))


@router.post("/review/{card_id}/attempts", response_model=AttemptResult, tags=["review"])
async def review_attempt(
    card_id: str,
    audio: UploadFile = File(...),
    debug_transcript: str | None = Form(None),
    user: User = Depends(speech_rate_limit),
    db: Session = Depends(get_db),
    repo: ContentRepository = RepoDep,
    settings: Settings = SettingsDep,
    provider: SpeechProvider = SpeechDep,
):
    card = db.scalar(select(SrsCard).where(SrsCard.id == card_id, SrsCard.user_id == user.id))
    if not card:
        raise HTTPException(404, "card not found")
    ex = practice.card_to_exercise(repo, card)
    if not ex:
        raise HTTPException(410, "content no longer available")
    return await _grade(ex, audio, debug_transcript, settings, provider, db, user, repo)


@router.get("/progress", response_model=practice.Progress, tags=["progress"])
def get_progress(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return practice.progress(db, user.id)

