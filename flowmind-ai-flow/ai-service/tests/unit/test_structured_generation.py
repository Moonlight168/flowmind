"""
FlowMind 智能流程设计服务 - 结构化生成主路径单元测试

mock create_react_agent，验证 ReAct + response_format 结构化输出路径。
"""

import app.design.generation as react_agent_module
from app.design.generation import run_react_agent
from app.domain.design_models import BasicDesign, FlowDesign


class _FakeAgent:
    """mock create_react_agent 返回的 agent：invoke 返回 structured_response"""

    def __init__(self, response):
        self._response = response

    def invoke(self, messages, config=None):
        if isinstance(self._response, Exception):
            raise self._response
        return {"structured_response": self._response}


def _mock_runtime(monkeypatch):
    class _Runtime:
        def __init__(self):
            self.calls = 0

        def execute(self, task_name, operation, structured=False):
            self.calls += 1
            return operation(object())

    runtime = _Runtime()
    monkeypatch.setattr(react_agent_module, "get_model_runtime", lambda: runtime)
    return runtime


def _mock_agent(monkeypatch, response, captured):
    def _create(model, tools, response_format=None):
        captured["response_format"] = response_format
        captured["tools"] = tools
        return _FakeAgent(response)

    monkeypatch.setattr("app.design.generation.create_react_agent", _create)


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
    _mock_runtime(monkeypatch)
    _mock_agent(monkeypatch, obj, captured)
    result = run_react_agent("flow_design", [], current_form_data={})
    assert result["nodes"][0]["id"] == "startEvent"
    assert len(result["nodes"]) == 3
    assert captured["response_format"] is FlowDesign


def test_structured_output_retry_then_error(monkeypatch):
    """结构化输出失败 → 重试 3 次 → error（不降级）"""
    captured = {}
    runtime = _mock_runtime(monkeypatch)
    _mock_agent(monkeypatch, ValueError("结构化输出失败"), captured)
    result = run_react_agent("flow_design", [], current_form_data={})
    assert result["intent"] == "error"
    assert runtime.calls == 3  # 结构化内容重试 3 次


def test_basic_mode_uses_basic_schema(monkeypatch):
    """basic 模式用 BasicDesign（flow_name/code）+ 仅分类工具"""
    obj = BasicDesign(flow_name="报销审批", code="expense")
    captured = {}
    _mock_runtime(monkeypatch)
    _mock_agent(monkeypatch, obj, captured)
    result = run_react_agent("flow_design", [], current_form_data={}, mode="basic")
    assert result["flow_name"] == "报销审批"
    assert result["code"] == "expense"
    assert captured["response_format"] is BasicDesign
    assert {t.name for t in captured["tools"]} == {"search_categories"}
