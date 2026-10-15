"""Structured generation main-path tests."""

from langchain_core.messages import AIMessage, ToolMessage

import app.design.generation as generation_module
from app.design.generation import run_react_agent
from app.domain.design_models import BasicDesign, CategoryDesign, FlowDesign


class _FakeAgent:
    def __init__(self, messages=None):
        self._messages = messages or [AIMessage(content="retrieval complete")]

    def invoke(self, messages, config=None):
        return {"messages": self._messages}


class _FakeStructuredModel:
    def __init__(self, response, captured):
        self._response = response
        self._captured = captured

    def invoke(self, messages, config=None):
        self._captured["structured_messages"] = messages
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


class _FakeModel:
    def __init__(self, response, captured):
        self._response = response
        self._captured = captured

    def with_structured_output(self, schema):
        self._captured["structured_schema"] = schema
        return _FakeStructuredModel(self._response, self._captured)


def _mock_runtime(monkeypatch, response, captured):
    class _Runtime:
        def __init__(self):
            self.calls = 0

        def execute(self, task_name, operation, structured=False):
            self.calls += 1
            return operation(_FakeModel(response, captured))

    runtime = _Runtime()
    monkeypatch.setattr(generation_module, "get_model_runtime", lambda: runtime)
    return runtime


def _mock_agent(monkeypatch, captured, messages=None):
    def _create(model, tools, response_format=None):
        captured["response_format"] = response_format
        captured["tools"] = tools
        return _FakeAgent(messages)

    monkeypatch.setattr("app.design.generation.create_react_agent", _create)


def test_structured_output_success(monkeypatch):
    obj = FlowDesign(
        operations=[
            {
                "op": "replace_graph",
                "nodes": [
                    {"type": "START_EVENT", "id": "startEvent", "name": "start"},
                    {"type": "END_EVENT", "id": "endEvent", "name": "end"},
                ],
                "edges": [{"source": "start", "target": "end"}],
            }
        ]
    )
    captured = {}
    _mock_runtime(monkeypatch, obj, captured)
    _mock_agent(monkeypatch, captured)

    result = run_react_agent("flow_design", [], current_form_data={})

    assert result["operations"][0]["nodes"][0]["id"] == "startEvent"
    assert captured["response_format"] is None
    assert captured["structured_schema"] is FlowDesign


def test_structured_output_retry_then_error(monkeypatch):
    captured = {}
    runtime = _mock_runtime(
        monkeypatch, ValueError("invalid structured output"), captured
    )
    _mock_agent(monkeypatch, captured)

    result = run_react_agent("flow_design", [], current_form_data={})

    assert result["intent"] == "error"
    assert runtime.calls == 3


def test_basic_mode_uses_basic_schema(monkeypatch):
    obj = BasicDesign(
        operations=[
            {
                "op": "update_flow_metadata",
                "changes": {"flow_name": "expense approval", "code": "expense"},
            }
        ]
    )
    captured = {}
    _mock_runtime(monkeypatch, obj, captured)
    _mock_agent(monkeypatch, captured)

    result = run_react_agent("flow_design", [], current_form_data={}, mode="basic")

    assert result["operations"][0]["changes"]["code"] == "expense"
    assert captured["response_format"] is None
    assert captured["structured_schema"] is BasicDesign
    assert {tool.name for tool in captured["tools"]} == {"search_categories"}


def test_optional_metadata_fields_are_not_expanded_to_none(monkeypatch):
    obj = BasicDesign(
        operations=[
            {"op": "update_flow_metadata", "changes": {"description": "新描述"}}
        ]
    )
    captured = {}
    _mock_runtime(monkeypatch, obj, captured)
    _mock_agent(monkeypatch, captured)

    result = run_react_agent("flow_design", [], current_form_data={}, mode="basic")

    assert result["operations"][0]["changes"] == {"description": "新描述"}


def test_optional_category_fields_are_not_expanded_to_none(monkeypatch):
    obj = CategoryDesign(
        operations=[{"op": "update_category", "changes": {"remark": "新备注"}}]
    )
    captured = {}
    _mock_runtime(monkeypatch, obj, captured)
    _mock_agent(monkeypatch, captured)

    result = run_react_agent("category_design", [], current_form_data={})

    assert result["operations"][0]["changes"] == {"remark": "新备注"}


def test_structured_handoff_does_not_replay_tool_call_metadata(monkeypatch):
    obj = CategoryDesign(
        operations=[
            {
                "op": "update_category",
                "changes": {"category_name": "请假分类", "code": "LEAVE"},
            }
        ]
    )
    captured = {}
    _mock_runtime(monkeypatch, obj, captured)
    _mock_agent(
        monkeypatch,
        captured,
        messages=[
            AIMessage(
                content="查询分类",
                tool_calls=[
                    {
                        "name": "search_categories",
                        "args": {},
                        "id": "call-1",
                        "type": "tool_call",
                    }
                ],
            ),
            ToolMessage(
                content='[{"code":"OTHER"}]',
                name="search_categories",
                tool_call_id="call-1",
            ),
            AIMessage(content="LEAVE 不冲突，可以生成"),
        ],
    )

    result = run_react_agent("category_design", [], current_form_data={})

    assert result["operations"][0]["changes"]["code"] == "LEAVE"
    handoff = captured["structured_messages"][-1]
    assert isinstance(handoff, dict)
    assert "OTHER" in handoff["content"]
    assert "LEAVE 不冲突" in handoff["content"]
    assert not any(
        isinstance(message, ToolMessage) for message in captured["structured_messages"]
    )
