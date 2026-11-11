class MockLLMProvider:
    """Returns the scripted line verbatim: deterministic for QA."""

    name = "mock"

    async def roleplay_reply(self, ctx) -> str:
        return ctx.next_scripted_line or "Thank you! That's the end of our conversation."
