"""
FlowMind 智能流程设计服务 - 待创建开始表单的占位 key 测试

系统没有表单时，模型给出 start_form_name；后端在开始节点写占位 key，
使生成的 bpmn_xml 带上 formKey，前端创建表单后再替换成真实 key_<formId>。
"""

from app.domain.design_models import PENDING_FORM_KEY
from app.graph.nodes.generate import _materialize_result


def _replace_graph_result(*, start_form_name: str | None = None) -> dict:
    result = {
        "operations": [
            {
                "op": "replace_graph",
                "nodes": [
                    {"id": "startEvent", "name": "开始", "type": "START_EVENT"},
                    {"id": "endEvent", "name": "结束", "type": "END_EVENT"},
                ],
                "edges": [],
            }
        ],
    }
    if start_form_name is not None:
        result["start_form_name"] = start_form_name
    return result


def test_start_form_name_sets_placeholder_key():
    payload = _materialize_result(
        {}, _replace_graph_result(start_form_name="请假申请单"), "flow_design", {}, "design"
    )

    assert payload["start_form_name"] == "请假申请单"
    start = next(n for n in payload["nodes"] if n["type"] == "START_EVENT")
    assert start["form_key"] == PENDING_FORM_KEY


def test_start_form_name_is_trimmed():
    payload = _materialize_result(
        {}, _replace_graph_result(start_form_name="  请假申请单  "), "flow_design", {}, "design"
    )

    assert payload["start_form_name"] == "请假申请单"


def test_without_start_form_name_form_key_is_untouched():
    payload = _materialize_result(
        {}, _replace_graph_result(), "flow_design", {}, "design"
    )

    assert "start_form_name" not in payload
    assert "form_key" not in payload["nodes"][0]


def test_basic_mode_does_not_touch_form_key():
    """基本信息模式不生成节点，也不该写表单占位。"""
    result = {
        "operations": [
            {
                "op": "update_flow_metadata",
                "changes": {"flow_name": "请假审批", "category_name": "人事管理"},
            }
        ],
        "start_form_name": "请假申请单",
    }

    payload = _materialize_result({}, result, "flow_design", {}, "basic")

    assert payload.get("nodes") is None


# ---------- 新建表单的表单名 ----------


def test_form_name_from_model_is_kept_when_baseline_has_none():
    result = {
        "operations": [
            {"op": "replace_form", "widgetList": [], "formConfig": {}}
        ],
        "form_name": "请假申请单",
    }

    payload = _materialize_result({}, result, "form_design", {}, "design")

    assert payload["form_name"] == "请假申请单"


def test_model_form_name_does_not_override_existing_name():
    result = {
        "operations": [{"op": "replace_form", "widgetList": [], "formConfig": {}}],
        "form_name": "模型编的名字",
    }

    payload = _materialize_result(
        {}, result, "form_design", {"form_name": "已有表单"}, "design"
    )

    assert payload["form_name"] == "已有表单"
