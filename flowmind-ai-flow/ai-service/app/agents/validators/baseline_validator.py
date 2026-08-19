"""
FlowMind 智能流程设计服务 - 基线保留校验器

增量修改场景：拦截 LLM 静默删除/修改基线内容（用户未要求却删/改了）。
覆盖 flow（nodes+edges）、form（widgetList）、category（code）。
"""

from app.agents.validators.base import (
    ValidationError,
    ValidationResult,
    ValidatorContext,
)
from app.infra.logger import logger

# 用户指令中表示"删除"意图的关键词（避免"不要/取消"误报："不要财务审批改成总监"是修改非删除）
DELETE_KEYWORDS = ("删", "去掉", "移除")


class BaselineValidator:
    name = "baseline"

    def validate(self, output: dict, context: ValidatorContext) -> ValidationResult:
        if context.design_type == "flow_design":
            return self._validate_flow(output, context)
        if context.design_type == "form_design":
            return self._validate_form(output, context)
        if context.design_type == "category_design":
            return self._validate_category(output, context)
        return ValidationResult.ok()

    def _has_delete_intent(self, context: ValidatorContext) -> bool:
        return any(kw in (context.user_input or "") for kw in DELETE_KEYWORDS)

    def _validate_flow(
        self, output: dict, context: ValidatorContext
    ) -> ValidationResult:
        baseline_nodes = context.current_form_data.get("nodes") or []
        if not baseline_nodes:
            return ValidationResult.ok()

        baseline_ids = {n.get("id") for n in baseline_nodes if n.get("id")}
        output_ids = {n.get("id") for n in (output.get("nodes") or []) if n.get("id")}
        deleted = baseline_ids - output_ids
        if deleted and not self._has_delete_intent(context):
            return ValidationResult.from_errors(
                [
                    ValidationError(
                        "BASE_B001",
                        f"删除了基线节点 {sorted(deleted)}，但用户未要求删除",
                    )
                ]
            )

        # edges 保留：基线的 source->target 连线不能被静默删
        baseline_edges = {
            (e.get("source"), e.get("target"))
            for e in (context.current_form_data.get("edges") or [])
        }
        output_edges = {
            (e.get("source"), e.get("target")) for e in (output.get("edges") or [])
        }
        deleted_edges = baseline_edges - output_edges
        if deleted_edges and not self._has_delete_intent(context):
            return ValidationResult.from_errors(
                [
                    ValidationError(
                        "BASE_B002",
                        f"删除了基线连线 {sorted(map(str, deleted_edges))}，但用户未要求删除",
                    )
                ]
            )
        return ValidationResult.ok()

    def _validate_form(
        self, output: dict, context: ValidatorContext
    ) -> ValidationResult:
        baseline_widgets = context.current_form_data.get("widgetList") or []
        if not baseline_widgets:
            return ValidationResult.ok()

        def _names(widgets):
            return {
                w.get("options", {}).get("name")
                for w in widgets
                if w.get("options", {}).get("name")
            }

        deleted = _names(baseline_widgets) - _names(output.get("widgetList") or [])
        if deleted and not self._has_delete_intent(context):
            return ValidationResult.from_errors(
                [
                    ValidationError(
                        "BASE_B003",
                        f"删除了基线字段 {sorted(deleted)}，但用户未要求删除",
                    )
                ]
            )
        return ValidationResult.ok()

    def _validate_category(
        self, output: dict, context: ValidatorContext
    ) -> ValidationResult:
        # category 增量：code 不应静默变（改 code 不是删除，删除意图不放行）
        baseline_code = context.current_form_data.get("code")
        output_code = output.get("code")
        if baseline_code and output_code and baseline_code != output_code:
            logger.info(
                f"[baseline] 分类 code 从 '{baseline_code}' 变为 '{output_code}'"
            )
            return ValidationResult.from_errors(
                [
                    ValidationError(
                        "BASE_B004",
                        f"分类 code 从 '{baseline_code}' 变为 '{output_code}'，但用户未要求修改",
                    )
                ]
            )
        return ValidationResult.ok()
