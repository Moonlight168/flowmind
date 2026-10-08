"""
FlowMind 智能流程设计服务 - 依赖实体（表单/分类）缺失时的 review 行为测试

模型给出建议名（start_form_name / category_name）时，由前端在「应用变更」时创建实体，
本轮校验放行；模型没给建议名时退回追问，避免重试到死循环。
"""

from app.design.validators import (
    ValidationError,
    ValidationResult,
    ValidatorContext,
)
from app.graph.nodes.review import (
    _clear_pending_entity_errors,
    _design_clarification,
)


def _ctx(design_type: str = "flow_design", mode: str = "basic", **kw):
    return ValidatorContext(design_type=design_type, mode=mode, **kw)


def _result(*rule_ids: str) -> ValidationResult:
    return ValidationResult.from_errors(
        [ValidationError(rule_id, f"{rule_id} 说明") for rule_id in rule_ids]
    )


# ---------- 有建议名：放行，交给前端创建 ----------


def test_pending_start_form_clears_form_errors():
    result = _result("NODE_N010", "NODE_N005")

    _clear_pending_entity_errors(
        result, {"start_form_name": "请假申请单"}, _ctx(mode="design")
    )

    assert result.errors == []
    assert result.is_valid


def test_pending_category_clears_category_errors():
    result = _result("CAT_C005")

    _clear_pending_entity_errors(
        result, {"category_name": "人事管理"}, _ctx(mode="basic")
    )

    assert result.is_valid


def test_pending_name_does_not_clear_unrelated_errors():
    result = _result("NODE_N010", "EDGE_E001")

    _clear_pending_entity_errors(
        result, {"start_form_name": "请假申请单"}, _ctx(mode="design")
    )

    assert [e.rule_id for e in result.errors] == ["EDGE_E001"]
    assert not result.is_valid


def test_pending_category_does_not_clear_form_errors():
    """basic 模式只放行分类相关错误，其他规则不受影响。"""
    result = _result("NODE_N010", "CAT_C005")

    _clear_pending_entity_errors(
        result, {"category_name": "人事管理"}, _ctx(mode="basic")
    )

    assert [e.rule_id for e in result.errors] == ["NODE_N010"]


# ---------- 没有建议名：保持原样，退回追问 ----------


def test_no_pending_name_keeps_errors():
    result = _result("NODE_N010")

    _clear_pending_entity_errors(result, {}, _ctx(mode="design"))

    assert not result.is_valid


def test_blank_pending_name_is_ignored():
    result = _result("NODE_N010")

    _clear_pending_entity_errors(result, {"start_form_name": "   "}, _ctx(mode="design"))

    assert not result.is_valid


# ---------- 兜底追问 ----------


def test_unrelated_error_returns_none():
    errors = [ValidationError("CAT_C002", "分类编码不符合规范: ''")]
    assert _design_clarification(errors, _ctx()) is None


def test_empty_category_list_asks_user_to_create_one():
    msg = _design_clarification(
        [ValidationError("CAT_C005", "当前系统还没有流程分类")], _ctx()
    )

    assert msg is not None
    assert "没有流程分类" in msg


def test_mismatched_code_lists_available_categories():
    ctx = _ctx(
        available_categories=[
            {"categoryId": 1, "code": "hr", "categoryName": "人事管理"},
            {"categoryId": 2, "code": "fin", "categoryName": "财务管理"},
        ]
    )
    msg = _design_clarification(
        [ValidationError("CAT_C003", "分类编码 'invented' 不存在")], ctx
    )

    assert msg is not None
    assert "人事管理" in msg
    assert "财务管理" in msg


def test_category_design_code_conflict_is_not_a_user_question():
    """分类设计里"编码已存在"可以换一个重试，不该打断用户。"""
    ctx = _ctx(design_type="category_design", mode="design")
    errors = [ValidationError("CAT_C003", "分类编码 'hr' 已存在，请换一个")]

    assert _design_clarification(errors, ctx) is None


def test_no_form_asks_user_to_create_one():
    errors = [ValidationError("NODE_N010", "当前系统还没有表单")]
    msg = _design_clarification(errors, _ctx(mode="design"))

    assert msg is not None
    assert "没有表单" in msg
