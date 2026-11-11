from functools import lru_cache

from app.core.config import get_settings
from app.speech.base import SpeechProvider
from app.speech.mock import MockSpeechProvider


@lru_cache
def get_speech_provider() -> SpeechProvider:
    s = get_settings()
    if s.speech_provider == "google_cloud":
        from app.speech.google_cloud import GoogleCloudSpeechProvider

        if not s.google_cloud_api_key:
            raise RuntimeError("GOOGLE_CLOUD_API_KEY is required for google_cloud speech provider")
        return GoogleCloudSpeechProvider(s.google_cloud_api_key)
    if s.speech_provider == "openai_whisper":
        from app.speech.openai_whisper import OpenAIWhisperProvider

        if not s.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for openai_whisper")
        return OpenAIWhisperProvider(s.openai_api_key)
    return MockSpeechProvider()

