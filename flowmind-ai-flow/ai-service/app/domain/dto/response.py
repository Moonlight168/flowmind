"""
FlowMind 智能流程设计服务 - 统一返回格式

定义 AI 服务的统一 API 响应包装格式。
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseVO(BaseModel, Generic[T]):
    """统一返回包装

    Attributes:
        code: HTTP 状态码，200=成功，非200=失败
        message: 返回消息
        data: 泛型数据体
        trace_id: 追踪 ID
    """

    code: int = Field(default=200, description="HTTP 状态码")
    message: str = Field(default="success", description="返回消息")
    data: T | None = Field(default=None, description="泛型数据体")
    trace_id: str = Field(default="", description="追踪 ID")

    @classmethod
    def success(
        cls, data: T, message: str = "success", trace_id: str = ""
    ) -> ResponseVO[T]:
        """成功返回"""
        return cls(code=200, message=message, data=data, trace_id=trace_id)

    @classmethod
    def error(cls, code: int, message: str, trace_id: str = "") -> ResponseVO[None]:
        """错误返回"""
        return cls(code=code, message=message, data=None, trace_id=trace_id)
