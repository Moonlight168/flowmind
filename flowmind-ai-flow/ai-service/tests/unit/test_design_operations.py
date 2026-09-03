"""FlowMind AI 增量设计操作测试。"""

import json

import pytest
from langchain_core.messages import HumanMessage

import app.graph.nodes.generate as generate_module
from app.design.intent import Intent
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


def test_add_node_preserves_replaced_edge_id_on_the_continuation() -> None:
    baseline = {
        "nodes": [{"id": "a"}, {"id": "b"}],
        "edges": [
            {"id": "Flow_2", "source": "a", "target": "b", "name": "原连线"},
            {"id": "Flow_5", "source": "x", "target": "y"},
        ],
    }

    result = apply_design_operations(
        "flow_design",
        baseline,
        [{"op": "add_node", "after_id": "a", "node": {"id": "new"}}],
    )

    assert {edge.get("id") for edge in result["edges"]} == {
        None,
        "Flow_2",
        "Flow_5",
    }
    assert any(
        edge.get("id") == "Flow_2" and edge["source"] == "new" and edge["target"] == "b"
        for edge in result["edges"]
    )


def test_nested_form_widget_can_be_updated_and_removed() -> None:
    baseline = {
        "widgetList": [
            {
                "type": "card",
                "formItemFlag": False,
                "options": {"name": "employee_card", "label": "员工信息"},
                "widgetList": [
                    {
                        "type": "input",
                        "formItemFlag": True,
                        "options": {"name": "employee_name", "label": "姓名"},
                    },
                    {
                        "type": "input",
                        "formItemFlag": True,
                        "options": {"name": "employee_phone", "label": "电话"},
                    },
                ],
            }
        ]
    }

    result = apply_design_operations(
        "form_design",
        baseline,
        [
            {
                "op": "update_widget",
                "widget_name": "employee_name",
                "changes": {"options": {"label": "员工姓名"}},
            },
            {"op": "remove_widget", "widget_name": "employee_phone"},
        ],
    )

    children = result["widgetList"][0]["widgetList"]
    assert [item["options"]["name"] for item in children] == ["employee_name"]
    assert children[0]["options"]["label"] == "员工姓名"


def test_invalid_operation_target_is_repaired_once(monkeypatch) -> None:
    responses = iter(
        [
            {
                "operations": [
                    {
                        "op": "update_node",
                        "node_id": "missing",
                        "changes": {"name": "新名称"},
                    }
                ]
            },
            {
                "operations": [
                    {
                        "op": "update_node",
                        "node_id": "task",
                        "changes": {"name": "新名称"},
                    }
                ]
            },
        ]
    )
    calls = []

    def run_agent(**kwargs):
        calls.append(kwargs["messages"])
        return next(responses)

    monkeypatch.setattr(generate_module, "run_react_agent", run_agent)
    monkeypatch.setattr(
        generate_module,
        "discriminate_intent",
        lambda *args, **kwargs: Intent(kind="design"),
    )
    state = {
        "messages": [HumanMessage(content="修改审批节点名称")],
        "design_type": "flow_design",
        "mode": "design",
        "current_form_data": {
            "nodes": [{"id": "task", "type": "USER_TASK", "name": "审批"}],
            "edges": [],
        },
        "allow_full_replace": False,
        "review_retry_count": 0,
    }

    result = generate_module.generate_node(state)

    assert len(calls) == 2
    assert result["intent"] == "success"
    assert result["design_output"]["nodes"][0]["name"] == "新名称"
