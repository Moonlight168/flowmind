"""
FlowMind 智能流程设计服务 - 审查 Agent

本模块提供输出审查和自动重试能力，确保 Agent 输出符合 Schema 要求。
"""

from dataclasses import dataclass
from typing import Any

from langchain_core.messages import HumanMessage

from app.domain.schemas import SchemaRegistry
from app.graph.state import AppState
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

    MAX_RETRIES = 2

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

        # 2. 业务规则验证（可扩展）
        business_errors = self._validate_business_rules(output, context)
        errors.extend(business_errors)

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

    def _validate_business_rules(
        self,
        output: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> list[str]:
        """验证业务规则

        Args:
            output: 输出数据
            context: 上下文信息

        Returns:
            错误信息列表
        """
        # 当前无特定业务规则，预留扩展点
        return []

    def review_with_retry(
        self,
        agent_process_func,
        state: AppState,
        schema_name: str,
    ) -> AppState:
        """带重试的审查流程

        Args:
            agent_process_func: Agent 的 _process 方法
            state: 当前状态
            schema_name: Schema 名称

        Returns:
            更新后的状态
        """
        for attempt in range(self.MAX_RETRIES + 1):
            # 执行 Agent 处理
            result_state = agent_process_func(state)

            # 获取输出数据进行审查
            output = self._extract_output(state, schema_name)
            if not output:
                # 无法提取输出，直接返回
                return result_state

            # 审查输出
            review_result = self.review(output, schema_name, state)

            if review_result.passed:
                logger.debug(f"审查通过，尝试次数: {attempt + 1}")
                return result_state

            # 审查未通过，准备重试
            if attempt < self.MAX_RETRIES:
                logger.warning(
                    f"审查未通过（第 {attempt + 1} 次），错误: {review_result.errors}"
                )
                # 将错误反馈加入消息历史
                error_message = self._build_error_message(review_result.errors)
                state["messages"].append(HumanMessage(content=error_message))
            else:
                # 超过最大重试次数
                logger.error(f"审查失败，已达到最大重试次数 ({self.MAX_RETRIES})")
                state["review_failed"] = True
                state["review_errors"] = review_result.errors

        return state

    def _extract_output(
        self,
        state: AppState,
        schema_name: str,
    ) -> dict[str, Any] | None:
        """从状态中提取输出数据

        Args:
            state: 当前状态
            schema_name: Schema 名称

        Returns:
            输出数据或 None
        """
        # 根据 Schema 名称确定要提取的字段
        schema_to_field = {
            "category_classification": "category",
            "flow_design": "bpmn_structure",
            "form_generation": "form_json",
        }

        field_name = schema_to_field.get(schema_name)
        if field_name:
            return state.get(field_name)

        return None

    def _build_error_message(self, errors: list[str]) -> str:
        """构建错误反馈消息

        Args:
            errors: 错误列表

        Returns:
            格式化的错误消息
        """
        error_list = "\n".join(f"- {e}" for e in errors)
        return f"输出格式不符合要求，请修正以下问题：\n{error_list}"


# 全局审查器实例
reviewer_agent = ReviewerAgent()


def with_reviewer(schema_name: str):
    """审查装饰器工厂

    为 Agent 的 _process 方法添加审查和重试能力。

    Args:
        schema_name: Schema 名称

    Returns:
        装饰器函数

    Usage:
        class MyAgent(BaseAgent):
            @with_reviewer("my_schema")
            def _process(self, state: AppState) -> AppState:
                ...
    """
    def decorator(func):
        def wrapper(self, state: AppState) -> AppState:
            return reviewer_agent.review_with_retry(
                agent_process_func=func,
                state=state,
                schema_name=schema_name,
            )
        return wrapper
    return decorator
