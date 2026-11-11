"""Deterministic provider for local QA: the client sends the transcript it wants to simulate."""

from app.speech.base import SpeechResult


class MockSpeechProvider:
    name = "mock"

    async def transcribe(self, audio, content_type, expected_text=None, debug_transcript=None) -> SpeechResult:
        return SpeechResult(transcript=debug_transcript or "", confidence=None)
