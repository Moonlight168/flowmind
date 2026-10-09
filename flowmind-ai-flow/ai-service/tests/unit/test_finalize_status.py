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
        lambda structure, category, process_key="": "<xml/>",
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


def test_form_success_message_falls_back_when_name_is_blank():
    """form_name 为空串时 dict.get 的默认值不生效，曾渲染成【】。"""
    state = {
        "design_type": "form_design",
        "intent": "success",
        "design_output": {
            "widgetList": [{"type": "input"}],
            "form_name": "",
            "operations": [{"op": "add_widget", "widget": {}}],
            "operation_count": 1,
            "review": {"passed": True, "errors": []},
        },
    }

    message = finalize_node(state)["design_output"]["message"]

    assert "【未命名】" in message
    assert "【】" not in message


def test_form_success_message_uses_generated_name():
    state = {
        "design_type": "form_design",
        "intent": "success",
        "design_output": {
            "widgetList": [{"type": "input"}],
            "form_name": "请假申请单",
            "operations": [{"op": "add_widget", "widget": {}}],
            "operation_count": 1,
            "review": {"passed": True, "errors": []},
        },
    }

    message = finalize_node(state)["design_output"]["message"]

    assert "【请假申请单】" in message
