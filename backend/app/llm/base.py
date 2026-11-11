"""LLM provider interface for the scripted AI conversation."""

from typing import Protocol

from pydantic import BaseModel


class RoleplayContext(BaseModel):
    scenario_title: str
    cefr: str
    setting: str
    ai_role: str
    user_role: str
    history: list[dict]  # [{"speaker": "ai"|"user", "text": str}]
    user_utterance: str
    next_scripted_line: str | None  # the line the script expects the AI to say next


class LLMProvider(Protocol):
    name: str

    async def roleplay_reply(self, ctx: RoleplayContext) -> str: ...
