"""
FlowMind 智能流程设计服务 - 分类校验器

在 JSON 层校验分类字段（category_design + flow_design basic 模式专属）。
"""

import re

from app.design.validators.base import (
    ValidationError,
    ValidationResult,
    ValidationSeverity,
    ValidatorContext,
)

CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class CategoryValidator:
    name = "category"

    def validate(self, output: dict, context: ValidatorContext) -> ValidationResult:
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []

        # basic 模式输出字段是 flow_name，兼容两种字段名
        name = output.get("category_name") or output.get("flow_name") or ""
        code = output.get("code", "") or ""
        remark = output.get("remark", "") or ""

        # CAT_C001: category_name 长度 1-30 非空白
        if not name or not name.strip() or len(name) > 30:
            errors.append(
                ValidationError("CAT_C001", f"分类名称长度应为 1-30 且非空白: '{name}'")
            )

        # CAT_C002: code 命名规范
        if not code or not CODE_PATTERN.match(code):
            errors.append(
                ValidationError(
                    "CAT_C002", f"分类编码不符合 [a-z][a-z0-9_]* 规范: '{code}'"
                )
            )

        # CAT_C003: code 唯一性（依赖 available_categories，空则跳过）
        current_id = context.current_form_data.get(
            "categoryId", context.current_form_data.get("id")
        )
        current_code = context.current_form_data.get("code")
        if context.categories_lookup_complete and code:
            if context.design_type == "category_design":
                other_categories = [
                    category
                    for category in context.available_categories
                    if not _is_current_category(category, current_id, current_code)
                ]
                available_codes = _category_codes(other_categories)
                # 新建：code 不应已存在
                if code in available_codes:
                    errors.append(
                        ValidationError(
                            "CAT_C003", f"分类编码 '{code}' 已存在，请换一个"
                        )
                    )
            elif context.design_type == "flow_design" and context.mode == "basic":
                # 选用：code 应已存在
                if code not in _category_codes(context.available_categories):
                    errors.append(
                        ValidationError(
                            "CAT_C003",
                            f"分类编码 '{code}' 不存在，请从 search_categories 结果中选择",
                        )
                    )

        # CAT_C004: remark 长度 ≤200
        if remark and len(remark) > 200:
            warnings.append(
                ValidationError(
                    "CAT_C004",
                    "备注长度超过 200 字",
                    severity=ValidationSeverity.WARNING,
                )
            )

        return ValidationResult.from_errors(errors + warnings)


def _is_current_category(
    category: dict, current_id: object | None, current_code: object | None
) -> bool:
    category_id = category.get("categoryId", category.get("id"))
    if current_id is not None and category_id is not None:
        return str(category_id) == str(current_id)
    return current_code is not None and str(category.get("code")) == str(current_code)


def _category_codes(categories: list[dict]) -> set[str]:
    return {
        str(category.get("code"))
        for category in categories
        if category.get("code") is not None
    }
