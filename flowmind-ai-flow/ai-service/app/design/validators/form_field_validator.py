"""
FlowMind 智能流程设计服务 - 表单字段级校验器

在 JSON 层校验表单 widgetList（form_design 专属），转换 VForm3 之前早失败。
"""

import re

from app.design.validators.base import (
    ValidationError,
    ValidationResult,
    ValidationSeverity,
    ValidatorContext,
)
from app.design.vform3_transformer import CONTAINER_TYPES, DISPLAY_TYPES, FIELD_TYPES

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
OPTION_ITEM_TYPES = {"radio", "checkbox", "select", "cascader"}
ALLOWED_WIDGET_TYPES = FIELD_TYPES | CONTAINER_TYPES | DISPLAY_TYPES


class FormFieldValidator:
    name = "form_field"

    def validate(self, output: dict, context: ValidatorContext) -> ValidationResult:
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []
        widgets = output.get("widgetList", []) or []

        # FORM_FF001: widgetList 非空
        if not widgets:
            errors.append(ValidationError("FORM_FF001", "widgetList 数组为空"))
            return ValidationResult.from_errors(errors)

        seen_names: set[str] = set()
        for widget in _walk_widgets(widgets):
            options = widget.get("options", {}) or {}
            name = options.get("name", "")
            widget_type = (widget.get("type") or "").lower()

            if widget_type and widget_type not in ALLOWED_WIDGET_TYPES:
                errors.append(
                    ValidationError(
                        "FORM_FF009",
                        f"不支持的 VForm3 组件: '{widget_type}'",
                        element_id=name,
                    )
                )

            requires_flag = widget_type != "grid-col"
            if not widget_type or (requires_flag and "formItemFlag" not in widget):
                errors.append(
                    ValidationError(
                        "FORM_FF002",
                        f"表单组件缺少 type/formItemFlag: {name or '<无name>'}",
                        element_id=name,
                    )
                )

            # 只有数据字段参与绑定名和业务属性校验，容器可使用内部名称。
            if widget_type in FIELD_TYPES:
                if not name:
                    errors.append(
                        ValidationError("FORM_FF002", "表单字段缺少 options.name")
                    )
                    continue
                if name in seen_names:
                    errors.append(
                        ValidationError(
                            "FORM_FF003", f"字段绑定名重复: '{name}'", element_id=name
                        )
                    )
                elif not NAME_PATTERN.match(name):
                    errors.append(
                        ValidationError(
                            "FORM_FF003",
                            f"字段绑定名不符合 [a-z][a-z0-9_]* 规范: '{name}'",
                            element_id=name,
                        )
                    )
                seen_names.add(name)

            # FORM_FF004: 选项类组件 optionItems 非空
            if widget_type in OPTION_ITEM_TYPES:
                if not options.get("optionItems"):
                    errors.append(
                        ValidationError(
                            "FORM_FF004",
                            f"{widget_type} 组件 '{name}' 的 optionItems 不能为空",
                            element_id=name,
                        )
                    )

            # FORM_FF005: required 与 disabled 互斥
            if (
                widget_type in FIELD_TYPES
                and options.get("required")
                and options.get("disabled")
            ):
                errors.append(
                    ValidationError(
                        "FORM_FF005",
                        f"字段 '{name}' 的 required 与 disabled 不能同时为 true",
                        element_id=name,
                    )
                )

            # FORM_FF006: cascader 嵌套 ≤3 层
            if widget_type == "cascader" and options.get("optionItems"):
                if _max_depth(options["optionItems"]) > 3:
                    warnings.append(
                        ValidationError(
                            "FORM_FF006",
                            f"cascader '{name}' 嵌套层级超过 3 层",
                            severity=ValidationSeverity.WARNING,
                            element_id=name,
                        )
                    )

            # FORM_FF007: label 非空且长度 1-30
            label = options.get("label", "")
            if widget_type in FIELD_TYPES and (not label or len(label) > 30):
                errors.append(
                    ValidationError(
                        "FORM_FF007",
                        f"字段 '{name}' 的 label 长度应为 1-30",
                        element_id=name,
                    )
                )

            # FORM_FF008: 容器 formItemFlag 必须为 false
            if (
                widget_type in (CONTAINER_TYPES - {"grid-col"})
                and widget.get("formItemFlag") is not False
            ):
                errors.append(
                    ValidationError(
                        "FORM_FF008",
                        f"容器组件 '{widget_type}' 的 formItemFlag 必须为 false",
                    )
                )
            if widget_type in CONTAINER_TYPES and not _has_valid_children(widget):
                errors.append(
                    ValidationError(
                        "FORM_FF010", f"容器组件 '{widget_type}' 的嵌套结构不合法"
                    )
                )

        return ValidationResult.from_errors(errors + warnings)


def _max_depth(items: list[dict]) -> int:
    """计算 optionItems 的最大嵌套深度"""
    depth = 1
    for item in items:
        children = item.get("children") or []
        if children:
            depth = max(depth, 1 + _max_depth(children))
    return depth


def _walk_widgets(widgets: list[dict]):
    for widget in widgets:
        yield widget
        yield from _walk_widgets(widget.get("widgetList") or [])
        for child in widget.get("cols") or []:
            yield from _walk_widgets([child])
        for child in widget.get("tabs") or []:
            yield from _walk_widgets(child.get("widgetList") or [])
        for row in widget.get("rows") or []:
            for cell in row.get("cols") or []:
                yield from _walk_widgets(cell.get("widgetList") or [])


def _has_valid_children(widget: dict) -> bool:
    widget_type = widget.get("type")
    if widget_type == "grid":
        return isinstance(widget.get("cols"), list) and all(
            child.get("type") == "grid-col" for child in widget["cols"]
        )
    child_key = {"card": "widgetList", "tab": "tabs", "table": "rows"}.get(widget_type)
    return child_key is None or isinstance(widget.get(child_key), list)
