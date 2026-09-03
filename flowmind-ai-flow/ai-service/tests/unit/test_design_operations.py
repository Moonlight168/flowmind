"""FlowMind AI 增量设计操作测试。"""

import json

import pytest

from app.design.operations import apply_design_operations, normalize_design_baseline
from app.graph.nodes.generate import _contains_forbidden_replace


def test_flow_update_does_not_mutate_or_drop_unmentioned_nodes() -> None:
    baseline = {
        "nodes": [
            {"id": "start", "type": "START_EVENT", "name": "开始", "form_key": "1"},
            {
                "id": "manager",
                "type": "USER_TASK",
                "name": "经理审批",
                "candidate_groups": ["ROLE1"],
            },
            {"id": "end", "type": "END_EVENT", "name": "结束"},
        ],
        "edges": [
            {"source": "start", "target": "manager"},
            {"source": "manager", "target": "end"},
        ],
    }

    result = apply_design_operations(
        "flow_design",
        baseline,
        [
            {
                "op": "update_node",
                "node_id": "manager",
                "changes": {"name": "部门经理审批"},
            }
        ],
    )

    assert baseline["nodes"][1]["name"] == "经理审批"
    assert [node["name"] for node in result["nodes"]] == [
        "开始",
        "部门经理审批",
        "结束",
    ]
    assert result["edges"] == baseline["edges"]


def test_flow_node_insert_rewires_single_outgoing_edge() -> None:
    baseline = {
        "nodes": [
            {"id": "manager", "type": "USER_TASK", "name": "经理审批"},
            {"id": "end", "type": "END_EVENT", "name": "结束"},
        ],
        "edges": [{"source": "manager", "target": "end"}],
    }

    result = apply_design_operations(
        "flow_design",
        baseline,
        [
            {
                "op": "add_node",
                "after_id": "manager",
                "node": {"id": "finance", "type": "USER_TASK", "name": "财务审批"},
            }
        ],
    )

    assert result["edges"] == [
        {"source": "manager", "target": "finance"},
        {"source": "finance", "target": "end"},
    ]


def test_form_content_is_normalized_and_add_widget_preserves_metadata() -> None:
    form_json = {
        "widgetList": [
            {
                "id": "input_old",
                "type": "input",
                "formItemFlag": True,
                "options": {"name": "reason", "label": "事由"},
            }
        ],
        "formConfig": {"modelName": "leaveForm"},
    }
    baseline = normalize_design_baseline(
        "form_design",
        {"formId": 7, "formName": "请假表", "content": json.dumps(form_json)},
    )

    result = apply_design_operations(
        "form_design",
        baseline,
        [
            {
                "op": "add_widget",
                "after_name": "reason",
                "widget": {
                    "type": "date",
                    "formItemFlag": True,
                    "options": {"name": "start_date", "label": "开始日期"},
                },
            }
        ],
    )

    assert result["formId"] == 7
    assert [item["options"]["name"] for item in result["widgetList"]] == [
        "reason",
        "start_date",
    ]
    assert result["formConfig"] == {"modelName": "leaveForm"}


def test_unknown_operation_is_rejected_without_mutating_baseline() -> None:
    baseline = {"nodes": [], "edges": []}

    with pytest.raises(ValueError, match="不支持的流程操作"):
        apply_design_operations("flow_design", baseline, [{"op": "guess"}])

    assert baseline == {"nodes": [], "edges": []}


def test_full_replace_requires_explicit_permission_for_existing_design() -> None:
    state = {"current_form_data": {"nodes": [{"id": "start"}]}}
    operations = [{"op": "replace_graph", "nodes": [], "edges": []}]

    assert _contains_forbidden_replace(state, operations)
    state["allow_full_replace"] = True
    assert not _contains_forbidden_replace(state, operations)
