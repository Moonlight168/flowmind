"""
FlowMind 智能流程设计服务 - 校验器单元测试
"""

from app.agents.validators import (
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


def test_node_start_missing_form_key():
    nodes = [{"id": "s", "name": "开始", "type": "START_EVENT"}]
    result = NodeValidator().validate({"nodes": nodes}, _ctx())
    assert any(e.rule_id == "NODE_N005" for e in result.errors)


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


# ---------- CategoryValidator ----------


def test_category_bad_code():
    result = CategoryValidator().validate(
        {"category_name": "请假", "code": "1bad"}, _ctx("category_design")
    )
    assert any(e.rule_id == "CAT_C002" for e in result.errors)


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
