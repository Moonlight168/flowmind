"""
FlowMind 智能流程设计服务 - 设计结果落地（_materialize_result）测试

覆盖：待创建开始表单的占位 key、模型建议的表单名、整体替换的放行。
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
        _replace_graph_result(start_form_name="请假申请单"), "flow_design", {}, "design"
    )

    assert payload["start_form_name"] == "请假申请单"
    start = next(n for n in payload["nodes"] if n["type"] == "START_EVENT")
    assert start["form_key"] == PENDING_FORM_KEY


def test_start_form_name_is_trimmed():
    payload = _materialize_result(
        _replace_graph_result(start_form_name="  请假申请单  "), "flow_design", {}, "design"
    )

    assert payload["start_form_name"] == "请假申请单"


def test_without_start_form_name_form_key_is_untouched():
    payload = _materialize_result(_replace_graph_result(), "flow_design", {}, "design")

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

    payload = _materialize_result(result, "flow_design", {}, "basic")

    assert payload.get("nodes") is None


# ---------- 新建表单的表单名 ----------


def test_form_name_from_model_is_kept_when_baseline_has_none():
    result = {
        "operations": [
            {"op": "replace_form", "widgetList": [], "formConfig": {}}
        ],
        "form_name": "请假申请单",
    }

    payload = _materialize_result(result, "form_design", {}, "design")

    assert payload["form_name"] == "请假申请单"


def test_model_form_name_does_not_override_existing_name():
    result = {
        "operations": [{"op": "replace_form", "widgetList": [], "formConfig": {}}],
        "form_name": "模型编的名字",
    }

    payload = _materialize_result(
        result, "form_design", {"form_name": "已有表单"}, "design"
    )

    assert payload["form_name"] == "已有表单"


# ---------- 整体替换不再被拦截 ----------


def test_full_replace_applies_to_existing_form():
    """已有表单也允许整体替换：安全性由变更预览与版本回退保证，不再硬拦截。"""
    baseline = {"widgetList": [{"options": {"name": "reason"}}], "formConfig": {}}
    result = {
        "operations": [
            {"op": "replace_form", "widgetList": [], "formConfig": {"labelWidth": 100}}
        ]
    }

    payload = _materialize_result(result, "form_design", baseline, "design")

    assert payload["widgetList"] == []
    assert payload["formConfig"]["labelWidth"] == 100


def test_full_replace_applies_to_existing_flow():
    baseline = {"nodes": [{"id": "start", "type": "START_EVENT", "name": "开始"}], "edges": []}
    result = {
        "operations": [
            {
                "op": "replace_graph",
                "nodes": [{"id": "only", "type": "END_EVENT", "name": "结束"}],
                "edges": [],
            }
        ]
    }

    payload = _materialize_result(result, "flow_design", baseline, "design")

    assert [node["id"] for node in payload["nodes"]] == ["only"]
