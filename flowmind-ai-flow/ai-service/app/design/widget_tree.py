"""VForm3 widget 树遍历辅助。

AI 简化形态与转换后的 VForm3 文档形态并存，且 cols/tabs/rows 的子项
在两种形态下结构不同（简化形态是 {widgetList} 容器，文档形态是带 type
的 widget）。统一按"有 type 视为 widget，否则视为容器"遍历，供操作器、
校验器与评测复用，避免各处维护略有差异的递归实现。
"""

from collections.abc import Iterator
from typing import Any


def iter_widgets(widgets: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    """深度优先产出树中所有 widget（含容器）。"""
    for widget in widgets:
        yield widget
        for child_widgets in iter_child_lists(widget):
            yield from iter_widgets(child_widgets)


def iter_child_lists(widget: dict[str, Any]) -> Iterator[list[dict[str, Any]]]:
    """产出 widget 的所有子 widget 列表。"""
    widget_list = widget.get("widgetList")
    if isinstance(widget_list, list):
        yield widget_list
    for key in ("cols", "tabs", "rows"):
        children = widget.get(key)
        if not isinstance(children, list):
            continue
        for child in children:
            if not isinstance(child, dict):
                continue
            if child.get("type"):
                # 文档形态：cols/tabs 的子项本身就是 widget
                yield [child]
            else:
                child_widgets = child.get("widgetList")
                if isinstance(child_widgets, list):
                    yield child_widgets
            if key == "rows":
                for cell in child.get("cols") or child.get("cells") or []:
                    if not isinstance(cell, dict):
                        continue
                    if cell.get("type"):
                        yield [cell]
                    else:
                        cell_widgets = cell.get("widgetList")
                        if isinstance(cell_widgets, list):
                            yield cell_widgets
