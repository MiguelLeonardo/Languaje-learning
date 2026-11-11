from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.api.deps import RepoDep
from app.content.repository import ContentRepository
from app.core.config import Settings, get_settings
from app.core.security import create_token, get_current_user, speech_rate_limit
from app.db.models import RoleplaySession, SrsCard, User
from app.db.session import get_db
from app.speech.google_cloud import synthesize_google_tts
from app.speech.tts import synthesize_elevenlabs_tts, synthesize_openai_tts

router = APIRouter()
STATIC_DIR = Path(__file__).resolve().parents[2] / "static"
STATIC_INDEX = STATIC_DIR / "index.html"
STATIC_FIREBASE_CFG = STATIC_DIR / "firebase-config.js"


@router.get("/", include_in_schema=False)
def ui_index() -> FileResponse:
    return FileResponse(STATIC_INDEX, media_type="text/html")


@router.get("/firebase-config.js", include_in_schema=False)
def firebase_config_js() -> FileResponse:
    return FileResponse(STATIC_FIREBASE_CFG, media_type="application/javascript")


@router.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok"}


@router.get("/ready", tags=["system"])
def ready(db: Session = Depends(get_db), repo: ContentRepository = RepoDep) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ready", "scenarios": len(repo.list())}


@router.get("/v1/providers/status", tags=["system"])
def providers_status(
    settings: Settings = Depends(get_settings),
    x_google_cloud_key: str | None = Header(default=None),
    x_gemini_key: str | None = Header(default=None),
    x_openai_key: str | None = Header(default=None),
    x_elevenlabs_key: str | None = Header(default=None),
    x_anthropic_key: str | None = Header(default=None),
) -> dict:
    has_google = bool(x_google_cloud_key or settings.google_cloud_api_key)
    has_gemini = bool(x_gemini_key or settings.gemini_api_key)
    has_openai = bool(x_openai_key or settings.openai_api_key)
    has_elevenlabs = bool(x_elevenlabs_key or settings.elevenlabs_api_key)
    has_anthropic = bool(x_anthropic_key or settings.anthropic_api_key)
    return {
        "speech_provider": (
            "openai_whisper"
            if has_openai
            else ("google_cloud" if has_google else settings.speech_provider)
        ),
        "tts_provider": (
            "elevenlabs"
            if has_elevenlabs
            else ("openai_tts" if has_openai else ("google_cloud" if has_google else settings.tts_provider))
        ),
        "llm_provider": (
            "anthropic" if has_anthropic else ("gemini" if has_gemini else settings.llm_provider)
        ),
        "has_google_cloud_key": has_google,
        "has_gemini_key": has_gemini,
        "has_openai_key": has_openai,
        "has_elevenlabs_key": has_elevenlabs,
        "has_anthropic_key": has_anthropic,
    }


@router.get("/v1/freemium/status", tags=["system"])
def freemium_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    x_freemium_tier: str | None = Header(default=None),
) -> dict:
    tier = (x_freemium_tier or "free").lower()
    if tier not in ("free", "pro"):
        tier = "free"
    day_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    used_today = (
        db.scalar(
            select(func.count(RoleplaySession.id)).where(
                RoleplaySession.user_id == user.id,
                RoleplaySession.created_at >= day_start,
            )
        )
        or 0
    )
    limit = 999 if tier == "pro" else settings.free_daily_roleplays
    return {
        "tier": tier,
        "daily_roleplays_used": int(used_today),
        "daily_roleplays_limit": limit,
        "can_start_roleplay": tier == "pro" or used_today < limit,
        "free_tier_providers": {
            "auth": "firebase_anonymous",
            "database": "cloud_firestore",
            "stt": "google_cloud_stt (60 min/mes gratis) + webspeech",
            "tts": "google_cloud_tts (4M chars/mes gratis) + webspeech",
            "llm": f"{settings.gemini_model} (Google AI Studio Free Tier)",
        },
    }


class TtsRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    voice: str | None = None


@router.post("/v1/tts", tags=["speech"])
async def synthesize_speech(
    body: TtsRequest,
    _user: User = Depends(speech_rate_limit),
    settings: Settings = Depends(get_settings),
    x_google_cloud_key: str | None = Header(default=None),
    x_openai_key: str | None = Header(default=None),
    x_elevenlabs_key: str | None = Header(default=None),
) -> Response:
    eleven_key = x_elevenlabs_key or settings.elevenlabs_api_key
    openai_key = x_openai_key or settings.openai_api_key
    google_key = x_google_cloud_key or settings.google_cloud_api_key
    if eleven_key:
        audio = await synthesize_elevenlabs_tts(body.text, eleven_key, body.voice or settings.elevenlabs_voice_id)
        return Response(content=audio, media_type="audio/mpeg")
    if openai_key:
        audio = await synthesize_openai_tts(body.text, openai_key, body.voice or settings.openai_tts_voice)
        return Response(content=audio, media_type="audio/mpeg")
    if google_key:
        audio = await synthesize_google_tts(body.text, google_key, body.voice or settings.google_tts_voice)
        return Response(content=audio, media_type="audio/mpeg")
    raise HTTPException(
        400,
        "No Speaker TTS API key configured (set GOOGLE_CLOUD_API_KEY, OPENAI_API_KEY, or ELEVENLABS_API_KEY)",
    )


class DevTokenIn(BaseModel):
    user_id: str = "dev-user"


@router.post("/v1/auth/dev-token", tags=["auth"])
def dev_token(body: DevTokenIn, settings: Settings = Depends(get_settings)) -> dict:
    """Local/test only. Staging/production use an external IdP (Firebase Auth / Cognito) issuing JWTs."""
    if not settings.is_dev:
        raise HTTPException(404, "not found")
    return {"access_token": create_token(body.user_id, settings), "token_type": "bearer"}


@router.post("/v1/dev/fast-forward-srs", tags=["dev"])
def fast_forward_srs(
    minutes: int = 15,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Local/test helper to fast-forward due_at on SRS cards for immediate UI review."""
    if not settings.is_dev:
        raise HTTPException(404, "not found")
    cards = db.scalars(select(SrsCard).where(SrsCard.user_id == user.id)).all()
    for card in cards:
        card.due_at = card.due_at - timedelta(minutes=minutes)
    db.commit()
    return {"updated": len(cards)}
