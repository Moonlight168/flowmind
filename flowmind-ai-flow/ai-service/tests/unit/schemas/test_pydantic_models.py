"""
FlowMind 智能流程设计服务 - Pydantic 设计 schema 单元测试
"""

import pytest
from pydantic import ValidationError

from app.domain.schemas.pydantic_models import (
    CategoryDesign,
    FlowDesign,
    FlowNode,
    FormDesign,
    FormWidget,
)


def test_flow_design_valid():
    obj = FlowDesign(nodes=[
        {"type": "START_EVENT", "id": "startEvent", "name": "开始", "form_key": "form1"},
        {"type": "USER_TASK", "id": "node_approve", "name": "审批", "candidate_groups": ["ROLE1"]},
        {"type": "END_EVENT", "id": "endEvent", "name": "结束"},
    ], edges=[
        {"source": "start", "target": "node_approve"},
        {"source": "node_approve", "target": "end"},
    ])
    assert len(obj.nodes) == 3
    assert len(obj.edges) == 2


def test_flow_node_invalid_type_rejected():
    with pytest.raises(ValidationError):
        FlowNode(type="ROBOT_TASK", id="x", name="x")


def test_flow_node_extra_field_rejected():
    with pytest.raises(ValidationError):
        FlowNode(type="USER_TASK", id="x", name="x", x=1, y=2)  # 坐标是锁定字段


def test_flow_node_missing_required():
    with pytest.raises(ValidationError):
        FlowNode(type="USER_TASK")  # 缺 id/name


def test_form_design_valid():
    obj = FormDesign(
        form_name="请假申请单",
        widgetList=[
            FormWidget(type="input", formItemFlag=True, options={"name": "reason", "label": "请假事由"}),
        ],
    )
    assert obj.form_name == "请假申请单"
    assert len(obj.widgetList) == 1


def test_category_design_valid():
    obj = CategoryDesign(category_name="请假审批", code="leave_approval")
    assert obj.code == "leave_approval"


def test_category_design_extra_rejected():
    with pytest.raises(ValidationError):
        CategoryDesign(category_name="x", code="x", unexpected_field="y")
