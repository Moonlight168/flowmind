"""
FlowMind 智能流程设计服务 - 工作流 Langfuse 接入测试
"""

from contextlib import contextmanager
from importlib import import_module
from types import SimpleNamespace

chat_module = import_module("app.graph.workflows.chat_workflow")
design_module = import_module("app.graph.workflows.design_workflow")


class _Observation:
    def __init__(self):
        self.output = None

    def update(self, *, output):
        self.output = output


@contextmanager
def _empty_scope(*args, **kwargs):
    yield


def _observed_scope(captured, observation):
    @contextmanager
    def _scope(name, **kwargs):
        captured["observation_name"] = name
        captured["observation_kwargs"] = kwargs
        yield observation

    return _scope


def _traced_config(captured):
    def _config(config):
        captured["base_config"] = config
        return {**config, "callbacks": ["langfuse"]}

    return _config


def test_chat_entry_attaches_callback_and_records_output(monkeypatch):
    """聊天入口应注入顶层回调并把最终回复写入根观测。"""
    captured = {}
    observation = _Observation()

    class _Graph:
        def invoke(self, state, config):
            captured["graph_config"] = config
            return {"chat_response": "ok"}

    monkeypatch.setattr(chat_module, "thread_exists", lambda thread_id: True)
    monkeypatch.setattr(chat_module, "log_context", _empty_scope)
    monkeypatch.setattr(
        chat_module, "observe_workflow", _observed_scope(captured, observation)
    )
    monkeypatch.setattr(chat_module, "langchain_config", _traced_config(captured))
    monkeypatch.setattr(chat_module, "chat_workflow", _Graph())

    result = chat_module.invoke_chat_workflow("hello", "thread-1", "trace-1")

    assert result["chat_response"] == "ok"
    assert captured["observation_name"] == "flowmind.chat"
    assert captured["graph_config"]["callbacks"] == ["langfuse"]
    assert observation.output == {"chat_response": "ok"}


def test_design_entry_attaches_callback_and_records_output(monkeypatch):
    """同步设计入口应注入顶层回调并记录最终设计结果。"""
    captured = {}
    observation = _Observation()
    expected_output = {"form_data": {"name": "leave"}}

    class _Graph:
        def invoke(self, state, config):
            captured["graph_config"] = config
            return {"intent": "success", "design_output": expected_output}

    monkeypatch.setattr(
        design_module,
        "_prepare_design_call",
        lambda *args: ({"configurable": {"thread_id": "thread-1"}}, "trace-1", {}),
    )
    monkeypatch.setattr(design_module.request_cache, "scope", _empty_scope)
    monkeypatch.setattr(design_module, "_thread_lock", _empty_scope)
    monkeypatch.setattr(design_module, "log_context", _empty_scope)
    monkeypatch.setattr(
        design_module, "observe_workflow", _observed_scope(captured, observation)
    )
    monkeypatch.setattr(design_module, "langchain_config", _traced_config(captured))
    monkeypatch.setattr(design_module, "design_workflow", _Graph())

    result = design_module.invoke_design_workflow(
        "flow_design", "设计请假流程", "thread-1", "trace-1"
    )

    assert result == expected_output
    assert captured["observation_name"] == "flowmind.design"
    assert captured["graph_config"]["callbacks"] == ["langfuse"]
    assert observation.output == expected_output


def test_stream_design_entry_keeps_observation_until_final_output(monkeypatch):
    """SSE 设计入口的观测应覆盖完整迭代并记录最终状态。"""
    captured = {}
    observation = _Observation()
    expected_output = {"form_data": {"name": "leave"}}

    class _Graph:
        def stream(self, state, config, stream_mode):
            captured["graph_config"] = config
            yield {"design": {}}
            yield {"format": {}}

        def get_state(self, config):
            return SimpleNamespace(values={"design_output": expected_output})

    monkeypatch.setattr(
        design_module,
        "_prepare_design_call",
        lambda *args: ({"configurable": {"thread_id": "thread-1"}}, "trace-1", {}),
    )
    monkeypatch.setattr(design_module.request_cache, "scope", _empty_scope)
    monkeypatch.setattr(design_module, "_thread_lock", _empty_scope)
    monkeypatch.setattr(design_module, "log_context", _empty_scope)
    monkeypatch.setattr(
        design_module, "observe_workflow", _observed_scope(captured, observation)
    )
    monkeypatch.setattr(design_module, "langchain_config", _traced_config(captured))
    monkeypatch.setattr(design_module, "design_workflow", _Graph())

    events = list(
        design_module.stream_design_workflow(
            "flow_design", "设计请假流程", "thread-1", "trace-1"
        )
    )

    assert events[-1] == {"type": "done", **expected_output}
    assert captured["observation_name"] == "flowmind.design"
    assert captured["graph_config"]["callbacks"] == ["langfuse"]
    assert observation.output == expected_output
