"""
FlowMind 智能流程设计服务 - 基线节点保留校验器单元测试
"""

from app.agents.validators import BaselineValidator, ValidatorContext


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
