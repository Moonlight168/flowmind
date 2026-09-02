"""
FlowMind 智能流程设计服务 - 模型运行时单元测试

通过公开 interface 验证运行时 Provider 降级行为。
"""

from contextlib import contextmanager

import pytest

from app.llm.runtime import (
    ModelExhaustedError,
    ModelRuntime,
    ModelRuntimeConfig,
    PartialStreamError,
)


class _FakeModel:
    def __init__(self, provider: str, calls: list[str]) -> None:
        self.provider = provider
        self.calls = calls

    def invoke(self, messages: list[dict[str, str]]) -> str:
        self.calls.append(self.provider)
        if self.provider == "primary":
            raise ConnectionError("primary unavailable")
        return "fallback ok"

    def stream(self, messages: list[dict[str, str]], config=None):
        self.calls.append(self.provider)
        if self.provider == "primary":
            raise ConnectionError("primary unavailable")
        yield "fallback"
        yield " ok"


class _PartialStreamModel:
    def __init__(self, provider: str, calls: list[str]) -> None:
        self.provider = provider
        self.calls = calls

    def stream(self, messages: list[dict[str, str]], config=None):
        self.calls.append(self.provider)
        yield "partial"
        raise ConnectionError("stream interrupted")


def test_execute_switches_provider_after_runtime_failure() -> None:
    calls: list[str] = []
    runtime = ModelRuntime(
        providers={
            "primary": {"model_name": "primary-model"},
            "fallback": {"model_name": "fallback-model"},
        },
        priority=["primary", "fallback"],
        config=ModelRuntimeConfig(max_retries=1, retry_interval=0),
        model_builder=lambda provider, _config, _task: _FakeModel(provider, calls),
    )

    result = runtime.execute("chat", lambda model: model.invoke([]))

    assert result == "fallback ok"
    assert calls == ["primary", "fallback"]


def test_stream_switches_provider_before_first_token() -> None:
    calls: list[str] = []
    runtime = ModelRuntime(
        providers={"primary": {}, "fallback": {}},
        priority=["primary", "fallback"],
        config=ModelRuntimeConfig(max_retries=1, retry_interval=0),
        model_builder=lambda provider, _config, _task: _FakeModel(provider, calls),
    )

    chunks = list(runtime.stream("chat", [], config={"callbacks": []}))

    assert chunks == ["fallback", " ok"]
    assert calls == ["primary", "fallback"]


def test_describe_providers_returns_only_safe_runtime_metadata() -> None:
    runtime = ModelRuntime(
        providers={
            "primary": {
                "model_name": "model-a",
                "base_url": "https://private.example/v1",
                "api_key": "secret",
                "supports_structured_output": False,
            },
            "fallback": {
                "model_name": "model-b",
                "supports_structured_output": True,
            },
        },
        priority=["primary", "fallback"],
    )

    assert runtime.describe_providers() == [
        {
            "name": "primary",
            "model": "model-a",
            "priority": 1,
            "supports_structured_output": False,
        },
        {
            "name": "fallback",
            "model": "model-b",
            "priority": 2,
            "supports_structured_output": True,
        },
    ]


def test_execute_respects_disabled_fallback() -> None:
    calls: list[str] = []
    runtime = ModelRuntime(
        providers={"primary": {}, "fallback": {}},
        priority=["primary", "fallback"],
        config=ModelRuntimeConfig(enabled=False, max_retries=10, retry_interval=0),
        model_builder=lambda provider, _config, _task: _FakeModel(provider, calls),
    )

    with pytest.raises(ModelExhaustedError):
        runtime.execute("chat", lambda model: model.invoke([]))

    assert calls == ["primary"]


def test_execute_filters_models_without_structured_output() -> None:
    calls: list[str] = []
    runtime = ModelRuntime(
        providers={
            "plain": {"supports_structured_output": False},
            "structured": {"supports_structured_output": True},
        },
        priority=["plain", "structured"],
        config=ModelRuntimeConfig(max_retries=1, retry_interval=0),
        model_builder=lambda provider, _config, _task: _FakeModel(provider, calls),
    )

    result = runtime.execute("intent", lambda model: model.invoke([]), structured=True)

    assert result == "fallback ok"
    assert calls == ["structured"]


