"""OpenAI transcription adapter (used in staging/production behind SPEECH_PROVIDER=openai_whisper)."""

import math

import httpx

from app.speech.base import SpeechResult


class OpenAIWhisperProvider:
    name = "openai_whisper"
    url = "https://api.openai.com/v1/audio/transcriptions"

    def __init__(self, api_key: str, model: str = "whisper-1", timeout: float = 30.0):
        self._key, self._model, self._timeout = api_key, model, timeout

    async def transcribe(self, audio, content_type, expected_text=None, debug_transcript=None) -> SpeechResult:
        data = {"model": self._model, "language": "en", "response_format": "verbose_json"}
        if expected_text:
            data["prompt"] = expected_text  # biases recognition toward the target vocabulary
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(self.url, headers={"Authorization": f"Bearer {self._key}"},
                                  data=data, files={"file": ("answer", audio, content_type)})
            r.raise_for_status()
            body = r.json()
        segments = body.get("segments") or []
        conf = None
        if segments:
            avg_logprob = sum(s.get("avg_logprob", 0.0) for s in segments) / len(segments)
            conf = round(max(0.0, min(1.0, math.exp(avg_logprob))), 3)
        return SpeechResult(transcript=body.get("text", "").strip(), confidence=conf)
