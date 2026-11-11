from fastapi import Depends, Header, HTTPException, UploadFile, status

from app.content.repository import ContentRepository, get_repository
from app.core.config import Settings, get_settings
from app.llm.base import LLMProvider
from app.llm.factory import get_llm_provider
from app.speech.base import SpeechProvider, SpeechResult
from app.speech.factory import get_speech_provider


def repo_dep() -> ContentRepository:
    return get_repository()


def resolve_speech_provider(
    provider: SpeechProvider = Depends(get_speech_provider),
    x_google_cloud_key: str | None = Header(default=None),
    x_openai_key: str | None = Header(default=None),
) -> SpeechProvider:
    if x_google_cloud_key:
        from app.speech.google_cloud import GoogleCloudSpeechProvider

        return GoogleCloudSpeechProvider(x_google_cloud_key)
    if x_openai_key:
        from app.speech.openai_whisper import OpenAIWhisperProvider

        return OpenAIWhisperProvider(x_openai_key)
    return provider


def resolve_llm_provider(
    llm: LLMProvider = Depends(get_llm_provider),
    settings: Settings = Depends(get_settings),
    x_gemini_key: str | None = Header(default=None),
    x_anthropic_key: str | None = Header(default=None),
) -> LLMProvider:
    if x_gemini_key:
        from app.llm.gemini import GeminiLLMProvider

        return GeminiLLMProvider(x_gemini_key, settings.gemini_model)
    if x_anthropic_key:
        from app.llm.anthropic_claude import AnthropicClaudeProvider

        return AnthropicClaudeProvider(x_anthropic_key, settings.anthropic_model)
    return llm


async def read_audio(audio: UploadFile, settings: Settings) -> bytes:
    ctype = (audio.content_type or "").split(";")[0].strip().lower()
    if ctype not in settings.allowed_audio_types:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"unsupported audio type '{ctype}'")
    data = await audio.read(settings.max_audio_bytes + 1)
    if len(data) > settings.max_audio_bytes:
        raise HTTPException(413, "audio too large")
    if not data:
        raise HTTPException(422, "empty audio")
    return data


async def transcribe_answer(
    audio: UploadFile, expected_text: str | None, debug_transcript: str | None,
    settings: Settings, provider: SpeechProvider,
) -> SpeechResult:
    data = await read_audio(audio, settings)
    if debug_transcript and provider.name != "mock":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "debug_transcript only allowed with the mock provider")
    ctype = (audio.content_type or "").split(";")[0].strip().lower()
    return await provider.transcribe(data, ctype, expected_text=expected_text, debug_transcript=debug_transcript)


SettingsDep = Depends(get_settings)
SpeechDep = Depends(resolve_speech_provider)
LLMDep = Depends(resolve_llm_provider)
RepoDep = Depends(repo_dep)

