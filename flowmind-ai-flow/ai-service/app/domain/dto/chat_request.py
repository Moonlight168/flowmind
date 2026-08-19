"""
FlowMind 智能流程设计服务 - 对话请求 DTO
"""

from pydantic import BaseModel, Field


class ChatRequestDTO(BaseModel):
    """对话请求 DTO

    用于接收前端的多轮对话请求。

    Attributes:
        user_input: 用户输入文本
        thread_id: 会话线程 ID（新建会话时为 None）
        control_intent: 控制意图（confirm/modify/cancel）
        confirmation_id: 确认流程 ID
    """

    user_input: str = Field(..., max_length=2000, description="用户输入文本")
    thread_id: str | None = Field(None, description="会话线程 ID")
    control_intent: str | None = Field(None, description="控制意图")
    confirmation_id: str | None = Field(None, description="确认流程 ID")
