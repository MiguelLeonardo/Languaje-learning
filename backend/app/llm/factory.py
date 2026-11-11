from functools import lru_cache

from app.core.config import get_settings
from app.llm.base import LLMProvider
from app.llm.mock import MockLLMProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    s = get_settings()
    if s.llm_provider == "anthropic":
        from app.llm.anthropic_claude import AnthropicClaudeProvider

        if not s.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for the anthropic provider")
        return AnthropicClaudeProvider(s.anthropic_api_key, s.anthropic_model)
    return MockLLMProvider()
