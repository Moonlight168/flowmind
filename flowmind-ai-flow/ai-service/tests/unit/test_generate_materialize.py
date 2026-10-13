"""Tests for materializing structured design operations."""

import pytest

from app.graph.nodes.generate import _materialize_result


def _replace_graph_result() -> dict:
    return {
        "operations": [
            {
                "op": "replace_graph",
                "nodes": [
                    {"id": "startEvent", "name": "开始", "type": "START_EVENT"},
                    {"id": "endEvent", "name": "结束", "type": "END_EVENT"},
                ],
                "edges": [],
            }
        ]
    }


def test_complete_form_draft_is_exposed_without_inserting_temporary_key():
    result = _replace_graph_result()
    result["new_forms"] = [
        {
            "form_name": "申请信息表",
            "node_ids": ["startEvent"],
            "widgetList": [
                {
                    "type": "input",
                    "formItemFlag": True,
                    "options": {"name": "reason", "label": "申请原因", "required": True},
                }
            ],
            "formConfig": {},
        }
    ]

    payload = _materialize_result(result, "flow_design", {}, "design")

    assert payload["new_forms"] == result["new_forms"]
    assert "form_key" not in payload["nodes"][0]


def test_flow_without_form_draft_leaves_form_key_untouched():
    payload = _materialize_result(_replace_graph_result(), "flow_design", {}, "design")

    assert "new_forms" not in payload
    assert "form_key" not in payload["nodes"][0]


def test_generated_form_draft_rejects_unknown_target_node():
    result = _replace_graph_result()
    result["new_forms"] = [
        {
            "form_name": "申请信息表",
            "node_ids": ["missing"],
            "widgetList": [
                {
                    "type": "input",
                    "formItemFlag": True,
                    "options": {"name": "reason", "label": "申请原因"},
                }
            ],
            "formConfig": {},
        }
    ]

    with pytest.raises(ValueError, match="missing"):
        _materialize_result(result, "flow_design", {}, "design")


def test_form_name_from_model_is_kept_when_baseline_has_none():
    result = {
        "operations": [{"op": "replace_form", "widgetList": [], "formConfig": {}}],
        "form_name": "请假申请单",
    }

    payload = _materialize_result(result, "form_design", {}, "design")

    assert payload["form_name"] == "请假申请单"


def test_model_form_name_does_not_override_existing_name():
    result = {
        "operations": [{"op": "replace_form", "widgetList": [], "formConfig": {}}],
        "form_name": "模型建议名称",
    }

    payload = _materialize_result(
        result, "form_design", {"form_name": "已有表单"}, "design"
    )

    assert payload["form_name"] == "已有表单"


def test_full_replace_applies_to_existing_form():
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
    baseline = {
        "nodes": [{"id": "start", "type": "START_EVENT", "name": "开始"}],
        "edges": [],
    }
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
