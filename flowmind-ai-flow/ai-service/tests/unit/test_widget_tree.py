"""Widget 树遍历辅助的单元测试：AI 简化形态与 VForm3 文档形态。"""

from app.design.widget_tree import iter_child_lists, iter_widgets


def _name(widget: dict) -> str:
    return str((widget.get("options") or {}).get("name") or "")


def test_iter_widgets_covers_simplified_shape() -> None:
    # AI 简化形态：cols/tabs/rows 子项是 {widgetList} 容器（无 type）
    tree = [
        {
            "type": "grid",
            "options": {"name": "grid1"},
            "cols": [
                {
                    "widgetList": [
                        {"type": "input", "options": {"name": "a"}},
                        {
                            "type": "tab",
                            "tabs": [
                                {
                                    "widgetList": [
                                        {
                                            "type": "table",
                                            "rows": [
                                                {
                                                    "cols": [
                                                        {
                                                            "widgetList": [
                                                                {
                                                                    "type": "select",
                                                                    "options": {
                                                                        "name": "deep"
                                                                    },
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        },
                    ]
                }
            ],
        }
    ]
    assert {_name(w) for w in iter_widgets(tree) if _name(w)} == {
        "grid1",
        "a",
        "deep",
    }


def test_iter_widgets_covers_document_shape() -> None:
    # 文档形态：cols/tabs/rows 子项本身就是带 type 的 widget
    tree = [
        {
            "id": "1",
            "key": 1,
            "type": "grid",
            "options": {},
            "cols": [
                {
                    "id": "2",
                    "key": 2,
                    "type": "grid-col",
                    "internal": True,
                    "options": {},
                    "widgetList": [{"id": "3", "key": 3, "type": "input", "options": {}}],
                }
            ],
            "rows": [],
        }
    ]
    types = [w.get("type") for w in iter_widgets(tree)]
    assert types == ["grid", "grid-col", "input"]


def test_iter_child_lists_ignores_non_list_children() -> None:
    assert list(iter_child_lists({"widgetList": None, "cols": "bad"})) == []
