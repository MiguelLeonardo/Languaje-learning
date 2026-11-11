"""Claude adapter (Anthropic Messages API) for the scripted roleplay."""

from pathlib import Path

import httpx

from app.llm.base import RoleplayContext

PROMPT = (Path(__file__).parent / "prompts" / "roleplay_v1.txt").read_text(encoding="utf-8")


class AnthropicClaudeProvider:
    name = "anthropic"
    url = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str, model: str, timeout: float = 20.0):
        self._key, self._model, self._timeout = api_key, model, timeout

    async def roleplay_reply(self, ctx: RoleplayContext) -> str:
        system = PROMPT.format(
            ai_role=ctx.ai_role, cefr=ctx.cefr, scenario_title=ctx.scenario_title, setting=ctx.setting,
            user_role=ctx.user_role, next_scripted_line=ctx.next_scripted_line or "Wrap up the conversation politely.",
        )
        messages = [
            {"role": "assistant" if h["speaker"] == "ai" else "user", "content": h["text"]} for h in ctx.history
        ]
        messages.append({"role": "user", "content": ctx.user_utterance})
        if messages[0]["role"] == "assistant":
            messages.insert(0, {"role": "user", "content": "(start)"})
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(
                self.url,
                headers={"x-api-key": self._key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": self._model, "max_tokens": 120, "system": system, "messages": messages},
            )
            r.raise_for_status()
            body = r.json()
        text = "".join(b.get("text", "") for b in body.get("content", []) if b.get("type") == "text").strip()
        return text or (ctx.next_scripted_line or "")
