"""
FlowMind 智能流程设计服务 - 校验器编排管线

顺序执行所有 Validator，合并结果，并提供死循环检测。
"""

from app.agents.validators.base import (
    ValidationError,
    ValidationResult,
    Validator,
    ValidatorContext,
)


class ValidatorPipeline:
    """顺序执行校验器并聚合结果"""

    def __init__(self, validators: list[Validator]):
        self.validators = validators

    def run(self, output: dict, context: ValidatorContext) -> ValidationResult:
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []
        for validator in self.validators:
            result = validator.validate(output, context)
            errors.extend(result.errors)
            warnings.extend(result.warnings)
        return ValidationResult(is_valid=not errors, errors=errors, warnings=warnings)

    def detect_loop(
        self,
        current_errors: list[ValidationError],
        history: list[frozenset[str]],
    ) -> bool:
        """连续 2 次错误 rule_id 集合完全相同 → 判定为死循环"""
        current = frozenset(e.rule_id for e in current_errors)
        if not current:
            return False
        return bool(history and history[-1] == current)
