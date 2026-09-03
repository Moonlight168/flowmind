"""设计工作流前置处理节点测试。"""

from app.graph.nodes.prepare import prepare_design_node


def test_prepare_normalizes_form_content() -> None:
    state = {
        "design_type": "form_design",
        "mode": "design",
        "current_form_data": {
            "formName": "请假单",
            "content": '{"widgetList":[{"type":"input"}],"formConfig":{}}',
        },
    }

    result = prepare_design_node(state)

    assert result["current_form_data"]["form_name"] == "请假单"
    assert result["current_form_data"]["widgetList"] == [{"type": "input"}]


def test_prepare_rejects_basic_mode_outside_flow_design() -> None:
    result = prepare_design_node(
        {"design_type": "form_design", "mode": "basic", "current_form_data": {}}
    )

    assert result["intent"] == "error"
    assert result["design_output"]["error_type"] == "internal"
