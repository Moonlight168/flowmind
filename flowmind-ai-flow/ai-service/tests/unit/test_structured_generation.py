"""Structured generation main-path tests."""

import app.design.generation as generation_module
from app.design.generation import run_react_agent
from app.domain.design_models import BasicDesign, FlowDesign


class _FakeAgent:
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
    monkeypatch.setattr(generation_module, "get_model_runtime", lambda: runtime)
    return runtime


def _mock_agent(monkeypatch, response, captured):
    def _create(model, tools, response_format=None):
        captured["response_format"] = response_format
        captured["tools"] = tools
        return _FakeAgent(response)

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
    _mock_runtime(monkeypatch)
    _mock_agent(monkeypatch, obj, captured)

    result = run_react_agent("flow_design", [], current_form_data={})

    assert result["operations"][0]["nodes"][0]["id"] == "startEvent"
    assert captured["response_format"] is FlowDesign


def test_structured_output_retry_then_error(monkeypatch):
    captured = {}
    runtime = _mock_runtime(monkeypatch)
    _mock_agent(monkeypatch, ValueError("invalid structured output"), captured)

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
    _mock_runtime(monkeypatch)
    _mock_agent(monkeypatch, obj, captured)

    result = run_react_agent("flow_design", [], current_form_data={}, mode="basic")

    assert result["operations"][0]["changes"]["code"] == "expense"
    assert captured["response_format"] is BasicDesign
    assert {tool.name for tool in captured["tools"]} == {"search_categories"}
