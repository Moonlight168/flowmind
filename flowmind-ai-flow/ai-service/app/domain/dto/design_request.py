"""
FlowMind 智能流程设计服务 - 设计请求 DTO
"""

from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, Field


def _coerce_thread_id(value: object) -> object:
    """后端业务 id 是 Long，JSON 序列化后是数字，而 thread_id 契约是 str。

    不转换会得到 422（Input should be a valid string），且前端拿不到可读原因。
    """
    return None if value is None else str(value)


#: 会话标识。调用方可能直接传后端返回的数字 id，这里统一转成字符串
ThreadId = Annotated[str | None, BeforeValidator(_coerce_thread_id)]


class DesignRequestDTO(BaseModel):
    """设计请求 DTO"""

    user_input: str = Field(..., max_length=2000, description="用户输入文本")
    current_form_data: dict | None = Field(
        default=None, description="当前表单数据，用于提供上下文"
    )
    mode: Literal["basic", "design"] = Field(
        default="design",
        description="设计模式：basic（仅基本信息）或 design（含 BPMN XML）",
    )
    thread_id: ThreadId = Field(
        default=None,
        max_length=100,
        description="会话标识，用于区分同一用户的多个设计任务；不传则按用户+类型生成默认会话",
    )
    history_count: int | None = Field(
        default=None,
        ge=0,
        description="回退场景：只取前 N 条对话历史（版本指针）；不传则用完整历史",
    )
    allow_full_replace: bool = False


class RollbackRequestDTO(BaseModel):
    """回退设计会话历史请求（版本覆盖时裁剪 checkpoint 对话）"""

    message_count: int = Field(..., ge=0, description="裁剪到前 N 条消息")
    thread_id: ThreadId = Field(
        default=None,
        max_length=100,
        description="会话标识，同设计请求的 thread_id",
    )
    mode: Literal["basic", "design"] = Field(
        default="design",
        description="设计模式，与设计请求保持一致",
    )
