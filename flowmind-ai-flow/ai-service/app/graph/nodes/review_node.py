"""
FlowMind 智能流程设计服务 - 审查节点

本模块提供输出质量审查能力，基于 ReviewerAgent 实现。
审查失败时将错误反馈注入对话历史，触发重新生成。
"""

from typing import Any

from app.agents.reviewer import reviewer_agent
from app.graph.nodes.base import node_handler
from app.graph.state.app_state import AppState
from app.infra.logger import logger

MAX_RETRIES = 3


@node_handler("review")
def review_node(state: AppState) -> AppState:
    """审查节点

    使用 ReviewerAgent 审查 Agent 输出的质量。
    审查失败时将错误反馈加入对话历史，由 workflow 路由回 design 节点重新生成。
    """
    try:
        schema_name = state.get("schema_name", "")
        if not schema_name:
            logger.warning("审查节点：未指定 schema_name，跳过审查")
            state["review_passed"] = True
            return state

        output = _extract_output(state)
        if not output:
            logger.warning("审查节点：未能提取输出数据，跳过审查")
            state["review_passed"] = True
            return state

        review_result = reviewer_agent.review(output, schema_name, state)

        if review_result.passed:
            logger.debug("审查通过")
            state["review_passed"] = True
            state["review_errors"] = []
            return state

        # 审查未通过
        retry_count = state.get("review_retry_count", 0) + 1
        state["review_retry_count"] = retry_count
        state["review_passed"] = False
        state["review_errors"] = review_result.errors
        state["review_suggestions"] = review_result.suggestions

        if retry_count <= MAX_RETRIES:
            logger.warning(f"审查未通过（第 {retry_count} 次）：{review_result.errors}")
            # 将错误反馈加入对话历史，让 design agent 重新生成
            error_feedback = _build_error_feedback(review_result.errors)
            history = list(state.get("conversation_history", []))
            history.append({"role": "assistant", "content": error_feedback})
            state["conversation_history"] = history
        else:
            logger.error(f"审查失败，已达到最大重试次数 ({MAX_RETRIES})")

        return state

    except Exception as e:
        logger.error(f"审查节点执行失败：{e}")
        state["review_passed"] = False
        state["review_errors"] = [str(e)]
        return state


def _build_error_feedback(errors: list[str]) -> str:
    """构建错误反馈消息，注入对话历史引导重新生成"""
    error_list = "\n".join(f"- {e}" for e in errors)
    return f"上一轮输出格式不符合要求，请修正以下问题后重新生成：\n{error_list}"


def _extract_output(state: AppState) -> dict[str, Any] | None:
    """从状态中提取输出数据"""
    design_output = state.get("design_output") or {}
    return design_output.get("form_data") or design_output
