from functools import lru_cache

from app.core.config import get_settings
from app.llm.base import LLMProvider
from app.llm.mock import MockLLMProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    s = get_settings()
    if s.llm_provider == "gemini":
        from app.llm.gemini import GeminiLLMProvider

        if not s.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required for the gemini provider")
        return GeminiLLMProvider(s.gemini_api_key, s.gemini_model)
    if s.llm_provider == "anthropic":
        from app.llm.anthropic_claude import AnthropicClaudeProvider

        if not s.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for the anthropic provider")
        return AnthropicClaudeProvider(s.anthropic_api_key, s.anthropic_model)
    return MockLLMProvider()

