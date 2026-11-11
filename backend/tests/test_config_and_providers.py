import asyncio

import pytest

from app.core.config import Settings, get_settings
from app.llm.base import RoleplayContext
from app.llm.mock import MockLLMProvider


def test_production_guards(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        get_settings()
    get_settings.cache_clear()
    monkeypatch.setenv("JWT_SECRET", "x" * 40)
    with pytest.raises(RuntimeError, match="Mock speech"):
        get_settings()
    get_settings.cache_clear()
    monkeypatch.setenv("SPEECH_PROVIDER", "openai_whisper")
    assert get_settings().env == "production"
    get_settings.cache_clear()


def test_dev_token_disabled_outside_dev(client):
    client.app.dependency_overrides[get_settings] = lambda: Settings(env="staging", jwt_secret="y" * 40)
    assert client.post("/v1/auth/dev-token", json={}).status_code == 404
    client.app.dependency_overrides.clear()


def test_factories_require_keys(monkeypatch):
    from app.llm.factory import get_llm_provider
    from app.speech.factory import get_speech_provider

    for f in (get_settings, get_llm_provider, get_speech_provider):
        f.cache_clear()
    monkeypatch.setenv("SPEECH_PROVIDER", "openai_whisper")
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    with pytest.raises(RuntimeError):
        get_speech_provider()
    with pytest.raises(RuntimeError):
        get_llm_provider()
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    for f in (get_settings, get_llm_provider, get_speech_provider):
        f.cache_clear()
    assert get_speech_provider().name == "openai_whisper"
    assert get_llm_provider().name == "anthropic"
    for f in (get_settings, get_llm_provider, get_speech_provider):
        f.cache_clear()


def test_mock_llm_fallback():
    ctx = RoleplayContext(scenario_title="t", cefr="A1", setting="s", ai_role="a", user_role="u", history=[],
                          user_utterance="hi", next_scripted_line=None)
    assert "end" in asyncio.run(MockLLMProvider().roleplay_reply(ctx))
