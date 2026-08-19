"""
FlowMind 智能流程设计服务 - 设计请求 DTO
"""

from pydantic import BaseModel, Field


class DesignRequestDTO(BaseModel):
    """设计请求 DTO"""

    user_input: str = Field(..., max_length=2000, description="用户输入文本")
    current_form_data: dict | None = Field(
        default=None, description="当前表单数据，用于提供上下文"
    )
    mode: str = Field(
        default="design",
        description="设计模式：basic（仅基本信息）或 design（含 BPMN XML）",
    )
    thread_id: str | None = Field(
        default=None,
        description="会话标识，用于区分同一用户的多个设计任务；不传则按用户+类型生成默认会话",
    )
