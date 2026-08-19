"""
FlowMind 智能流程设计服务 - 基线节点保留校验器

增量修改场景：拦截 LLM 静默删除基线节点（用户未要求删除却删了）。
"""

from app.agents.validators.base import (
    ValidationError,
    ValidationResult,
    Validator,
    ValidatorContext,
)
from app.infra.logger import logger

# 用户指令中表示"删除节点"意图的关键词（避免"不要/取消"误报："不要财务审批改成总监"是修改非删除）
DELETE_KEYWORDS = ("删", "去掉", "移除")


class BaselineValidator:
    name = "baseline"

    def validate(self, output: dict, context: ValidatorContext) -> ValidationResult:
        if context.design_type != "flow_design":
            return ValidationResult.ok()

        baseline_nodes = context.current_form_data.get("nodes") or []
        if not baseline_nodes:
            return ValidationResult.ok()

        baseline_ids = {n.get("id") for n in baseline_nodes if n.get("id")}
        output_ids = {n.get("id") for n in (output.get("nodes") or []) if n.get("id")}
        deleted = baseline_ids - output_ids

        if not deleted:
            return ValidationResult.ok()

        # 有节点被删，检查用户指令是否含删除意图
        user_input = context.user_input or ""
        has_delete_intent = any(kw in user_input for kw in DELETE_KEYWORDS)

        if has_delete_intent:
            logger.info(f"[baseline] 用户指令含删除意图，允许删除节点: {sorted(deleted)}")
            return ValidationResult.ok()

        return ValidationResult.from_errors([
            ValidationError(
                "BASE_B001",
                f"增量修改时删除了基线节点 {sorted(deleted)}，但用户未要求删除，请保留原有节点",
            )
        ])
