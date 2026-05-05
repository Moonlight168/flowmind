"""
FlowMind 智能流程设计服务 - 日志模块

使用 structlog 实现结构化日志。

Usage:
    from app.infra.logger import logger

    logger.info("message")
    logger.bind(model_name="qwen", api_model="qwen3.6-flash").info("LLM调用")
"""

from .decorators import (
    log_api_endpoint,
    log_node_execution,
)
from .logger_config import (
    bind_contextvars,
    clear_contextvars,
    generate_request_id,
    generate_trace_id,
    get_logger,
    get_request_id,
    get_session_id,
    get_trace_id,
    log_context,
    logger,
    set_request_id,
    set_session_id,
    set_trace_id,
    setup_logging,
)

__all__ = [
    "bind_contextvars",
    "clear_contextvars",
    "generate_request_id",
    "generate_trace_id",
    "get_logger",
    "get_request_id",
    "get_session_id",
    "get_trace_id",
    "log_api_endpoint",
    "log_context",
    "log_node_execution",
    "logger",
    "set_request_id",
    "set_session_id",
    "set_trace_id",
    "setup_logging",
]
