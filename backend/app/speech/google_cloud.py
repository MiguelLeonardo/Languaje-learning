"""Google Cloud Speech-to-Text (60 min/mo Free Tier) and Text-to-Speech (4M chars/mo Free Tier) adapters."""

import base64

import httpx

from app.speech.base import SpeechResult


class GoogleCloudSpeechProvider:
    name = "google_cloud"
    url = "https://speech.googleapis.com/v1/speech:recognize"

    def __init__(self, api_key: str, timeout: float = 25.0):
        self._key = api_key
        self._timeout = timeout

    async def transcribe(
        self, audio: bytes, content_type: str, expected_text: str | None = None, debug_transcript: str | None = None
    ) -> SpeechResult:
        b64 = base64.b64encode(audio).decode("ascii")
        speech_contexts = [{"phrases": [expected_text], "boost": 15.0}] if expected_text else []
        payload = {
            "config": {
                "languageCode": "en-US",
                "enableAutomaticPunctuation": True,
                "enableWordConfidence": True,
                "speechContexts": speech_contexts,
            },
            "audio": {"content": b64},
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(f"{self.url}?key={self._key}", json=payload)
            r.raise_for_status()
            body = r.json()
        results = body.get("results") or []
        if not results or not results[0].get("alternatives"):
            return SpeechResult(transcript="", confidence=0.0)
        alt = results[0]["alternatives"][0]
        return SpeechResult(
            transcript=alt.get("transcript", "").strip(),
            confidence=round(float(alt.get("confidence", 0.9)), 3),
        )


async def synthesize_google_tts(
    text: str, api_key: str, voice_name: str = "en-US-Wavenet-F", timeout: float = 20.0
) -> bytes:
    """Synthesizes speech using Google Cloud Text-to-Speech (Free Tier: 4M Standard / 1M WaveNet chars/month)."""
    payload = {
        "input": {"text": text},
        "voice": {"languageCode": "en-US", "name": voice_name},
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": 0.96},
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(
            f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}",
            json=payload,
        )
        r.raise_for_status()
        b64 = r.json().get("audioContent", "")
        return base64.b64decode(b64)