def test_execute_limits_additional_provider_attempts() -> None:
    calls: list[str] = []
    runtime = ModelRuntime(
        providers={"primary": {}, "secondary": {}, "third": {}},
        priority=["primary", "secondary", "third"],
        config=ModelRuntimeConfig(max_retries=1, retry_interval=0),
        model_builder=lambda provider, _config, _task: _FakeModel("primary", calls),
    )

    with pytest.raises(ModelExhaustedError):
        runtime.execute("chat", lambda model: model.invoke([]))

    assert calls == ["primary", "primary"]


def test_execute_waits_configured_interval_before_fallback(monkeypatch) -> None:
    calls: list[str] = []
    waits: list[float] = []
    monkeypatch.setattr("app.llm.runtime.time.sleep", waits.append)
    runtime = ModelRuntime(
        providers={"primary": {}, "fallback": {}},
        priority=["primary", "fallback"],
        config=ModelRuntimeConfig(max_retries=1, retry_interval=0.25),
        model_builder=lambda provider, _config, _task: _FakeModel(provider, calls),
    )

    runtime.execute("chat", lambda model: model.invoke([]))

    assert waits == [0.25]


def test_stream_does_not_replay_after_first_token() -> None:
    calls: list[str] = []
    runtime = ModelRuntime(
        providers={"primary": {}, "fallback": {}},
        priority=["primary", "fallback"],
        config=ModelRuntimeConfig(max_retries=1, retry_interval=0),
        model_builder=lambda provider, _config, _task: _PartialStreamModel(
            provider, calls
        ),
    )

    stream = runtime.stream("chat", [])
    assert next(stream) == "partial"
    with pytest.raises(PartialStreamError, match="流式响应中断"):
        next(stream)

    assert calls == ["primary"]


def test_execute_observes_each_provider_attempt(monkeypatch) -> None:
    calls: list[str] = []
    observed: list[dict] = []
    outputs: list[dict] = []

    class _Observation:
        def update(self, *, output):
            outputs.append(output)

    @contextmanager
    def _observe(**metadata):
        observed.append(metadata)
        yield _Observation()

    monkeypatch.setattr("app.llm.runtime.observe_model_attempt", _observe)
    runtime = ModelRuntime(
        providers={"primary": {}, "fallback": {}},
        priority=["primary", "fallback"],
        config=ModelRuntimeConfig(max_retries=1, retry_interval=0),
        model_builder=lambda provider, _config, _task: _FakeModel(provider, calls),
    )

    runtime.execute("chat", lambda model: model.invoke([]))

    assert observed == [
        {
            "task_name": "chat",
            "provider": "primary",
            "attempt_index": 1,
            "fallback_enabled": True,
            "structured_required": False,
            "streaming": False,
        },
        {
            "task_name": "chat",
            "provider": "fallback",
            "attempt_index": 2,
            "fallback_enabled": True,
            "structured_required": False,
            "streaming": False,
        },
    ]
    assert outputs == [
        {
            "success": False,
            "failure_category": "ConnectionError",
            "token_started": False,
        },
        {"success": True, "token_started": False},
    ]


def test_compression_token_limit_comes_from_settings(monkeypatch) -> None:
    monkeypatch.setattr("app.llm.runtime.settings.compress.summary_max_tokens", 123)
    monkeypatch.setattr("app.llm.runtime.ChatOpenAI", lambda **kwargs: kwargs)
    runtime = ModelRuntime(
        providers={"primary": {"model_name": "model-a"}},
        priority=["primary"],
        config=ModelRuntimeConfig(retry_interval=0),
    )

    max_tokens = runtime.execute("compress", lambda model: model["max_tokens"])

    assert max_tokens == 123
