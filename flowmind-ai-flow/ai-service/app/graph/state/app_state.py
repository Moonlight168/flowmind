"""
FlowMind 智能流程设计服务 - 统一状态定义

最小化设计：只保留节点间必须传递的数据
"""

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AppState(TypedDict, total=False):
    """统一应用状态

    设计原则：
    - messages 是核心字段，所有历史通过它存取
    - design_type/mode 在 initial_state 传入，在节点间传递
    - Checkpoint 自动持久化所有状态字段
    """

    # 核心：消息历史（LangGraph add_messages 自动追加，Checkpoint 自动持久化）
    messages: Annotated[list[BaseMessage], add_messages]

    # design workflow 必须字段
    design_type: str | None
    mode: str | None
    current_form_data: dict | None

    # chat 专用
    chat_response: str | None

    # design 专用
    design_output: dict | None
    intent: str | None  # 标识 clarification/success

    # review 专用
    review_retry_count: int | None  # 审查重试计数
    review_error_history: (
        list[list[str]] | None
    )  # 最近 3 次错误 rule_id 集合（用于死循环检测）
