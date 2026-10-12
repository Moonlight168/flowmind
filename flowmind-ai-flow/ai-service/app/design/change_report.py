"""把设计操作翻译成面向用户的变更摘要与明细。

只服务表单与流程模型两个场景：分类与流程基本信息只改几个文本字段，
前端沿用原有的字段 diff 呈现，不走这里。

明细按动作分组 —— 每个动作一行，行内列出受影响的字段/节点，
避免「一个字段一行」把面板撑长。
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from app.design.operations import find_widget

#: 分组：(动作, 摘要模板, 归入本组的操作)
_GROUPS: dict[str, list[tuple[str, str, tuple[str, ...]]]] = {
    "form": [
        ("add", "新增 {n} 个字段", ("add_widget",)),
        ("update", "修改 {n} 个字段", ("update_widget",)),
        ("remove", "删除 {n} 个字段", ("remove_widget",)),
        ("move", "调整 {n} 个字段位置", ("move_widget",)),
    ],
    "flow": [
        ("add", "新增 {n} 个节点", ("add_node",)),
        ("update", "修改 {n} 个节点", ("update_node",)),
        ("remove", "删除 {n} 个节点", ("remove_node",)),
        ("add", "新增 {n} 条连线", ("add_edge",)),
        ("update", "修改 {n} 条连线", ("update_edge",)),
        ("remove", "删除 {n} 条连线", ("remove_edge",)),
    ],
}

#: 表单组件属性 → 中文名
_WIDGET_ATTRS = {
    "defaultValue": "默认值",
    "required": "必填",
    "placeholder": "占位符",
    "label": "标题",
    "hidden": "隐藏",
    "readonly": "只读",
    "disabled": "禁用",
    "validation": "校验规则",
    "optionItems": "选项",
}

#: 流程节点属性 → 中文名
_NODE_ATTRS = {
    "name": "名称",
    "candidate_groups": "候选角色",
    "assignee": "审批人",
    "form_key": "表单",
    "type": "类型",
    "condition": "分支条件",
}


def build_change_report(
    design_type: str,
    operations: list[dict[str, Any]],
    baseline: dict[str, Any],
    result: dict[str, Any],
) -> tuple[str, list[dict[str, str]]]:
    """返回 (摘要, 明细行)。明细每项是 {action, text}，action 供前端着色。"""
    kind = "form" if design_type == "form_design" else "flow"
    ops = [op for op in operations if isinstance(op, dict)]
    counts = Counter(str(op.get("op") or "") for op in ops)

    replace_op = "replace_form" if kind == "form" else "replace_graph"
    if counts.get(replace_op):
        return _replace_report(kind, baseline, result)

    old_widgets = _baseline_widgets(baseline) if kind == "form" else []
    old_nodes = list(baseline.get("nodes") or [])

    summary_parts: list[str] = []
    details: list[dict[str, str]] = []
    for action, template, op_names in _GROUPS[kind]:
        group = [op for op in ops if str(op.get("op") or "") in op_names]
        if not group:
            continue
        label = template.format(n=len(group))
        # 修改项的正文里已用顿号分隔属性，项与项之间改用分号
        separator = "；" if action == "update" else "、"
        items = separator.join(
            _item_text(op, kind, old_widgets, old_nodes) for op in group
        )
        summary_parts.append(label)
        details.append({"action": action, "text": f"{label}：{items}"})
    return "、".join(summary_parts) or "更新设计", details


def _replace_report(
    kind: str, baseline: dict[str, Any], result: dict[str, Any]
) -> tuple[str, list[dict[str, str]]]:
    """整体替换：摘要给出规模变化，明细列出新内容的名称。"""
    if kind == "form":
        old_count = len(_baseline_widgets(baseline))
        names = [_widget_label(widget) for widget in result.get("widgetList") or []]
        unit, op_label = "个字段", "整体替换表单"
    else:
        old_count = len(baseline.get("nodes") or [])
        names = [
            str(node.get("name") or node.get("id") or "")
            for node in result.get("nodes") or []
        ]
        unit, op_label = "个节点", "整体替换流程图"

    new_count = len(names)
    summary = (
        f"{op_label}（{old_count} → {new_count} {unit}）"
        if old_count
        else f"生成 {new_count} {unit}"
    )
    fields = "、".join(name for name in names if name)
    if not fields or new_count > 8:
        return summary, []
    return summary, [{"action": "replace", "text": f"{summary}：{fields}"}]


def _item_text(
    operation: dict[str, Any],
    kind: str,
    old_widgets: list[dict[str, Any]],
    old_nodes: list[dict[str, Any]],
) -> str:
    op = str(operation.get("op") or "")
    if kind == "form":
        if op == "add_widget":
            return _widget_label(operation.get("widget") or {})
        if op in {"remove_widget", "move_widget"}:
            return _widget_display(old_widgets, operation.get("widget_name"))
        if op == "update_widget":
            return _update_widget_item(operation, old_widgets)
        return ""
    if op == "add_node":
        node = operation.get("node") or {}
        return str(node.get("name") or node.get("id") or "新节点")
    if op == "remove_node":
        return _node_label(old_nodes, operation.get("node_id"))
    if op == "update_node":
        return _update_node_item(operation, old_nodes)
    if op in {"add_edge", "update_edge", "remove_edge"}:
        return _edge_label(operation.get("edge") or operation)
    return ""


def _update_widget_item(
    operation: dict[str, Any], old_widgets: list[dict[str, Any]]
) -> str:
    widget_name = str(operation.get("widget_name") or "?")
    old_widget = find_widget(old_widgets, widget_name) or {}
    old_options = old_widget.get("options") or {}
    changes = operation.get("changes") or {}
    parts = [
        f"{_WIDGET_ATTRS.get(attr, attr)} {_format(old_options.get(attr))} → {_format(value)}"
        for attr, value in (changes.get("options") or {}).items()
    ]
    parts += [
        f"{_WIDGET_ATTRS.get(attr, attr)} {_format(old_widget.get(attr))} → {_format(value)}"
        for attr, value in changes.items()
        if attr != "options"
    ]
    label = _widget_display(old_widgets, widget_name)
    return f"{label} · {'、'.join(parts)}" if parts else f"{label} · 内容调整"


def _update_node_item(
    operation: dict[str, Any], old_nodes: list[dict[str, Any]]
) -> str:
    node_id = operation.get("node_id")
    old_node = _find_node(old_nodes, node_id) or {}
    parts = [
        f"{_NODE_ATTRS.get(attr, attr)} {_format(old_node.get(attr))} → {_format(value)}"
        for attr, value in (operation.get("changes") or {}).items()
    ]
    label = str(old_node.get("name") or node_id or "?")
    return f"{label} · {'、'.join(parts)}" if parts else label


def _baseline_widgets(baseline: dict[str, Any]) -> list[dict[str, Any]]:
    """基线里的组件列表。表单宿主传的是 content(JSON 字符串)，需解析。"""
    widgets = baseline.get("widgetList")
    if isinstance(widgets, list):
        return widgets
    content = baseline.get("content")
    if isinstance(content, str) and content.strip():
        try:
            content = json.loads(content)
        except json.JSONDecodeError:
            return []
    if isinstance(content, dict):
        parsed = content.get("widgetList")
        return parsed if isinstance(parsed, list) else []
    return []


def _find_node(nodes: list[dict[str, Any]], node_id: object) -> dict[str, Any] | None:
    return next((node for node in nodes if node.get("id") == node_id), None)


def _widget_label(widget: dict[str, Any]) -> str:
    options = widget.get("options") or {}
    return str(options.get("label") or options.get("name") or widget.get("type") or "新字段")


def _widget_display(old_widgets: list[dict[str, Any]], widget_name: object) -> str:
    """优先显示组件标题（用户看得懂的），取不到才退回内部字段名。"""
    widget = find_widget(old_widgets, str(widget_name or ""))
    if widget:
        return _widget_label(widget)
    return str(widget_name or "?")


def _node_label(nodes: list[dict[str, Any]], node_id: object) -> str:
    node = _find_node(nodes, node_id)
    return str((node or {}).get("name") or node_id or "?")


def _edge_label(edge: dict[str, Any]) -> str:
    name = edge.get("name")
    if name:
        return str(name)
    source = edge.get("source") or edge.get("sourceRef") or "?"
    target = edge.get("target") or edge.get("targetRef") or "?"
    return f"{source} → {target}"


def _format(value: Any) -> str:
    if value is None or value == "":
        return "未设置"
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, list):
        return "、".join(str(item) for item in value) or "无"
    return str(value)


__all__ = ["build_change_report"]
