"""
FlowMind 智能流程设计服务 - Langfuse 可观测性

统一维护工作流根观测和 LangChain 回调，保证 Workflow、Agent、LLM 与工具调用
位于同一条 Langfuse 链路中。未配置 Langfuse 密钥时自动禁用，不影响业务执行。
"""

import os
import sys
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from typing import Any

from langchain_core.callbacks import BaseCallbackManager
from langfuse import get_client, propagate_attributes
from langfuse.langchain import CallbackHandler

from app.core.auth_context import get_current_user
from app.infra.logger import logger

OBSERVABILITY_ERRORS = (ValueError, RuntimeError, TypeError, OSError)
_langchain_handler: ContextVar[CallbackHandler | None] = ContextVar(
    "langfuse_langchain_handler", default=None
)


def observability_enabled() -> bool:
    """仅在密钥完整且未显式关闭追踪时启用 Langfuse。"""
    tracing_enabled = os.getenv("LANGFUSE_TRACING_ENABLED", "true").lower()
    return bool(
        os.getenv("LANGFUSE_PUBLIC_KEY")
        and os.getenv("LANGFUSE_SECRET_KEY")
        and tracing_enabled not in {"0", "false", "no", "off"}
    )


def langchain_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """把当前 Langfuse 回调合并进 Runnable 配置。"""
    merged = dict(config or {})
    handler = _langchain_handler.get()
    if handler is None:
        return merged

    callbacks = merged.get("callbacks")
    if callbacks is None:
        merged["callbacks"] = [handler]
    elif isinstance(callbacks, list):
        merged["callbacks"] = [*callbacks, handler]
    elif isinstance(callbacks, BaseCallbackManager):
        callback_manager = callbacks.copy()
        callback_manager.add_handler(handler)
        merged["callbacks"] = callback_manager
    else:
        raise TypeError(f"不支持的 callbacks 类型: {type(callbacks).__name__}")
    return merged


@contextmanager
def observe_workflow(
    name: str,
    *,
    input: dict[str, Any],
    session_id: str,
    trace_id: str,
    metadata: dict[str, Any] | None = None,
    tags: list[str] | None = None,
) -> Iterator[Any | None]:
    """创建工作流根观测，并向所有下游 LangChain 调用传播关联信息。"""
    if not observability_enabled():
        yield None
        return

    user = get_current_user()
    user_id = str(user.user_id) if user and user.user_id else None
    trace_metadata = {"business_trace_id": trace_id, **(metadata or {})}
    stack = ExitStack()
    try:
        client = get_client()
        stack.enter_context(
            propagate_attributes(
                user_id=user_id,
                session_id=session_id,
                tags=tags,
                metadata=trace_metadata,
                trace_name=name,
            )
        )
        observation = stack.enter_context(
            client.start_as_current_observation(
                name=name,
                as_type="agent",
                input=input,
                metadata=trace_metadata,
            )
        )
        handler = CallbackHandler()
    except OBSERVABILITY_ERRORS as exc:
        logger.warning(f"[langfuse] 初始化失败，本次调用降级为无观测: {exc}")
        try:
            stack.close()
        except OBSERVABILITY_ERRORS as close_exc:
            logger.warning(f"[langfuse] 清理失败: {close_exc}")
        yield None
        return

    token = _langchain_handler.set(handler)
    try:
        yield observation
    finally:
        _langchain_handler.reset(token)
        exception_info = sys.exc_info()
        try:
            stack.__exit__(*exception_info)
        except OBSERVABILITY_ERRORS as exc:
            logger.warning(f"[langfuse] 结束观测失败: {exc}")


def record_observation_output(observation: Any | None, output: Any) -> None:
    """记录根观测输出；监控异常不得影响业务结果。"""
    if observation is None:
        return
    try:
        observation.update(output=output)
    except OBSERVABILITY_ERRORS as exc:
        logger.warning(f"[langfuse] 记录输出失败: {exc}")


def shutdown_observability() -> None:
    """在进程退出前发送队列中尚未上报的观测数据。"""
    if not observability_enabled():
        return
    try:
        get_client().shutdown()
    except OBSERVABILITY_ERRORS as exc:
        logger.warning(f"[langfuse] 退出刷新失败: {exc}")


__all__ = [
    "langchain_config",
    "observability_enabled",
    "observe_workflow",
    "record_observation_output",
    "shutdown_observability",
]
