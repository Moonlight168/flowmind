"""
FlowMind 智能流程设计服务 - 变更文案生成测试

build_change_report 把表单/流程模型的操作翻译成面向用户的摘要与明细，
按动作分组，每组一行。分类与流程基本信息走原有呈现，不经过这里。
"""

import json

from app.design.change_report import build_change_report


def _widget(name: str, label: str, **options) -> dict:
    return {
        "type": "input",
        "formItemFlag": True,
        "options": {"name": name, "label": label, **options},
    }


def _form_baseline(*widgets: dict) -> dict:
    return {"content": json.dumps({"widgetList": list(widgets)})}


def _lines(details: list[dict]) -> list[str]:
    """把 {label, detail} 还原成一行，便于按可读文本断言。"""
    return [f"{item['label']}：{item['detail']}" for item in details]


# ---------- 表单：整体替换 ----------


def test_form_replace_on_new_form_reports_generated_fields():
    result = {
        "widgetList": [_widget("applicant_name", "申请人"), _widget("leave_type", "请假类型")]
    }

    summary, details = build_change_report(
        "form_design", [{"op": "replace_form"}], {}, result
    )

    assert summary == "生成 2 个字段"
    assert details == [{"action": "replace", "label": "生成 2 个字段", "detail": "申请人、请假类型"}]


def test_form_replace_on_existing_form_reports_scale_change():
    baseline = _form_baseline(_widget("a", "甲"), _widget("b", "乙"))
    result = {"widgetList": [_widget("a", "甲"), _widget("b", "乙"), _widget("c", "丙")]}

    summary, details = build_change_report(
        "form_design", [{"op": "replace_form"}], baseline, result
    )

    assert summary == "整体替换表单（2 → 3 个字段）"
    assert _lines(details) == ["整体替换表单（2 → 3 个字段）：甲、乙、丙"]


def test_many_fields_keep_the_name_list_for_preview():
    """整体替换也必须有可展开的字段明细，不能只显示摘要。"""
    result = {"widgetList": [_widget(f"f{i}", f"字段{i}") for i in range(10)]}

    summary, details = build_change_report(
        "form_design", [{"op": "replace_form"}], {}, result
    )

    assert summary == "生成 10 个字段"
    assert _lines(details) == [
        "生成 10 个字段：" + "、".join(f"字段{i}" for i in range(10))
    ]


# ---------- 表单：增量（按动作分组，一行一组）----------


def test_form_groups_each_action_into_one_line():
    operations = [
        {"op": "add_widget", "widget": _widget("attachment", "附件")},
        {"op": "add_widget", "widget": _widget("approver", "审批人")},
        {
            "op": "update_widget",
            "widget_name": "leave_reason",
            "changes": {"options": {"placeholder": "请详细说明"}},
        },
    ]
    baseline = _form_baseline(
        _widget("leave_reason", "请假事由", placeholder="请输入请假事由")
    )

    summary, details = build_change_report("form_design", operations, baseline, {})

    assert summary == "新增 2 个字段、修改 1 个字段"
    assert details == [
        {"action": "add", "label": "新增 2 个字段", "detail": "附件、审批人"},
        {
            "action": "update",
            "label": "修改 1 个字段",
            "detail": "请假事由 · 占位符 请输入请假事由 → 请详细说明",
        },
    ]


def test_update_reads_old_value_from_nested_baseline():
    operations = [
        {
            "op": "update_widget",
            "widget_name": "leave_type",
            "changes": {"options": {"defaultValue": "personal", "required": True}},
        }
    ]
    baseline = {
        "content": (
            '{"widgetList": [{"type": "grid", "cols": [{"widgetList": '
            '[{"options": {"name": "leave_type", "label": "请假类型", '
            '"defaultValue": "", "required": false}}]}]}]}'
        )
    }

    _, details = build_change_report("form_design", operations, baseline, {})

    assert _lines(details) == ["修改 1 个字段：请假类型 · 默认值 未设置 → personal、必填 否 → 是"]


def test_remove_and_move_use_baseline_label_and_group_separately():
    operations = [
        {"op": "remove_widget", "widget_name": "old_field"},
        {"op": "move_widget", "widget_name": "leave_reason"},
    ]
    baseline = _form_baseline(_widget("old_field", "旧字段"), _widget("leave_reason", "请假事由"))

    summary, details = build_change_report("form_design", operations, baseline, {})

    assert summary == "删除 1 个字段、调整 1 个字段位置"
    assert details == [
        {"action": "remove", "label": "删除 1 个字段", "detail": "旧字段"},
        {"action": "move", "label": "调整 1 个字段位置", "detail": "请假事由"},
    ]


def test_widget_missing_from_baseline_falls_back_to_field_name():
    _, details = build_change_report(
        "form_design", [{"op": "remove_widget", "widget_name": "ghost"}], {}, {}
    )

    assert _lines(details) == ["删除 1 个字段：ghost"]


# ---------- 流程模型 ----------


def test_flow_replace_reports_scale_change():
    baseline = {"nodes": [{"id": "s", "name": "开始"}, {"id": "e", "name": "结束"}]}
    result = {
        "nodes": [
            {"id": "s", "name": "开始"},
            {"id": "m", "name": "主管审批"},
            {"id": "e", "name": "结束"},
        ]
    }

    summary, details = build_change_report(
        "flow_design", [{"op": "replace_graph"}], baseline, result
    )

    assert summary == "整体替换流程图（2 → 3 个节点）"
    assert _lines(details) == ["整体替换流程图（2 → 3 个节点）：开始、主管审批、结束"]


def test_flow_groups_nodes_and_edges_separately():
    operations = [
        {"op": "add_node", "node": {"id": "finance", "name": "财务审批"}},
        {"op": "add_edge", "edge": {"source": "a", "target": "b"}},
        {"op": "update_node", "node_id": "manager", "changes": {"name": "主管复核"}},
    ]
    baseline = {"nodes": [{"id": "manager", "name": "主管审批"}], "edges": []}

    summary, details = build_change_report("flow_design", operations, baseline, {})

    assert summary == "新增 1 个节点、修改 1 个节点、新增 1 条连线"
    assert details == [
        {"action": "add", "label": "新增 1 个节点", "detail": "财务审批"},
        {
            "action": "update",
            "label": "修改 1 个节点",
            "detail": "主管审批 · 名称 主管审批 → 主管复核",
        },
        {"action": "add", "label": "新增 1 条连线", "detail": "a → b"},
    ]


def test_flow_edge_prefers_name():
    _, details = build_change_report(
        "flow_design",
        [{"op": "remove_edge", "edge": {"name": "驳回", "source": "a", "target": "b"}}],
        {},
        {},
    )

    assert _lines(details) == ["删除 1 条连线：驳回"]
