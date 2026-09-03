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
    """

    user_input: str = Field(..., max_length=2000, description="用户输入文本")
    thread_id: str | None = Field(None, description="会话线程 ID")
