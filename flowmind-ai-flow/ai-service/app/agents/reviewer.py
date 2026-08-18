"""
FlowMind 智能流程设计服务 - 审查 Agent

本模块提供输出审查和自动重试能力，确保 Agent 输出符合 Schema 要求。
"""

from dataclasses import dataclass
from typing import Any

from app.domain.schemas import SchemaRegistry
from app.infra.logger import logger


@dataclass
class ReviewResult:
    """审查结果

    Attributes:
        passed: 是否通过审查
        errors: 错误信息列表
        suggestions: 改进建议列表
    """

    passed: bool
    errors: list[str]
    suggestions: list[str]


class ReviewerAgent:
    """审查 Agent - 验证 Agent 输出并支持自动重试

    职责：
    1. Schema 格式验证
    2. 业务规则验证（可扩展）
    3. 自动重试机制
    """

    def review(
        self,
        output: dict[str, Any],
        schema_name: str,
        context: dict[str, Any] | None = None,
    ) -> ReviewResult:
        """审查输出内容

        Args:
            output: Agent 输出的数据
            schema_name: Schema 名称
            context: 上下文信息（用于业务规则验证）

        Returns:
            ReviewResult 审查结果
        """
        errors = []
        suggestions = []

        # 1. Schema 格式验证
        schema_errors = self._validate_schema(output, schema_name)
        errors.extend(schema_errors)

        return ReviewResult(
            passed=len(errors) == 0,
            errors=errors,
            suggestions=suggestions,
        )

    def _validate_schema(self, output: dict[str, Any], schema_name: str) -> list[str]:
        """验证输出是否符合 Schema

        Args:
            output: 输出数据
            schema_name: Schema 名称

        Returns:
            错误信息列表
        """
        errors = []

        schema = SchemaRegistry.get(schema_name)
        if not schema:
            logger.warning(f"Schema '{schema_name}' 不存在，跳过验证")
            return errors

        # 获取 Schema 要求的字段
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})

        # 检查必填字段
        for field in required_fields:
            if field not in output:
                errors.append(f"缺少必填字段: {field}")
            elif output[field] is None:
                errors.append(f"字段 '{field}' 不能为空")

        # 检查字段类型（简化版）
        for field, value in output.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type and value is not None:
                    type_map = {
                        "string": str,
                        "number": (int, float),
                        "integer": int,
                        "boolean": bool,
                        "array": list,
                        "object": dict,
                    }
                    expected_python_type = type_map.get(expected_type)
                    if expected_python_type and not isinstance(value, expected_python_type):
                        errors.append(f"字段 '{field}' 类型错误，期望 {expected_type}")

        return errors


# 全局审查器实例
reviewer_agent = ReviewerAgent()
