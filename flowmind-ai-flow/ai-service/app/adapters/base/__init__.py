"""
FlowMind 智能流程设计服务 - 模型适配器基类模块

本模块提供模型适配器的基础组件。

文件结构:
- adapter.py: 抽象基类和数据结构（ModelAdapter, ModelConfig, ModelResponse）
- http_adapter.py: HTTP 实现基类（HttpModelAdapter, StandardHttpAdapter）
"""

from app.adapters.base.adapter import (
    ModelAdapter,
    ModelConfig,
    ModelResponse,
)
from app.adapters.base.http_adapter import (
    HttpAdapterConfig,
    HttpModelAdapter,
    StandardHttpAdapter,
    # JSON Schema 工具
    build_json_schema,
    # 构建器
    build_openai_compatible_payload,
    # 解析器
    parse_openai_response,
)

__all__ = [
    "build_json_schema",
    "build_openai_compatible_payload",
    "HttpAdapterConfig",
    "HttpModelAdapter",
    "ModelAdapter",
    "ModelConfig",
    "ModelResponse",
    "parse_openai_response",
    "StandardHttpAdapter",
]
