"""Neural Speaker (TTS) synthesis adapters for OpenAI TTS and ElevenLabs."""

import httpx


async def synthesize_openai_tts(text: str, api_key: str, voice: str = "nova", timeout: float = 20.0) -> bytes:
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(
            "https://api.openai.com/v1/audio/speech",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": "tts-1", "voice": voice, "input": text, "response_format": "mp3"},
        )
        r.raise_for_status()
        return r.content


async def synthesize_elevenlabs_tts(
    text: str, api_key: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM", timeout: float = 20.0
) -> bytes:
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": api_key, "Accept": "audio/mpeg"},
            json={"text": text, "model_id": "eleven_multilingual_v2"},
        )
        r.raise_for_status()
        return r.content
