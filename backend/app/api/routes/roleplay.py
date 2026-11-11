from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import LLMDep, RepoDep, SettingsDep, SpeechDep, transcribe_answer
from app.content.repository import ContentRepository
from app.core.config import Settings
from app.core.security import speech_rate_limit
from app.db.models import RoleplaySession, User
from app.db.session import get_db
from app.llm.base import LLMProvider
from app.services import roleplay
from app.speech.base import SpeechProvider

router = APIRouter(prefix="/v1/roleplay", tags=["roleplay"])


@router.post("/{scenario_id}/sessions", response_model=roleplay.RoleplayState)
def start_session(scenario_id: str, user: User = Depends(speech_rate_limit), db: Session = Depends(get_db),
                  repo: ContentRepository = RepoDep):
    s = repo.get(scenario_id)
    if not s:
        raise HTTPException(404, "scenario not found")
    return roleplay.start(db, user.id, s)


@router.post("/sessions/{session_id}/turns", response_model=roleplay.RoleplayState)
async def submit_turn(
    session_id: str,
    audio: UploadFile = File(...),
    debug_transcript: str | None = Form(None),
    user: User = Depends(speech_rate_limit),
    db: Session = Depends(get_db),
    repo: ContentRepository = RepoDep,
    settings: Settings = SettingsDep,
    provider: SpeechProvider = SpeechDep,
    llm: LLMProvider = LLMDep,
):
    session = db.scalar(select(RoleplaySession).where(RoleplaySession.id == session_id,
                                                      RoleplaySession.user_id == user.id))
    if not session:
        raise HTTPException(404, "session not found")
    if session.status != "active":
        raise HTTPException(409, "session already completed")
    scenario = repo.get(session.scenario_id)
    if not scenario:
        raise HTTPException(410, "content no longer available")
    pending = scenario.roleplay.turns[session.turn_index]
    speech = await transcribe_answer(audio, pending.suggested_lines[0], debug_transcript, settings, provider)
    return await roleplay.submit(db, session, scenario, speech.transcript, llm)
