"""FlowMind AI 增量设计操作应用器。

所有操作都应用到基线深拷贝，调用方只有在校验通过后才使用返回结果。
"""

import json
from copy import deepcopy
from typing import Any


def apply_design_operations(
    design_type: str,
    baseline: dict[str, Any] | None,
    operations: list[dict[str, Any]],
    *,
    mode: str = "design",
) -> dict[str, Any]:
    """在基线副本上应用指定类型的增量操作。"""
    result = normalize_design_baseline(design_type, baseline)
    for operation in operations:
        if design_type == "flow_design" and mode == "basic":
            _apply_update_operation(result, operation, "update_flow_metadata")
        elif design_type == "flow_design":
            _apply_flow_operation(result, operation)
        elif design_type == "form_design":
            _apply_form_operation(result, operation)
        elif design_type == "category_design":
            _apply_update_operation(result, operation, "update_category")
        else:
            raise ValueError(f"不支持的设计类型: {design_type}")
    return result


def normalize_design_baseline(
    design_type: str, baseline: dict[str, Any] | None
) -> dict[str, Any]:
    """把前端传入的数据归一化为增量操作可直接使用的结构。"""
    result = deepcopy(baseline or {})
    if design_type == "category_design":
        result.setdefault("category_name", result.get("categoryName", ""))
    elif design_type == "flow_design":
        result.setdefault("flow_name", result.get("modelName", ""))
        result.setdefault("code", result.get("category", ""))
    if design_type != "form_design":
        return result
    content = result.get("content")
    if isinstance(content, str) and content.strip():
        try:
            form_json = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("当前表单 content 不是合法 JSON") from exc
    elif isinstance(content, dict):
        form_json = content
    else:
        form_json = {}
    result.setdefault("widgetList", deepcopy(form_json.get("widgetList") or []))
    result.setdefault("formConfig", deepcopy(form_json.get("formConfig") or {}))
    result.setdefault("form_name", result.get("formName", ""))
    return result


def _apply_flow_operation(result: dict[str, Any], operation: dict[str, Any]) -> None:
    op = operation.get("op")
    if op == "replace_graph":
        result["nodes"] = deepcopy(operation.get("nodes") or [])
        result["edges"] = deepcopy(operation.get("edges") or [])
        return
    if op == "add_node":
        _add_flow_node(result, operation)
        return
    if op == "update_node":
        node = _find_by_id(result.get("nodes", []), operation.get("node_id"))
        if node is None:
            raise ValueError(f"要修改的流程节点不存在: {operation.get('node_id')}")
        node.update(operation.get("changes") or {})
        return
    if op == "remove_node":
        _remove_flow_node(result, operation.get("node_id"))
        return
    if op == "add_edge":
        result.setdefault("edges", []).append(deepcopy(operation.get("edge") or {}))
        return
    if op in {"update_edge", "remove_edge"}:
        _change_flow_edge(result, operation, remove=op == "remove_edge")
        return
    raise ValueError(f"不支持的流程操作: {op}")


def _add_flow_node(result: dict[str, Any], operation: dict[str, Any]) -> None:
    node = deepcopy(operation.get("node") or {})
    if not node.get("id"):
        raise ValueError("新增流程节点缺少 id")
    nodes = result.setdefault("nodes", [])
    if _find_by_id(nodes, node["id"]):
        raise ValueError(f"流程节点 id 已存在: {node['id']}")
    nodes.append(node)
    after_id = operation.get("after_id")
    if after_id:
        _insert_after(result.setdefault("edges", []), after_id, node["id"])


def _insert_after(edges: list[dict[str, Any]], after_id: str, node_id: str) -> None:
    outgoing = [edge for edge in edges if edge.get("source") == after_id]
    if len(outgoing) > 1:
        raise ValueError(f"节点 {after_id} 存在多条出边，请明确目标连线")
    if not outgoing:
        edges.append({"source": after_id, "target": node_id})
        return
    original = outgoing[0]
    target = original.get("target")
    edges.remove(original)
    edges.extend(
        [
            {"source": after_id, "target": node_id},
            {"source": node_id, "target": target},
        ]
    )


