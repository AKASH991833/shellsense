from __future__ import annotations

from shellsense.ai.analytics import AIAnalytics
from shellsense.ai.cache import AICache
from shellsense.ai.config import (
    DEFAULT_AI_CONFIG,
    get_available_providers,
    get_provider_config,
)
from shellsense.ai.context import AIContext
from shellsense.ai.memory import AIMemory
from shellsense.ai.middleware import MiddlewarePipeline
from shellsense.ai.prompts import PromptEngine
from shellsense.ai.providers.base import (
    AIResponse,
    ModelInfo,
    ProviderConfig,
    TokenUsage,
)
from shellsense.ai.providers.local_provider import LocalProvider
from shellsense.ai.security import get_api_key, has_api_key, set_api_key
from shellsense.ai.session import Conversation, SessionManager
from shellsense.ai.streaming import (
    build_streaming_response,
    simulate_streaming,
)
from shellsense.ai.tokenizer import TokenTracker, UsageRecord


class TestAIProviderBase:
    def test_provider_config_defaults(self) -> None:
        config = ProviderConfig()
        assert config.api_key == ""
        assert config.temperature == 0.3
        assert config.max_tokens == 1024

    def test_ai_response_defaults(self) -> None:
        resp = AIResponse()
        assert resp.content == ""
        assert resp.finished is True

    def test_token_usage_defaults(self) -> None:
        usage = TokenUsage()
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0

    def test_model_info_defaults(self) -> None:
        info = ModelInfo()
        assert info.id == ""
        assert info.provider == ""


class TestLocalProvider:
    def test_provider_info(self) -> None:
        provider = LocalProvider()
        info = provider.info
        assert info.name == "local"
        assert info.offline is True
        assert info.requires_api_key is False

    def test_health_check(self) -> None:
        provider = LocalProvider()
        assert provider.health_check() is False

    def test_get_models(self) -> None:
        provider = LocalProvider()
        models = provider.get_models()
        assert len(models) == 1
        assert models[0].id == "local"

    def test_generate_raises(self) -> None:
        provider = LocalProvider()
        import pytest

        with pytest.raises(Exception):
            provider.generate("test")


class TestAICache:
    def test_set_and_get(self) -> None:
        cache = AICache(max_memory=100, ttl=300.0, use_disk=False)
        response = AIResponse(content="hello", model="test", provider="test")
        cache.set("hello", response)
        cached = cache.get("hello")
        assert cached is not None
        assert cached.content == "hello"

    def test_miss_returns_none(self) -> None:
        cache = AICache(max_memory=100, ttl=300.0, use_disk=False)
        cached = cache.get("nonexistent")
        assert cached is None

    def test_clear(self) -> None:
        cache = AICache(max_memory=100, ttl=300.0, use_disk=False)
        response = AIResponse(content="hello", model="test", provider="test")
        cache.set("hello", response)
        cache.clear()
        assert cache.get("hello") is None

    def test_invalidate(self) -> None:
        cache = AICache(max_memory=100, ttl=300.0, use_disk=False)
        response = AIResponse(content="hello", model="test", provider="test")
        cache.set("hello", response)
        cache.invalidate("hello")
        assert cache.get("hello") is None

    def test_expiry(self) -> None:
        cache = AICache(max_memory=100, ttl=0, use_disk=False)
        response = AIResponse(content="hello", model="test", provider="test")
        cache.set("hello", response)
        import time

        time.sleep(0.01)
        assert cache.get("hello") is None


class TestSession:
    def test_create_conversation(self) -> None:
        conv = Conversation(provider="test", model="test-model")
        assert conv.session_id
        assert conv.provider == "test"
        assert conv.model == "test-model"

    def test_add_message(self) -> None:
        conv = Conversation()
        conv.add_message("user", "hello")
        conv.add_message("assistant", "hi")
        assert len(conv.messages) == 2
        assert conv.messages[0]["role"] == "user"

    def test_to_from_dict(self) -> None:
        conv = Conversation(provider="test", model="m")
        conv.add_message("user", "hello")
        data = conv.to_dict()
        restored = Conversation.from_dict(data)
        assert restored.provider == "test"
        assert len(restored.messages) == 1

    def test_session_manager(self) -> None:
        mgr = SessionManager()
        conv = mgr.create_session(provider="test")
        assert mgr.get_active_session() is not None
        assert mgr.get_session(conv.session_id) is not None

    def test_list_sessions(self) -> None:
        mgr = SessionManager()
        mgr.create_session(provider="p1")
        mgr.create_session(provider="p2")
        sessions = mgr.list_sessions()
        assert len(sessions) >= 2

    def test_delete_session(self) -> None:
        mgr = SessionManager()
        conv = mgr.create_session()
        mgr.delete_session(conv.session_id)
        assert mgr.get_active_session() is None

    def test_clear_all_sessions(self) -> None:
        mgr = SessionManager()
        mgr.create_session()
        mgr.create_session()
        mgr.clear_all_sessions()
        assert mgr.get_active_session() is None


class TestTokenTracker:
    def test_record_usage(self) -> None:
        tracker = TokenTracker()
        tracker.record_usage(
            UsageRecord(
                provider="test", input_tokens=10, output_tokens=5, total_tokens=15
            )
        )
        daily = tracker.get_daily_usage()
        assert daily["total_tokens"] == 15

    def test_estimate_cost(self) -> None:
        tracker = TokenTracker()
        cost = tracker.estimate_cost("openai", 1000, 500)
        assert cost > 0

    def test_ollama_cost_free(self) -> None:
        tracker = TokenTracker()
        cost = tracker.estimate_cost("ollama", 1000, 500)
        assert cost == 0.0

    def test_provider_usage(self) -> None:
        tracker = TokenTracker()
        tracker.record_usage(
            UsageRecord(
                provider="test_p", input_tokens=50, output_tokens=25, total_tokens=75
            )
        )
        usage = tracker.get_provider_usage()
        assert "test_p" in usage
        assert usage["test_p"]["total_tokens"] == 75


