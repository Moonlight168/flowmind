"""
FlowMind 智能流程设计服务 - 校验器单元测试
"""

from app.design.validators import (
    CategoryValidator,
    EdgeValidator,
    FormFieldValidator,
    NodeValidator,
    ValidationError,
    ValidatorContext,
    ValidatorPipeline,
)


def _ctx(
    design_type: str = "flow_design", mode: str = "design", **kw
) -> ValidatorContext:
    return ValidatorContext(design_type=design_type, mode=mode, **kw)


def _nodes(*types: str) -> list[dict]:
    return [{"id": f"n{i}", "name": f"节点{i}", "type": t} for i, t in enumerate(types)]


# ---------- NodeValidator ----------


def test_node_empty():
    result = NodeValidator().validate({"nodes": []}, _ctx())
    assert not result.is_valid
    assert any(e.rule_id == "NODE_N001" for e in result.errors)


def test_node_duplicate_id():
    nodes = [
        {"id": "n0", "name": "a", "type": "START_EVENT"},
        {"id": "n0", "name": "b", "type": "END_EVENT"},
    ]
    result = NodeValidator().validate({"nodes": nodes}, _ctx())
    assert any(e.rule_id == "NODE_N003" for e in result.errors)


def test_node_unknown_type():
    nodes = [{"id": "n0", "name": "a", "type": "ROBOT_TASK"}]
    result = NodeValidator().validate({"nodes": nodes}, _ctx())
    assert any(e.rule_id == "NODE_N007" for e in result.errors)


def test_node_gateway_needs_two_outgoing():
    nodes = [
        {"id": "g", "name": "网关", "type": "EXCLUSIVE_GATEWAY"},
        {"id": "u", "name": "审批", "type": "USER_TASK", "form_key": "f1"},
    ]
    edges = [{"source": "g", "target": "u"}]
    result = NodeValidator().validate({"nodes": nodes, "edges": edges}, _ctx())
    assert any(e.rule_id == "NODE_N006" for e in result.errors)


def test_node_merge_gateway_accepts_one_outgoing():
    nodes = [
        {"id": "a", "name": "分支A", "type": "USER_TASK", "form_key": "f1"},
        {"id": "b", "name": "分支B", "type": "USER_TASK", "form_key": "f1"},
        {"id": "g", "name": "汇聚", "type": "PARALLEL_GATEWAY"},
        {"id": "e", "name": "结束", "type": "END_EVENT"},
    ]
    edges = [
        {"source": "a", "target": "g"},
        {"source": "b", "target": "g"},
        {"source": "g", "target": "e"},
    ]
    result = NodeValidator().validate({"nodes": nodes, "edges": edges}, _ctx())
    assert not any(e.rule_id == "NODE_N006" for e in result.errors)


def test_node_start_missing_form_key():
    nodes = [{"id": "s", "name": "开始", "type": "START_EVENT"}]
    result = NodeValidator().validate({"nodes": nodes}, _ctx())
    assert any(e.rule_id == "NODE_N005" for e in result.errors)


def test_node_form_key_is_rejected_when_authoritative_form_list_is_empty():
    nodes = [{"id": "s", "name": "开始", "type": "START_EVENT", "form_key": "1"}]
    result = NodeValidator().validate(
        {"nodes": nodes}, _ctx(forms_lookup_complete=True, available_forms=[])
    )
    assert any(e.rule_id == "NODE_N005" for e in result.errors)


def test_node_numeric_form_id_matches_string_form_key():
    nodes = [{"id": "s", "name": "开始", "type": "START_EVENT", "form_key": "key_12"}]
    result = NodeValidator().validate(
        {"nodes": nodes},
        _ctx(forms_lookup_complete=True, available_forms=[{"formId": 12}]),
    )
    assert not any(e.rule_id == "NODE_N005" for e in result.errors)


def test_user_task_explicit_form_reference_must_exist():
    nodes = [
        {"id": "s", "name": "开始", "type": "START_EVENT", "form_key": "1"},
        {"id": "u", "name": "审批", "type": "USER_TASK", "form_key": "missing"},
    ]
    result = NodeValidator().validate(
        {"nodes": nodes},
        _ctx(forms_lookup_complete=True, available_forms=[{"formId": 1}]),
    )
    assert any(e.rule_id == "NODE_N005" and e.element_id == "u" for e in result.errors)