def _remove_flow_node(result: dict[str, Any], node_id: str | None) -> None:
    nodes = result.setdefault("nodes", [])
    node = _find_by_id(nodes, node_id)
    if node is None:
        raise ValueError(f"要删除的流程节点不存在: {node_id}")
    nodes.remove(node)
    edges = result.setdefault("edges", [])
    incoming = [edge for edge in edges if edge.get("target") == node_id]
    outgoing = [edge for edge in edges if edge.get("source") == node_id]
    edges[:] = [
        edge
        for edge in edges
        if edge.get("source") != node_id and edge.get("target") != node_id
    ]
    if len(incoming) == 1 and len(outgoing) == 1:
        edges.append(
            {
                "source": incoming[0].get("source"),
                "target": outgoing[0].get("target"),
            }
        )


def _change_flow_edge(
    result: dict[str, Any], operation: dict[str, Any], *, remove: bool
) -> None:
    edges = result.setdefault("edges", [])
    edge = _find_edge(edges, operation)
    if edge is None:
        raise ValueError("要修改的流程连线不存在")
    if remove:
        edges.remove(edge)
    else:
        edge.update(operation.get("changes") or {})


def _find_edge(
    edges: list[dict[str, Any]], operation: dict[str, Any]
) -> dict[str, Any] | None:
    edge_id = operation.get("edge_id")
    if edge_id:
        return next((edge for edge in edges if edge.get("id") == edge_id), None)
    source, target = operation.get("source"), operation.get("target")
    return next(
        (
            edge
            for edge in edges
            if edge.get("source") == source and edge.get("target") == target
        ),
        None,
    )


def _apply_form_operation(result: dict[str, Any], operation: dict[str, Any]) -> None:
    op = operation.get("op")
    if op == "replace_form":
        result["widgetList"] = deepcopy(operation.get("widgetList") or [])
        result["formConfig"] = deepcopy(operation.get("formConfig") or {})
        if operation.get("form_name"):
            result["form_name"] = operation["form_name"]
        return
    if op == "add_widget":
        _add_form_widget(result, operation)
        return
    if op in {"update_widget", "remove_widget", "move_widget"}:
        _change_form_widget(result, operation)
        return
    raise ValueError(f"不支持的表单操作: {op}")


def _add_form_widget(result: dict[str, Any], operation: dict[str, Any]) -> None:
    widgets = result.setdefault("widgetList", [])
    widget = deepcopy(operation.get("widget") or {})
    name = _widget_name(widget)
    if not name:
        raise ValueError("新增表单字段缺少 options.name")
    if _find_widget(widgets, name):
        raise ValueError(f"表单字段已存在: {name}")
    index = _widget_insert_index(widgets, operation.get("after_name"))
    widgets.insert(index, widget)


def _change_form_widget(result: dict[str, Any], operation: dict[str, Any]) -> None:
    widgets = result.setdefault("widgetList", [])
    name = operation.get("widget_name")
    widget = _find_widget(widgets, name)
    if widget is None:
        raise ValueError(f"要修改的表单字段不存在: {name}")
    op = operation.get("op")
    if op == "remove_widget":
        widgets.remove(widget)
    elif op == "move_widget":
        widgets.remove(widget)
        widgets.insert(
            _widget_insert_index(widgets, operation.get("after_name")), widget
        )
    else:
        changes = deepcopy(operation.get("changes") or {})
        option_changes = changes.pop("options", None)
        widget.update(changes)
        if option_changes:
            widget.setdefault("options", {}).update(option_changes)


def _apply_update_operation(
    result: dict[str, Any], operation: dict[str, Any], expected_op: str
) -> None:
    if operation.get("op") != expected_op:
        raise ValueError(f"不支持的操作: {operation.get('op')}")
    result.update(deepcopy(operation.get("changes") or {}))


def _find_by_id(items: list[dict[str, Any]], item_id: str | None) -> dict | None:
    return next((item for item in items if item.get("id") == item_id), None)


def _widget_name(widget: dict[str, Any]) -> str:
    return str((widget.get("options") or {}).get("name") or "")


def _find_widget(
    widgets: list[dict[str, Any]], name: str | None
) -> dict[str, Any] | None:
    return next((widget for widget in widgets if _widget_name(widget) == name), None)


def _widget_insert_index(widgets: list[dict[str, Any]], after_name: str | None) -> int:
    if not after_name:
        return len(widgets)
    previous = _find_widget(widgets, after_name)
    if previous is None:
        raise ValueError(f"插入位置字段不存在: {after_name}")
    return widgets.index(previous) + 1