class TestSecurity:
    def test_has_api_key_no_config(self) -> None:
        assert has_api_key("nonexistent") is False

    def test_set_and_get_api_key(self) -> None:
        set_api_key("test_provider", "test-key-123")
        key = get_api_key("test_provider")
        assert key == "test-key-123"
        set_api_key("test_provider", "")


class TestPromptEngine:
    def test_system_prompt_default(self) -> None:
        engine = PromptEngine()
        prompt = engine.get_system_prompt()
        assert "ShellSense" in prompt

    def test_system_prompt_style(self) -> None:
        engine = PromptEngine()
        prompt = engine.get_system_prompt("expert")
        assert "expert" in prompt.lower()

    def test_create_command_explain_prompt(self) -> None:
        engine = PromptEngine()
        prompt = engine.create_command_explain_prompt("ls")
        assert "ls" in prompt

    def test_render_template(self) -> None:
        engine = PromptEngine()
        engine.register_template("test", "Hello {name}")
        engine.set_variable("name", "World")
        result = engine.render("test")
        assert result == "Hello World"

    def test_render_with_variables(self) -> None:
        engine = PromptEngine()
        engine.register_template("greet", "Hi {user}")
        result = engine.render("greet", {"user": "Alice"})
        assert result == "Hi Alice"


class TestAIContext:
    def test_system_context(self) -> None:
        ctx = AIContext()
        sys_ctx = ctx.collect_system_context()
        assert "os" in sys_ctx
        assert "python_version" in sys_ctx

    def test_shell_context(self) -> None:
        ctx = AIContext()
        shell_ctx = ctx.collect_shell_context()
        assert "shell" in shell_ctx

    def test_set_and_get(self) -> None:
        ctx = AIContext()
        ctx.set("key", "value")
        assert ctx.get("key") == "value"

    def test_permission(self) -> None:
        ctx = AIContext()
        assert ctx.has_permission is False
        ctx.grant_permission()
        assert ctx.has_permission is True

    def test_context_summary(self) -> None:
        ctx = AIContext()
        ctx.set("os", "linux")
        summary = ctx.get_context_summary()
        assert "linux" in summary


class TestAIMemory:
    def test_enable_disable(self) -> None:
        mem = AIMemory()
        assert mem.enabled is True
        mem.disable()
        assert mem.enabled is False
        mem.enable()
        assert mem.enabled is True

    def test_set_preference(self) -> None:
        mem = AIMemory()
        mem.set_preference("theme", "dark")
        assert mem.get_preference("theme") == "dark"

    def test_session_data(self) -> None:
        mem = AIMemory()
        mem.set_session_data("key", "val")
        assert mem.get_session_data("key") == "val"

    def test_temporary_data(self) -> None:
        mem = AIMemory()
        mem.set_temporary("key", "tmp")
        assert mem.get_temporary("key") == "tmp"

    def test_clear(self) -> None:
        mem = AIMemory()
        mem.set_preference("x", "y")
        mem.clear()
        assert mem.get_preference("x") is None

    def test_export_import(self) -> None:
        mem = AIMemory()
        mem.set_preference("lang", "en")
        data = mem.export_data()
        assert "preferences" in data
        assert data["preferences"]["lang"] == "en"

        mem2 = AIMemory()
        mem2.import_data(data)
        assert mem2.get_preference("lang") == "en"


class TestStreaming:
    def test_simulate_streaming(self) -> None:
        chunks = list(simulate_streaming("hello", chunk_size=2))
        assert len(chunks) >= 2
        assert "".join(chunks) == "hello"

    def test_build_streaming_response(self) -> None:
        chunks = ["hello", " ", "world"]
        response = build_streaming_response(chunks)
        assert response.content == "hello world"


class TestAnalytics:
    def test_get_summary(self) -> None:
        tracker = TokenTracker()
        tracker.record_usage(
            UsageRecord(provider="test", input_tokens=10, output_tokens=5)
        )
        analytics = AIAnalytics(tracker)
        summary = analytics.get_summary()
        assert "daily" in summary
        assert "monthly" in summary
        assert "providers" in summary


class TestMiddleware:
    def test_pipeline(self) -> None:
        pipeline = MiddlewarePipeline()
        calls: list[str] = []

        def before(p: str, s: str) -> None:
            calls.append("before")

        def after(p: str, s: str, r: AIResponse) -> None:
            calls.append("after")

        pipeline.add_before(before)
        pipeline.add_after(after)

        pipeline.run_before("test", "")
        pipeline.run_after("test", "", AIResponse(content="ok"))

        assert "before" in calls
        assert "after" in calls


class TestAIConfig:
    def test_default_config_exists(self) -> None:
        assert "default_provider" in DEFAULT_AI_CONFIG
        assert "providers" in DEFAULT_AI_CONFIG

    def test_get_available_providers(self) -> None:
        providers = get_available_providers()
        assert "openai" in providers
        assert "gemini" in providers
        assert "ollama" in providers

    def test_get_provider_config_defaults(self) -> None:
        config = get_provider_config("openai")
        assert isinstance(config, dict)