# ---------- EdgeValidator ----------


def test_edge_bad_ref():
    nodes = _nodes("START_EVENT", "END_EVENT")
    edges = [{"source": "start", "target": "ghost"}]
    result = EdgeValidator().validate({"nodes": nodes, "edges": edges}, _ctx())
    assert any(e.rule_id == "EDGE_E001" for e in result.errors)


def test_edge_self_loop():
    nodes = _nodes("START_EVENT", "USER_TASK", "END_EVENT")
    nodes[1]["form_key"] = "f1"
    edges = [{"source": "n1", "target": "n1"}]
    result = EdgeValidator().validate({"nodes": nodes, "edges": edges}, _ctx())
    assert any(e.rule_id == "EDGE_E005" for e in result.errors)


def test_edge_exclusive_gateway_condition_required():
    nodes = [
        {"id": "g", "name": "网关", "type": "EXCLUSIVE_GATEWAY"},
        {"id": "u", "name": "审批", "type": "USER_TASK", "form_key": "f1"},
        {"id": "e", "name": "结束", "type": "END_EVENT"},
    ]
    edges = [{"source": "g", "target": "u"}, {"source": "g", "target": "e"}]
    result = EdgeValidator().validate({"nodes": nodes, "edges": edges}, _ctx())
    assert any(e.rule_id == "EDGE_E002" for e in result.errors)


def test_edge_exclusive_gateway_allows_one_default_branch():
    nodes = [
        {"id": "g", "name": "网关", "type": "EXCLUSIVE_GATEWAY"},
        {"id": "u", "name": "审批", "type": "USER_TASK", "form_key": "f1"},
        {"id": "e", "name": "结束", "type": "END_EVENT"},
    ]
    edges = [
        {"source": "g", "target": "u", "condition": "${amount > 100}"},
        {"source": "g", "target": "e", "is_default": True},
    ]
    result = EdgeValidator().validate({"nodes": nodes, "edges": edges}, _ctx())
    assert not any(e.rule_id == "EDGE_E002" for e in result.errors)


def test_edge_end_event_accepts_multiple_incoming():
    nodes = [
        {"id": "a", "name": "分支A", "type": "USER_TASK", "form_key": "f1"},
        {"id": "b", "name": "分支B", "type": "USER_TASK", "form_key": "f1"},
        {"id": "e", "name": "结束", "type": "END_EVENT"},
    ]
    edges = [{"source": "a", "target": "e"}, {"source": "b", "target": "e"}]
    result = EdgeValidator().validate({"nodes": nodes, "edges": edges}, _ctx())
    assert not any(e.rule_id == "EDGE_E007" for e in result.errors)


def test_edge_condition_field_must_exist_in_available_form():
    nodes = [
        {"id": "g", "name": "判断", "type": "EXCLUSIVE_GATEWAY"},
        {"id": "a", "name": "审批", "type": "USER_TASK", "form_key": "1"},
        {"id": "e", "name": "结束", "type": "END_EVENT"},
    ]
    edges = [
        {
            "source": "g",
            "target": "a",
            "condition": {"field": "missing", "operator": "gt", "value": 1},
        },
        {"source": "g", "target": "e", "is_default": True},
    ]
    context = _ctx(
        forms_lookup_complete=True,
        available_forms=[
            {"formId": 1, "content": '{"widgetList":[{"options":{"name":"amount"}}]}'}
        ],
    )
    result = EdgeValidator().validate({"nodes": nodes, "edges": edges}, context)
    assert any(e.rule_id == "EDGE_E009" for e in result.errors)


# ---------- FormFieldValidator ----------


def test_form_bad_name():
    widgets = [
        {
            "type": "input",
            "formItemFlag": True,
            "options": {"name": "1bad", "label": "字段"},
        }
    ]
    result = FormFieldValidator().validate({"widgetList": widgets}, _ctx("form_design"))
    assert any(e.rule_id == "FORM_FF003" for e in result.errors)


