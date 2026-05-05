"""
FlowMind 智能流程设计服务 - 日志配置

使用 structlog 实现结构化日志。
"""

import secrets
from contextlib import contextmanager

import structlog
from structlog.contextvars import (
    bind_contextvars,
    clear_contextvars,
    get_contextvars,
)

from app.config.settings import settings


def setup_logging():
    """配置 structlog 日志系统"""
    if settings.log.format == "simple":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer(ensure_ascii=False)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(settings.log.level.upper()),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """获取 logger 实例"""
    return structlog.get_logger(name)


# 默认 logger 实例
logger = get_logger()


# ============ 兼容旧接口的函数 ============


def generate_trace_id() -> str:
    """生成 trace_id"""
    return secrets.token_hex(4)


def generate_request_id() -> str:
    """生成 request_id"""
    return f"req-{secrets.token_hex(4)}"


def get_trace_id() -> str:
    """获取当前 trace_id"""
    return get_contextvars().get("trace_id", "-")


def set_trace_id(tid: str | None):
    """设置 trace_id"""
    if tid:
        bind_contextvars(trace_id=tid)


def get_request_id() -> str:
    """获取当前 request_id"""
    return get_contextvars().get("request_id", "-")


def set_request_id(rid: str | None):
    """设置 request_id"""
    if rid:
        bind_contextvars(request_id=rid)


def get_session_id() -> str:
    """获取当前 session_id"""
    return get_contextvars().get("session_id", "-")


def set_session_id(sid: str | None):
    """设置 session_id"""
    if sid:
        sid_str = sid[:8] if len(sid) > 8 else sid
        bind_contextvars(session_id=sid_str)


@contextmanager
def log_context(
    request_id: str | None = None,
    session_id: str | None = None,
    trace_id: str | None = None,
):
    """上下文管理器，临时设置日志上下文"""
    bind_contextvars(
        request_id=request_id or "-",
        session_id=session_id or "-",
        trace_id=trace_id or "-",
    )
    try:
        yield
    finally:
        clear_contextvars()


__all__ = [
    "bind_contextvars",
    "clear_contextvars",
    "generate_request_id",
    "generate_trace_id",
    "get_logger",
    "get_request_id",
    "get_session_id",
    "get_trace_id",
    "log_context",
    "logger",
    "set_request_id",
    "set_session_id",
    "set_trace_id",
    "setup_logging",
]
