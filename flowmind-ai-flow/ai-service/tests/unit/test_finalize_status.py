"""Public AI design response status and safe-fallback tests."""

from app.graph.nodes.finalize import finalize_node


def test_validation_failure_never_returns_a_draft():
    state = {
        "design_type": "flow_design",
        "intent": "error",
        "design_output": {
            "nodes": [{"id": "unsafe", "type": "USER_TASK", "name": "草稿"}],
            "review": {"passed": False, "errors": ["缺少开始节点"]},
            "operation_count": 1,
        },
    }
    result = finalize_node(state)["design_output"]
    assert result["status"] == "error"
    assert result["form_data"] is None
    assert result["validation"]["errors"] == ["缺少开始节点"]


def test_clarification_uses_needs_input_status():
    state = {
        "design_type": "form_design",
        "intent": "clarification",
        "design_output": {"message": "请选择表单"},
    }
    result = finalize_node(state)["design_output"]
    assert result["status"] == "needs_input"
    assert result["form_data"] is None


def test_ready_response_exposes_operations_and_validation(monkeypatch):
    monkeypatch.setattr(
        "app.graph.nodes.finalize.generate_bpmn_xml",
        lambda structure, category: "<xml/>",
    )
    state = {
        "design_type": "flow_design",
        "mode": "design",
        "intent": "success",
        "current_form_data": {"modelName": "请假"},
        "design_output": {
            "nodes": [
                {"id": "start", "type": "START_EVENT", "name": "开始", "form_key": "1"}
            ],
            "edges": [],
            "operations": [{"op": "replace_graph", "nodes": [], "edges": []}],
            "operation_count": 1,
            "review": {"passed": True, "errors": []},
        },
    }
    result = finalize_node(state)["design_output"]
    assert result["status"] == "ready"
    assert result["operation_count"] == 1
    assert result["operations"][0]["op"] == "replace_graph"
