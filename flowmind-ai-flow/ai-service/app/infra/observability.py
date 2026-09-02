"""
FlowMind 智能流程设计服务 - Langfuse 可观测性

统一维护工作流根观测和 LangChain 回调，保证 Workflow、Agent、LLM 与工具调用
位于同一条 Langfuse 链路中。未配置 Langfuse 密钥时自动禁用，不影响业务执行。
"""

import sys
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from functools import cache
from typing import Any

from langchain_core.callbacks import BaseCallbackManager
from langfuse import Langfuse, propagate_attributes
from langfuse.langchain import CallbackHandler

from app.config.settings import settings
from app.core.auth_context import get_current_user
from app.infra.logger import logger
from app.prompts.loader import get_prompt_metadata

OBSERVABILITY_ERRORS = (ValueError, RuntimeError, TypeError, OSError)
_langchain_handler: ContextVar[CallbackHandler | None] = ContextVar(
    "langfuse_langchain_handler", default=None
)


def observability_enabled() -> bool:
    """仅在密钥完整且未显式关闭追踪时启用 Langfuse。"""
    config = settings.observability
    return bool(config.public_key and config.secret_key and config.tracing_enabled)


@cache
def get_client() -> Langfuse:
    """使用统一 Settings 构造并缓存 Langfuse 客户端。"""
    config = settings.observability
    return Langfuse(
        public_key=config.public_key,
        secret_key=config.secret_key,
        base_url=config.base_url,
        tracing_enabled=config.tracing_enabled,
        environment=config.tracing_environment,
    )


def langchain_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """把当前 Langfuse 回调合并进 Runnable 配置。"""
    merged = dict(config or {})
    prompt_versions = get_prompt_metadata()
    if prompt_versions:
        metadata = dict(merged.get("metadata") or {})
        metadata["prompt_versions"] = prompt_versions
        merged["metadata"] = metadata
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
        handler = CallbackHandler(public_key=settings.observability.public_key)
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
        prompt_versions = get_prompt_metadata()
        if prompt_versions:
            record_observation_metadata(
                observation, {"prompt_versions": prompt_versions}
            )
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


def record_observation_metadata(
    observation: Any | None, metadata: dict[str, Any]
) -> None:
    """补充根观测元数据；监控异常不得影响业务结果。"""
    if observation is None:
        return
    try:
        observation.update(metadata=metadata)
    except OBSERVABILITY_ERRORS as exc:
        logger.warning(f"[langfuse] 记录元数据失败: {exc}")


@contextmanager
def observe_model_attempt(
    *,
    task_name: str | None,
    provider: str,
    attempt_index: int,
    fallback_enabled: bool,
    structured_required: bool,
    streaming: bool,
) -> Iterator[Any | None]:
    """在当前工作流下记录一次脱敏的 Provider 调用尝试。"""
    if not observability_enabled():
        yield None
        return

    metadata = {
        "task_name": task_name,
        "provider": provider,
        "attempt_index": attempt_index,
        "fallback_enabled": fallback_enabled,
        "structured_required": structured_required,
        "streaming": streaming,
    }
    stack = ExitStack()
    try:
        observation = stack.enter_context(
            get_client().start_as_current_observation(
                name="flowmind.model_attempt",
                as_type="span",
                metadata=metadata,
            )
        )
    except OBSERVABILITY_ERRORS as exc:
        logger.warning(f"[langfuse] 模型尝试观测初始化失败: {exc}")
        try:
            stack.close()
        except OBSERVABILITY_ERRORS as close_exc:
            logger.warning(f"[langfuse] 模型尝试观测清理失败: {close_exc}")
        yield None
        return

    try:
        yield observation
    finally:
        exception_info = sys.exc_info()
        try:
            stack.__exit__(*exception_info)
        except OBSERVABILITY_ERRORS as exc:
            logger.warning(f"[langfuse] 模型尝试观测结束失败: {exc}")


def shutdown_observability() -> None:
    """在进程退出前发送队列中尚未上报的观测数据。"""
    if not observability_enabled():
        return
    try:
        get_client().shutdown()
    except OBSERVABILITY_ERRORS as exc:
        logger.warning(f"[langfuse] 退出刷新失败: {exc}")


__all__ = [
    "get_client",
    "langchain_config",
    "observability_enabled",
    "observe_model_attempt",
    "observe_workflow",
    "record_observation_metadata",
    "record_observation_output",
    "shutdown_observability",
]
