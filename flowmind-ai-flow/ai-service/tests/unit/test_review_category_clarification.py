"""
FlowMind 智能流程设计服务 - 依赖数据不可用时的用户追问测试

系统没有分类/表单、或模型引用的分类不存在时，重试无法修复，
应转为向用户追问（clarification），而不是校验失败重试到死循环。
"""

from app.design.validators import ValidationError, ValidatorContext
from app.graph.nodes.review import _design_clarification


def _ctx(design_type: str = "flow_design", mode: str = "basic", **kw):
    return ValidatorContext(design_type=design_type, mode=mode, **kw)


def test_unrelated_error_returns_none():
    errors = [ValidationError("CAT_C002", "分类编码不符合规范: ''")]
    assert _design_clarification(errors, _ctx()) is None


def test_empty_category_list_asks_user_to_create_one():
    msg = _design_clarification(
        [ValidationError("CAT_C005", "当前系统还没有流程分类")], _ctx()
    )

    assert msg is not None
    assert "没有流程分类" in msg
    assert "创建" in msg


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
    ctx = _ctx(mode="design")
    msg = _design_clarification(
        [ValidationError("NODE_N005", "开始节点缺少 form_key")], ctx
    )
    assert msg is None  # NODE_N005 可重试，不在此列

    msg = _design_clarification(
        [ValidationError("NODE_N010", "当前系统还没有表单")], ctx
    )
    assert msg is not None
    assert "没有表单" in msg
    assert "创建" in msg
