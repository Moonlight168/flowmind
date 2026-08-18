"""
FlowMind 智能流程设计服务 - 分类校验器

在 JSON 层校验分类字段（category_design + flow_design basic 模式专属）。
"""

import re

from app.agents.validators.base import (
    ValidationError,
    ValidationResult,
    ValidationSeverity,
    Validator,
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
            errors.append(ValidationError("CAT_C001", f"分类名称长度应为 1-30 且非空白: '{name}'"))

        # CAT_C002: code 命名规范
        if not code or not CODE_PATTERN.match(code):
            errors.append(ValidationError("CAT_C002", f"分类编码不符合 [a-z][a-z0-9_]* 规范: '{code}'"))

        # CAT_C003: code 唯一性（依赖 available_categories，空则跳过）
        available_codes = {
            str(c.get("code")) for c in context.available_categories if c.get("code") is not None
        }
        if available_codes and code:
            if context.design_type == "category_design":
                # 新建：code 不应已存在
                if code in available_codes:
                    errors.append(ValidationError("CAT_C003", f"分类编码 '{code}' 已存在，请换一个"))
            elif context.design_type == "flow_design" and context.mode == "basic":
                # 选用：code 应已存在
                if code not in available_codes:
                    errors.append(ValidationError("CAT_C003", f"分类编码 '{code}' 不存在，请从 search_categories 结果中选择"))

        # CAT_C004: remark 长度 ≤200
        if remark and len(remark) > 200:
            warnings.append(ValidationError(
                "CAT_C004", "备注长度超过 200 字", severity=ValidationSeverity.WARNING,
            ))

        # CAT_C005: category_name 重名（仅 category_design）
        if context.design_type == "category_design" and name and context.available_categories:
            existing_names = {c.get("categoryName") for c in context.available_categories if c.get("categoryName")}
            if name in existing_names:
                errors.append(ValidationError("CAT_C005", f"分类名称 '{name}' 与已有分类重名"))

        return ValidationResult.from_errors(errors + warnings)
