"""
FlowMind 智能流程设计服务 - 模型适配器模块

本模块提供各种模型的适配器和统一管理功能。
"""

from app.adapters.base import (
    HttpModelAdapter,
    ModelAdapter,
    ModelConfig,
    ModelResponse,
)
from app.adapters.base.errors import ModelErrorCode, ModelError, classify_error
from app.adapters.factory import ModelFactory
from app.adapters.model_manager import ModelManager, ModelManagerConfig

__all__ = [
    "ModelErrorCode",
    "HttpModelAdapter",
    "ModelAdapter",
    "ModelConfig",
    "ModelError",
    "ModelFactory",
    "ModelManager",
    "ModelManagerConfig",
    "ModelResponse",
    "classify_error",
]
