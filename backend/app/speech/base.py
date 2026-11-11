"""Speech-to-text / pronunciation provider interface."""

from typing import Protocol

from pydantic import BaseModel


class SpeechResult(BaseModel):
    transcript: str
    confidence: float | None = None  # 0..1 pronunciation/recognition confidence


class SpeechProvider(Protocol):
    name: str

    async def transcribe(
        self, audio: bytes, content_type: str, expected_text: str | None = None,
        debug_transcript: str | None = None,
    ) -> SpeechResult: ...
