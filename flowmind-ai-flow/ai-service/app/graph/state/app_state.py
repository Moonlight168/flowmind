"""
FlowMind 智能流程设计服务 - 统一状态定义

使用 LangGraph 1.0.x 单一状态。
"""

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AppState(TypedDict, total=False):
    """统一应用状态"""
    # ===== 基础 =====
    messages: Annotated[list[BaseMessage], add_messages]
    thread_id: str
    trace_id: str | None

    # ===== 通用 AI 回复 =====
    chat_response: str

    # ===== 设计相关 =====
    design_type: str | None
    user_input: str | None
    conversation_history: list[dict]
    current_form_data: dict | None
    mode: str | None
    schema_name: str | None

    # 设计结果
    design_output: dict | None
    raw_result: dict | None
    formatted_result: dict | None

    # 设计状态
    design_success: bool | None
    design_error: str | None
    review_passed: bool | None
    review_errors: list | None
    review_suggestions: list | None
    review_retry_count: int | None
    format_success: bool | None
    format_error: str | None

    # ===== 任务上下文 =====
    last_node: str | None
    node_execution_count: int
    task_context: dict
