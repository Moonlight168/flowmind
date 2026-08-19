"""
FlowMind 智能流程设计服务 - 结构化生成主路径单元测试
"""

from app.adapters.factory import ModelFactory
from app.agents.react_agent import run_react_agent
from app.domain.schemas.pydantic_models import BasicDesign, FlowDesign


def _mock_manager(monkeypatch, llm):
    class _Manager:
        def __init__(self):
            self.calls = 0

        def create_llm(self, task_name=None, structured=False):
            self.calls += 1
            return llm

    manager = _Manager()
    monkeypatch.setattr(
        ModelFactory, "get_model_manager", classmethod(lambda cls: manager)
    )
    monkeypatch.setattr(
        "app.agents.react_agent.prefetch_summaries", lambda *a, **kw: {}
    )
    return manager


def test_structured_output_success(monkeypatch):
    """结构化输出成功 → model_dump"""
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

    class _LLM:
        def with_structured_output(self, schema):
            return self

        def invoke(self, messages):
            return obj

    _mock_manager(monkeypatch, _LLM())
    result = run_react_agent("flow_design", [], auth_token="", current_form_data={})
    assert result["nodes"][0]["id"] == "startEvent"
    assert len(result["nodes"]) == 3


def test_structured_output_retry_then_error(monkeypatch):
    """结构化输出失败 → 重试 3 次 → error（不降级）"""

    class _BoomLLM:
        def with_structured_output(self, schema):
            return self

        def invoke(self, messages):
            raise RuntimeError("结构化输出失败")

    manager = _mock_manager(monkeypatch, _BoomLLM())
    result = run_react_agent("flow_design", [], auth_token="", current_form_data={})
    assert result["intent"] == "error"
    assert manager.calls == 3  # 重试 3 次


def test_basic_mode_uses_basic_schema(monkeypatch):
    """basic 模式用 BasicDesign（flow_name/code），不用 FlowDesign"""
    obj = BasicDesign(flow_name="报销审批", code="expense")

    class _LLM:
        def with_structured_output(self, schema):
            assert schema is BasicDesign
            return self

        def invoke(self, messages):
            return obj

    _mock_manager(monkeypatch, _LLM())
    result = run_react_agent(
        "flow_design", [], auth_token="", current_form_data={}, mode="basic"
    )
    assert result["flow_name"] == "报销审批"
    assert result["code"] == "expense"
