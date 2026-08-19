"""
FlowMind 智能流程设计服务 - 结构化生成主路径单元测试
"""

from app.adapters.factory import ModelFactory
from app.agents.react_agent import run_react_agent
from app.domain.schemas.pydantic_models import FlowDesign


def test_structured_output_success(monkeypatch):
    """结构化输出主路径：with_structured_output 返回 Pydantic 对象 → model_dump"""
    obj = FlowDesign(
        nodes=[
            {"type": "START_EVENT", "id": "startEvent", "name": "开始", "form_key": "form1"},
            {"type": "USER_TASK", "id": "node_approve", "name": "审批", "candidate_groups": ["ROLE1"]},
            {"type": "END_EVENT", "id": "endEvent", "name": "结束"},
        ],
        edges=[{"source": "start", "target": "node_approve"}],
    )

    class _StructuredLLM:
        def with_structured_output(self, schema):
            return self

        def invoke(self, messages):
            return obj

    class _Manager:
        def create_llm(self, task_name=None, structured=False):
            return _StructuredLLM()

    monkeypatch.setattr(ModelFactory, "get_model_manager", classmethod(lambda cls: _Manager()))
    # 预取返回空（避免真实 HTTP）
    monkeypatch.setattr("app.agents.react_agent.prefetch_summaries", lambda *a, **kw: {})

    result = run_react_agent("flow_design", [], auth_token="", current_form_data={})
    assert result["nodes"][0]["id"] == "startEvent"
    assert result["nodes"][0]["type"] == "START_EVENT"
    assert len(result["nodes"]) == 3


def test_structured_output_failure_falls_back_to_legacy(monkeypatch):
    """结构化输出失败（抛异常）→ 降级 legacy ReAct（create_llm 不带 structured 被调用）"""
    calls = []

    class _BoomLLM:
        def with_structured_output(self, schema):
            return self

        def invoke(self, messages):
            raise RuntimeError("结构化输出失败")

    class _LegacyLLM:
        def bind_tools(self, tools, strict=True):
            raise RuntimeError("legacy 触发（测试终点）")

    class _Manager:
        def create_llm(self, task_name=None, structured=False):
            calls.append(structured)
            return _BoomLLM() if structured else _LegacyLLM()

    monkeypatch.setattr(ModelFactory, "get_model_manager", classmethod(lambda cls: _Manager()))
    monkeypatch.setattr("app.agents.react_agent.prefetch_summaries", lambda *a, **kw: {})

    # legacy 会抛异常（_LegacyLLM.bind_tools），证明降级路径被触发
    import pytest
    with pytest.raises(RuntimeError):
        run_react_agent("flow_design", [], auth_token="", current_form_data={})

    assert calls == [True, False]  # 先 structured=True，失败后 structured=False（legacy）
