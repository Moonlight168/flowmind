"""
FlowMind 智能流程设计服务 - 模型适配器基类模块

本模块提供模型适配器的基础组件和错误类型。
"""

from app.adapters.base.errors import ModelError, ModelErrorCode, classify_error

__all__ = [
    "ModelError",
    "ModelErrorCode",
    "classify_error",
]
