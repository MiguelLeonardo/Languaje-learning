"""Application settings (12-factor: everything comes from environment variables)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
DEV_JWT_SECRET = "local-dev-only-secret-change-me-0123456789"  # noqa: S105 - rejected outside local/test


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: Literal["local", "test", "staging", "production"] = "local"
    database_url: str = "sqlite:///./languaje.db"
    content_dir: Path = ROOT_DIR / "content" / "scenarios"

    # Auth
    jwt_secret: str = DEV_JWT_SECRET  # overridden via Secret Manager outside local
    jwt_issuer: str = "languaje-learning"
    jwt_ttl_minutes: int = 60 * 24

    # Providers (Speech STT, Speaker TTS, Roleplay LLM — Google Cloud & Gemini Free Tier first)
    speech_provider: Literal["mock", "google_cloud", "openai_whisper"] = "mock"
    tts_provider: Literal["browser", "google_cloud", "openai_tts", "elevenlabs"] = "browser"
    llm_provider: Literal["mock", "gemini", "anthropic"] = "mock"
    google_cloud_api_key: str | None = None
    google_tts_voice: str = "en-US-Wavenet-F"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    openai_api_key: str | None = None
    openai_tts_voice: str = "nova"
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5"

    # Freemium quotas
    free_daily_roleplays: int = 3

    # Audio upload limits
    max_audio_bytes: int = 5 * 1024 * 1024
    allowed_audio_types: tuple[str, ...] = (
        "audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp4", "audio/m4a", "audio/x-m4a",
        "audio/aac", "audio/webm", "audio/ogg",
    )
    persist_audio: bool = False  # privacy by default

    cors_origins: list[str] = [
        "http://localhost:8081",
        "http://localhost:19006",
        "http://localhost:5000",
        "https://languaje-learning.web.app",
        "https://languaje-learning.firebaseapp.com",
    ]

    @property
    def is_dev(self) -> bool:
        return self.env in ("local", "test")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.is_dev and (settings.jwt_secret == DEV_JWT_SECRET or len(settings.jwt_secret) < 32):
        raise RuntimeError("JWT_SECRET (>=32 chars) must be configured outside local/test environments")
    if not settings.is_dev and settings.speech_provider == "mock":
        raise RuntimeError("Mock speech provider is not allowed outside local/test")
    return settings
