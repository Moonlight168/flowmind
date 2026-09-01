"""
FlowMind 智能流程设计服务 - 结构化生成主路径单元测试

mock create_react_agent，验证 ReAct + response_format 结构化输出路径。
"""

from app.adapters.factory import ModelFactory
from app.adapters.model_manager import ModelManager
from app.agents.react_agent import run_react_agent
from app.domain.schemas.pydantic_models import BasicDesign, FlowDesign


class _FakeAgent:
    """mock create_react_agent 返回的 agent：invoke 返回 structured_response"""

    def __init__(self, response):
        self._response = response

    def invoke(self, messages, config=None):
        if isinstance(self._response, Exception):
            raise self._response
        return {"structured_response": self._response}


def _mock_manager(monkeypatch, providers=("primary",)):
    class _Manager:
        def __init__(self):
            self.calls = 0
            self.providers = providers

        def create_llm_with_provider(
            self, task_name=None, structured=False, excluded_providers=()
        ):
            self.calls += 1
            provider = next(
                (p for p in self.providers if p not in excluded_providers),
                self.providers[-1],
            )
            return object(), provider

    manager = _Manager()
    monkeypatch.setattr(
        ModelFactory, "get_model_manager", classmethod(lambda cls: manager)
    )
    return manager


def _mock_agent(monkeypatch, response, captured):
    def _create(model, tools, response_format=None):
        captured["response_format"] = response_format
        captured["tools"] = tools
        return _FakeAgent(response)

    monkeypatch.setattr("app.agents.react_agent.create_react_agent", _create)


def test_structured_output_success(monkeypatch):
    """ReAct 结构化输出成功 → model_dump"""
    obj = FlowDesign(
        nodes=[
            {
                "type": "START_EVENT",
                "id": "startEvent",
                "name": "开始",
                "form_key": "form1",
            },
            {
                "type": "USER_TASK",
                "id": "node_approve",
                "name": "审批",
                "candidate_groups": ["ROLE1"],
            },
            {"type": "END_EVENT", "id": "endEvent", "name": "结束"},
        ],
        edges=[{"source": "start", "target": "node_approve"}],
    )
    captured = {}
    _mock_manager(monkeypatch)
    _mock_agent(monkeypatch, obj, captured)
    result = run_react_agent("flow_design", [], current_form_data={})
    assert result["nodes"][0]["id"] == "startEvent"
    assert len(result["nodes"]) == 3
    assert captured["response_format"] is FlowDesign


def test_structured_output_retry_then_error(monkeypatch):
    """结构化输出失败 → 重试 3 次 → error（不降级）"""
    captured = {}
    manager = _mock_manager(monkeypatch)
    _mock_agent(monkeypatch, RuntimeError("结构化输出失败"), captured)
    result = run_react_agent("flow_design", [], current_form_data={})
    assert result["intent"] == "error"
    assert manager.calls == 3  # 重试 3 次


def test_runtime_failure_uses_fallback_provider(monkeypatch):
    """首个 provider 运行时失败后，下一次必须使用备用 provider。"""
    obj = BasicDesign(flow_name="报销审批", code="expense")
    manager = _mock_manager(monkeypatch, providers=("primary", "fallback"))
    used_providers = []

    def _create(model, tools, response_format=None):
        provider = manager.providers[manager.calls - 1]
        used_providers.append(provider)
        response = RuntimeError("primary unavailable") if provider == "primary" else obj
        return _FakeAgent(response)

    monkeypatch.setattr("app.agents.react_agent.create_react_agent", _create)
    result = run_react_agent("flow_design", [], current_form_data={}, mode="basic")

    assert result["code"] == "expense"
    assert used_providers == ["primary", "fallback"]


def test_model_manager_skips_failed_provider(monkeypatch):
    manager = ModelManager(
        providers={"primary": {"model_name": "p"}, "fallback": {"model_name": "f"}},
        priority=["primary", "fallback"],
    )
    monkeypatch.setattr(manager, "_build_llm", lambda config, task_name: object())

    _, provider = manager.create_llm_with_provider(
        structured=True, excluded_providers={"primary"}
    )

    assert provider == "fallback"


def test_basic_mode_uses_basic_schema(monkeypatch):
    """basic 模式用 BasicDesign（flow_name/code）+ 仅分类工具"""
    obj = BasicDesign(flow_name="报销审批", code="expense")
    captured = {}
    _mock_manager(monkeypatch)
    _mock_agent(monkeypatch, obj, captured)
    result = run_react_agent("flow_design", [], current_form_data={}, mode="basic")
    assert result["flow_name"] == "报销审批"
    assert result["code"] == "expense"
    assert captured["response_format"] is BasicDesign
    assert {t.name for t in captured["tools"]} == {"search_categories"}
