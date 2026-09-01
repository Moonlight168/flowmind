"""
FlowMind 智能流程设计服务 - Langfuse 可观测性单元测试
"""

from contextlib import contextmanager

import pytest
from langchain_core.callbacks import CallbackManager

from app.infra import observability


def test_observability_disabled_without_credentials(monkeypatch):
    """缺少密钥时不创建客户端，也不改变 Runnable 配置。"""
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.setattr(
        observability,
        "get_client",
        lambda: (_ for _ in ()).throw(AssertionError("不应初始化客户端")),
    )

    original = {"configurable": {"thread_id": "thread-1"}}
    with observability.observe_workflow(
        "test",
        input={"message": "hello"},
        session_id="thread-1",
        trace_id="trace-1",
    ) as observation:
        assert observation is None
        assert observability.langchain_config(original) == original


def test_observe_workflow_propagates_context_and_callback(monkeypatch):
    """根观测应传播用户、会话和业务 trace，并注册 LangChain 回调。"""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    captured = {}
    observation = object()
    handler = object()

    class _Client:
        @contextmanager
        def start_as_current_observation(self, **kwargs):
            captured["observation"] = kwargs
            yield observation

    @contextmanager
    def _propagate_attributes(**kwargs):
        captured["attributes"] = kwargs
        yield

    class _User:
        user_id = 42

    monkeypatch.setattr(observability, "get_client", lambda: _Client())
    monkeypatch.setattr(observability, "propagate_attributes", _propagate_attributes)
    monkeypatch.setattr(observability, "CallbackHandler", lambda: handler)
    monkeypatch.setattr(observability, "get_current_user", lambda: _User())

    with observability.observe_workflow(
        "flowmind.design",
        input={"message": "hello"},
        session_id="thread-1",
        trace_id="trace-1",
        metadata={"mode": "design"},
        tags=["design"],
    ) as current:
        config = observability.langchain_config({"callbacks": ["existing"]})
        assert current is observation
        assert config["callbacks"] == ["existing", handler]

    assert captured["attributes"] == {
        "user_id": "42",
        "session_id": "thread-1",
        "tags": ["design"],
        "metadata": {"business_trace_id": "trace-1", "mode": "design"},
        "trace_name": "flowmind.design",
    }
    assert captured["observation"]["as_type"] == "agent"


def test_disabled_flag_overrides_credentials(monkeypatch):
    """显式关闭追踪时即使存在密钥也保持禁用。"""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_TRACING_ENABLED", "false")

    assert observability.observability_enabled() is False


def test_shutdown_flushes_enabled_client(monkeypatch):
    """启用观测时，服务退出必须刷新 Langfuse 后台队列。"""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    flushed = []

    class _Client:
        def shutdown(self):
            flushed.append(True)

    monkeypatch.setattr(observability, "get_client", lambda: _Client())

    observability.shutdown_observability()

    assert flushed == [True]


def test_initialization_failure_does_not_break_business(monkeypatch):
    """Langfuse 初始化异常时应降级，业务代码仍可继续执行。"""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setattr(
        observability,
        "get_client",
        lambda: (_ for _ in ()).throw(ValueError("invalid config")),
    )

    with observability.observe_workflow(
        "test", input={}, session_id="thread-1", trace_id="trace-1"
    ) as observation:
        assert observation is None


def test_callback_manager_is_copied_before_adding_handler():
    """已有 CallbackManager 应保留且不被原地修改。"""
    handler = object()
    manager = CallbackManager([])
    token = observability._langchain_handler.set(handler)
    try:
        config = observability.langchain_config({"callbacks": manager})
    finally:
        observability._langchain_handler.reset(token)

    assert manager.handlers == []
    assert config["callbacks"].handlers == [handler]


def test_shutdown_failure_isolated(monkeypatch):
    """Langfuse 刷新异常不得阻断应用关闭。"""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

    class _Client:
        def shutdown(self):
            raise RuntimeError("flush failed")

    monkeypatch.setattr(observability, "get_client", lambda: _Client())

    observability.shutdown_observability()


def test_business_error_reaches_root_observation(monkeypatch):
    """业务异常必须传给根观测，使失败链路被正确标记。"""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    exit_types = []

    class _Context:
        def __init__(self, value=None):
            self.value = value

        def __enter__(self):
            return self.value

        def __exit__(self, exc_type, exc, traceback):
            exit_types.append(exc_type)

    class _Client:
        def start_as_current_observation(self, **kwargs):
            return _Context(object())

    monkeypatch.setattr(observability, "get_client", lambda: _Client())
    monkeypatch.setattr(
        observability, "propagate_attributes", lambda **kwargs: _Context()
    )
    monkeypatch.setattr(observability, "CallbackHandler", lambda: object())

    with (
        pytest.raises(KeyError, match="business failed"),
        observability.observe_workflow(
            "test", input={}, session_id="thread-1", trace_id="trace-1"
        ),
    ):
        raise KeyError("business failed")

    assert exit_types == [KeyError, KeyError]


def test_observation_exit_failure_does_not_mask_business_error(monkeypatch):
    """观测退出失败时，原始业务异常必须保持不变。"""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    root_exit_types = []

    class _PropagationContext:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, traceback):
            return None

    class _FailingObservationContext:
        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc, traceback):
            root_exit_types.append(exc_type)
            raise RuntimeError("langfuse close failed")

    class _Client:
        def start_as_current_observation(self, **kwargs):
            return _FailingObservationContext()

    monkeypatch.setattr(observability, "get_client", lambda: _Client())
    monkeypatch.setattr(
        observability,
        "propagate_attributes",
        lambda **kwargs: _PropagationContext(),
    )
    monkeypatch.setattr(observability, "CallbackHandler", lambda: object())

    with (
        pytest.raises(KeyError, match="business failed"),
        observability.observe_workflow(
            "test", input={}, session_id="thread-1", trace_id="trace-1"
        ),
    ):
        raise KeyError("business failed")

    assert root_exit_types == [KeyError]


def test_observation_exit_failure_does_not_break_success(monkeypatch):
    """正常业务完成后，观测退出失败也不得改变成功结果。"""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

    class _Context:
        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc, traceback):
            raise RuntimeError("langfuse close failed")

    class _Client:
        def start_as_current_observation(self, **kwargs):
            return _Context()

    monkeypatch.setattr(observability, "get_client", lambda: _Client())
    monkeypatch.setattr(
        observability, "propagate_attributes", lambda **kwargs: _Context()
    )
    monkeypatch.setattr(observability, "CallbackHandler", lambda: object())

    completed = False
    with observability.observe_workflow(
        "test", input={}, session_id="thread-1", trace_id="trace-1"
    ):
        completed = True

    assert completed is True
