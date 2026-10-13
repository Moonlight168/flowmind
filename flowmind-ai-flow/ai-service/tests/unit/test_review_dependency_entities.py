"""Review behavior for dependencies created only after preview confirmation."""

from app.design.validators import ValidationError, ValidationResult, ValidatorContext
from app.graph.nodes.review import _clear_pending_entity_errors, _design_clarification


def _ctx(design_type: str = "flow_design", mode: str = "basic", **kw):
    return ValidatorContext(design_type=design_type, mode=mode, **kw)


def _result(*rule_ids: str) -> ValidationResult:
    return ValidationResult.from_errors(
        [ValidationError(rule_id, f"{rule_id} 说明") for rule_id in rule_ids]
    )


def _pending_start_form() -> dict:
    return {
        "nodes": [{"id": "start", "type": "START_EVENT", "name": "开始"}],
        "new_forms": [
            {
                "form_name": "申请信息表",
                "node_ids": ["start"],
                "widgetList": [
                    {
                        "type": "input",
                        "formItemFlag": True,
                        "options": {"name": "reason", "label": "申请原因"},
                    }
                ],
                "formConfig": {},
            }
        ],
    }


def test_complete_pending_start_form_clears_form_errors():
    result = _result("NODE_N010", "NODE_N005")

    _clear_pending_entity_errors(result, _pending_start_form(), _ctx(mode="design"))

    assert result.errors == []
    assert result.is_valid


def test_pending_category_clears_category_errors():
    result = _result("CAT_C005")

    _clear_pending_entity_errors(
        result, {"category_name": "人事管理"}, _ctx(mode="basic")
    )

    assert result.is_valid


def test_pending_form_does_not_clear_unrelated_errors():
    result = _result("NODE_N010", "EDGE_E001")

    _clear_pending_entity_errors(result, _pending_start_form(), _ctx(mode="design"))

    assert [error.rule_id for error in result.errors] == ["EDGE_E001"]
    assert not result.is_valid


def test_form_draft_for_other_node_does_not_clear_start_form_errors():
    result = _result("NODE_N010")
    output = _pending_start_form()
    output["new_forms"][0]["node_ids"] = ["manager"]

    _clear_pending_entity_errors(result, output, _ctx(mode="design"))

    assert not result.is_valid


def test_pending_category_does_not_clear_form_errors():
    result = _result("NODE_N010", "CAT_C005")

    _clear_pending_entity_errors(
        result, {"category_name": "人事管理"}, _ctx(mode="basic")
    )

    assert [error.rule_id for error in result.errors] == ["NODE_N010"]


def test_no_pending_entity_keeps_errors():
    result = _result("NODE_N010")

    _clear_pending_entity_errors(result, {}, _ctx(mode="design"))

    assert not result.is_valid


def test_unrelated_error_returns_none():
    errors = [ValidationError("CAT_C002", "分类编码格式错误")]
    assert _design_clarification(errors, _ctx()) is None


def test_empty_category_list_asks_user_to_create_one():
    message = _design_clarification(
        [ValidationError("CAT_C005", "当前系统还没有流程分类")], _ctx()
    )

    assert message is not None
    assert "没有流程分类" in message


def test_mismatched_code_lists_available_categories():
    context = _ctx(
        available_categories=[
            {"categoryId": 1, "code": "hr", "categoryName": "人事管理"},
            {"categoryId": 2, "code": "fin", "categoryName": "财务管理"},
        ]
    )
    message = _design_clarification(
        [ValidationError("CAT_C003", "分类编码不存在")], context
    )

    assert message is not None
    assert "人事管理" in message
    assert "财务管理" in message


def test_category_design_code_conflict_is_not_a_user_question():
    context = _ctx(design_type="category_design", mode="design")
    errors = [ValidationError("CAT_C003", "分类编码已存在")]

    assert _design_clarification(errors, context) is None


def test_missing_form_without_complete_draft_asks_for_input():
    errors = [ValidationError("NODE_N010", "当前系统还没有表单")]
    message = _design_clarification(errors, _ctx(mode="design"))

    assert message is not None
    assert "没有表单" in message
