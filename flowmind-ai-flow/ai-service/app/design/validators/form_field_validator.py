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

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
CONTAINER_TYPES = {"grid", "table", "tab", "card"}
OPTION_ITEM_TYPES = {"radio", "checkbox", "select", "cascader"}


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
        for widget in widgets:
            options = widget.get("options", {}) or {}
            name = options.get("name", "")
            widget_type = (widget.get("type") or "").lower()

            # FORM_FF002: type/formItemFlag/options.name
            if not widget_type or "formItemFlag" not in widget or not name:
                errors.append(
                    ValidationError(
                        "FORM_FF002",
                        f"表单字段缺少 type/formItemFlag/options.name: {name or '<无name>'}",
                        element_id=name,
                    )
                )

            # FORM_FF003: name 唯一 + 命名规范
            if name:
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
            if options.get("required") and options.get("disabled"):
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
            if not label or len(label) > 30:
                errors.append(
                    ValidationError(
                        "FORM_FF007",
                        f"字段 '{name}' 的 label 长度应为 1-30",
                        element_id=name,
                    )
                )

            # FORM_FF008: 容器 formItemFlag 必须为 false
            if (
                widget_type in CONTAINER_TYPES
                and widget.get("formItemFlag") is not False
            ):
                errors.append(
                    ValidationError(
                        "FORM_FF008",
                        f"容器组件 '{widget_type}' 的 formItemFlag 必须为 false",
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
