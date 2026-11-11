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
from app.services import practice
from app.services.evaluation import Evaluation, evaluate
from app.services.exercises import Exercise, resolve_exercise
from app.services.feedback import Feedback, build_feedback
from app.speech.base import SpeechProvider

router = APIRouter(prefix="/v1", tags=["practice"])


class AttemptResult(BaseModel):
    exercise: Exercise
    evaluation: Evaluation
    feedback: Feedback
    srs: list[practice.SrsUpdate]


async def _grade(ex: Exercise, audio, debug_transcript, settings, provider, db, user, repo) -> AttemptResult:
    speech = await transcribe_answer(audio, ex.expected_text, debug_transcript, settings, provider)
    ev = evaluate(ex.expected_text, speech.transcript, ex.pass_threshold, speech.confidence)
    fb = build_feedback(ev, repo.phrase(ex.scenario_id, ex.phrase_id))
    updates = practice.record_attempt(db, user.id, ex, ev, fb)
    return AttemptResult(exercise=ex, evaluation=ev, feedback=fb, srs=updates)


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