def test_form_required_disabled_conflict():
    widgets = [
        {
            "type": "input",
            "formItemFlag": True,
            "options": {
                "name": "field1",
                "label": "字段",
                "required": True,
                "disabled": True,
            },
        }
    ]
    result = FormFieldValidator().validate({"widgetList": widgets}, _ctx("form_design"))
    assert any(e.rule_id == "FORM_FF005" for e in result.errors)


def test_form_nested_field_is_validated():
    widgets = [
        {
            "type": "card",
            "formItemFlag": False,
            "options": {},
            "widgetList": [
                {
                    "type": "input",
                    "formItemFlag": True,
                    "options": {"name": "1bad", "label": "字段"},
                }
            ],
        }
    ]
    result = FormFieldValidator().validate({"widgetList": widgets}, _ctx("form_design"))
    assert any(e.rule_id == "FORM_FF003" for e in result.errors)


# ---------- CategoryValidator ----------


def test_category_bad_code():
    result = CategoryValidator().validate(
        {"category_name": "请假", "code": "1bad"}, _ctx("category_design")
    )
    assert any(e.rule_id == "CAT_C002" for e in result.errors)


def test_flow_basic_category_must_come_from_authoritative_list():
    result = CategoryValidator().validate(
        {"flow_name": "报销", "code": "invented"},
        _ctx(
            "flow_design",
            mode="basic",
            categories_lookup_complete=True,
            available_categories=[],
        ),
    )
    assert any(e.rule_id == "CAT_C003" for e in result.errors)


def test_flow_basic_may_select_the_current_category():
    result = CategoryValidator().validate(
        {"flow_name": "请假", "code": "leave"},
        _ctx(
            "flow_design",
            mode="basic",
            current_form_data={"categoryId": 7, "code": "leave"},
            categories_lookup_complete=True,
            available_categories=[{"categoryId": 7, "code": "leave"}],
        ),
    )

    assert result.is_valid


def test_category_edit_excludes_itself_and_allows_duplicate_name():
    result = CategoryValidator().validate(
        {"category_name": "通用审批", "code": "leave_v2"},
        _ctx(
            "category_design",
            current_form_data={"categoryId": 7, "code": "leave"},
            categories_lookup_complete=True,
            available_categories=[
                {"categoryId": 7, "categoryName": "通用审批", "code": "leave_v2"},
                {"categoryId": 8, "categoryName": "通用审批", "code": "expense"},
            ],
        ),
    )

    assert result.is_valid


def test_category_edit_rejects_code_owned_by_another_category():
    result = CategoryValidator().validate(
        {"category_name": "请假", "code": "expense"},
        _ctx(
            "category_design",
            current_form_data={"categoryId": 7, "code": "leave"},
            categories_lookup_complete=True,
            available_categories=[
                {"categoryId": 7, "categoryName": "请假", "code": "leave"},
                {"categoryId": 8, "categoryName": "报销", "code": "expense"},
            ],
        ),
    )

    assert any(error.rule_id == "CAT_C003" for error in result.errors)


def test_candidate_group_must_exist_in_backend_roles():
    output = {
        "nodes": [
            {
                "id": "task",
                "name": "审批",
                "type": "USER_TASK",
                "candidate_groups": ["ROLE99"],
            }
        ],
        "edges": [],
    }
    result = NodeValidator().validate(
        output,
        _ctx(
            "flow_design",
            roles_lookup_complete=True,
            available_roles=[{"roleId": 2, "roleName": "财务"}],
        ),
    )

    assert any(error.rule_id == "NODE_N009" for error in result.errors)


# ---------- ValidatorPipeline ----------


def test_pipeline_aggregates():
    pipeline = ValidatorPipeline([NodeValidator(), EdgeValidator()])
    nodes = [{"id": "s", "name": "开始", "type": "START_EVENT"}]
    result = pipeline.run({"nodes": nodes}, _ctx())
    assert not result.is_valid
    assert any(e.rule_id == "NODE_N005" for e in result.errors)


def test_pipeline_detect_loop():
    pipeline = ValidatorPipeline([])
    e1 = ValidationError("NODE_N003", "dup")
    e2 = ValidationError("NODE_N003", "dup")
    history = [frozenset({"NODE_N003"})]
    assert pipeline.detect_loop([e1, e2], history) is True
    assert pipeline.detect_loop([e1], [frozenset({"OTHER"})]) is False
    assert pipeline.detect_loop([], history) is False
