"""Google Gemini Flash adapter (Free Tier via Google AI Studio / Vertex AI in Firebase)."""

from pathlib import Path

import httpx

from app.llm.base import RoleplayContext

PROMPT = (Path(__file__).parent / "prompts" / "roleplay_v1.txt").read_text(encoding="utf-8")


class GeminiLLMProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", timeout: float = 20.0):
        self._key = api_key
        self._model = model
        self._timeout = timeout

    async def roleplay_reply(self, ctx: RoleplayContext) -> str:
        system = PROMPT.format(
            ai_role=ctx.ai_role,
            cefr=ctx.cefr,
            scenario_title=ctx.scenario_title,
            setting=ctx.setting,
            user_role=ctx.user_role,
            next_scripted_line=ctx.next_scripted_line or "Wrap up the conversation politely.",
        )
        contents = [
            {
                "role": "model" if h["speaker"] == "ai" else "user",
                "parts": [{"text": h["text"]}],
            }
            for h in ctx.history
        ]
        contents.append({"role": "user", "parts": [{"text": ctx.user_utterance}]})
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent?key={self._key}"
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": contents,
            "generationConfig": {"maxOutputTokens": 120, "temperature": 0.4},
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            body = r.json()
        candidates = body.get("candidates") or []
        if candidates:
            parts = candidates[0].get("content", {}).get("parts") or []
            text = "".join(p.get("text", "") for p in parts).strip()
            if text:
                return text
        return ctx.next_scripted_line or "Thank you! Great conversation."
