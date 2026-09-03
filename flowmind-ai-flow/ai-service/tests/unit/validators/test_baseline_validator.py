"""
FlowMind 智能流程设计服务 - 基线节点保留校验器单元测试
"""

from app.design.validators import BaselineValidator, ValidatorContext


def _ctx(nodes=None, user_input=""):
    return ValidatorContext(
        design_type="flow_design",
        mode="design",
        current_form_data={"nodes": nodes or []},
        user_input=user_input,
    )


def test_no_baseline_skip():
    """无基线 → 跳过"""
    output = {"nodes": [{"id": "a", "name": "x", "type": "USER_TASK"}]}
    result = BaselineValidator().validate(output, _ctx(nodes=None))
    assert result.is_valid


def test_all_baseline_kept():
    """基线节点全保留 → 通过"""
    baseline = [{"id": "a", "name": "x", "type": "USER_TASK"}]
    output = {"nodes": [{"id": "a", "name": "x", "type": "USER_TASK"}]}
    result = BaselineValidator().validate(output, _ctx(baseline, "改个名字"))
    assert result.is_valid


def test_delete_with_intent_allowed():
    """用户指令含删除意图 → 允许删"""
    baseline = [
        {"id": "a", "name": "x", "type": "USER_TASK"},
        {"id": "b", "name": "y", "type": "USER_TASK"},
    ]
    output = {"nodes": [{"id": "a", "name": "x", "type": "USER_TASK"}]}
    result = BaselineValidator().validate(output, _ctx(baseline, "删掉 b 节点"))
    assert result.is_valid


def test_silent_delete_blocked():
    """静默删节点（指令无删除意图）→ 拦截"""
    baseline = [
        {"id": "a", "name": "x", "type": "USER_TASK"},
        {"id": "b", "name": "y", "type": "USER_TASK"},
    ]
    output = {"nodes": [{"id": "a", "name": "x", "type": "USER_TASK"}]}
    result = BaselineValidator().validate(output, _ctx(baseline, "加个审批节点"))
    assert not result.is_valid
    assert any(e.rule_id == "BASE_B001" for e in result.errors)


def test_edge_silent_delete_blocked():
    """静默删连线 → 拦截"""
    ctx = ValidatorContext(
        design_type="flow_design",
        mode="design",
        current_form_data={
            "nodes": [
                {"id": "a", "name": "x", "type": "START_EVENT"},
                {"id": "b", "name": "y", "type": "END_EVENT"},
            ],
            "edges": [{"source": "a", "target": "b"}],
        },
        user_input="改个名字",
    )
    output = {
        "nodes": [
            {"id": "a", "name": "x", "type": "START_EVENT"},
            {"id": "b", "name": "y", "type": "END_EVENT"},
        ],
        "edges": [],  # 删了连线
    }
    result = BaselineValidator().validate(output, ctx)
    assert not result.is_valid
    assert any(e.rule_id == "BASE_B002" for e in result.errors)


def test_add_node_may_split_the_original_outgoing_edge():
    ctx = ValidatorContext(
        design_type="flow_design",
        current_form_data={
            "nodes": [{"id": "a"}, {"id": "b"}],
            "edges": [{"source": "a", "target": "b"}],
        },
        user_input="在 a 后增加审批节点",
    )
    output = {
        "nodes": [{"id": "a"}, {"id": "new"}, {"id": "b"}],
        "edges": [
            {"source": "a", "target": "new"},
            {"source": "new", "target": "b"},
        ],
        "operations": [{"op": "add_node", "after_id": "a", "node": {"id": "new"}}],
    }

    assert BaselineValidator().validate(output, ctx).is_valid

    output["edges"].pop()
    assert not BaselineValidator().validate(output, ctx).is_valid


def test_confirmed_full_replacements_skip_baseline_retention_checks():
    flow_context = ValidatorContext(
        design_type="flow_design",
        current_form_data={"nodes": [{"id": "old"}]},
        allow_full_replace=True,
    )
    form_context = ValidatorContext(
        design_type="form_design",
        current_form_data={"widgetList": [{"options": {"name": "old"}}]},
        allow_full_replace=True,
    )

    assert (
        BaselineValidator()
        .validate(
            {"nodes": [{"id": "new"}], "operations": [{"op": "replace_graph"}]},
            flow_context,
        )
        .is_valid
    )
    assert (
        BaselineValidator()
        .validate(
            {
                "widgetList": [{"options": {"name": "new"}}],
                "operations": [{"op": "replace_form"}],
            },
            form_context,
        )
        .is_valid
    )


def test_form_widget_silent_delete_blocked():
    """静默删表单字段 → 拦截"""
    ctx = ValidatorContext(
        design_type="form_design",
        mode="design",
        current_form_data={
            "widgetList": [
                {"options": {"name": "field1"}},
                {"options": {"name": "field2"}},
            ]
        },
        user_input="改个标签",
    )
    output = {"widgetList": [{"options": {"name": "field1"}}]}
    result = BaselineValidator().validate(output, ctx)
    assert not result.is_valid
    assert any(e.rule_id == "BASE_B003" for e in result.errors)


def test_category_code_change_is_checked_by_category_validator():
    """分类编码允许修改，唯一性由 CategoryValidator 负责。"""
    ctx = ValidatorContext(
        design_type="category_design",
        mode="design",
        current_form_data={"category_name": "请假", "code": "leave_approval"},
        user_input="改个备注",
    )
    output = {"category_name": "请假", "code": "changed_code"}
    result = BaselineValidator().validate(output, ctx)
    assert result.is_valid
