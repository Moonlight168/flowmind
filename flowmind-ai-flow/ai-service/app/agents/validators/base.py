"""
FlowMind 智能流程设计服务 - 校验器基础类型

定义校验器协议、错误/结果类型与校验上下文。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


class ValidationSeverity(str, Enum):
    """校验严重级别"""

    ERROR = "error"  # 触发重试
    WARNING = "warning"  # 仅记录日志


@dataclass(frozen=True)
class ValidationError:
    """单条校验问题"""

    rule_id: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    element_id: str | None = None


@dataclass
class ValidationResult:
    """单个 Validator 的校验结果"""

    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    @classmethod
    def ok(cls) -> "ValidationResult":
        return cls(is_valid=True)

    @classmethod
    def from_errors(cls, errors: list[ValidationError]) -> "ValidationResult":
        real = [e for e in errors if e.severity is ValidationSeverity.ERROR]
        warns = [e for e in errors if e.severity is ValidationSeverity.WARNING]
        return cls(is_valid=not real, errors=real, warnings=warns)


@dataclass
class ValidatorContext:
    """校验上下文（review_node 构建）"""

    design_type: str = ""
    mode: str = "design"
    current_form_data: dict = field(default_factory=dict)
    available_forms: list[dict] = field(default_factory=list)
    available_categories: list[dict] = field(default_factory=list)
    existing_models: list[dict] = field(default_factory=list)
    auth_token: str | None = None
    thread_id: str | None = None


class Validator(Protocol):
    """校验器协议：实现 validate，返回 ValidationResult"""

    name: str

    def validate(self, output: dict, context: ValidatorContext) -> ValidationResult: ...
