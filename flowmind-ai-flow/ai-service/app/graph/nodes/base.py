"""
FlowMind 智能流程设计服务 - 节点基类

本模块提供节点装饰器，用于统一错误处理和日志记录。
日志采用三级级别（DEBUG/INFO/ERROR），通过LOG_LEVEL环境变量配置。
"""

import time
from collections.abc import Callable
from functools import wraps

import httpx
import redis
import requests
from langchain_core.messages import AIMessage
from langgraph.errors import GraphInterrupt
from openai import OpenAIError
from pydantic import ValidationError

from app.graph.state.app_state import AppState
from app.infra.logger import (
    get_request_id,
    get_session_id,
    logger,
)

NodeFunction = Callable[[AppState], AppState]
NODE_EXECUTION_ERRORS = (
    OpenAIError,
    httpx.HTTPError,
    redis.RedisError,
    requests.RequestException,
    ValidationError,
    RuntimeError,
    ValueError,
    TypeError,
    KeyError,
    AttributeError,
    ConnectionError,
    TimeoutError,
    OSError,
)
DESIGN_ERROR_MESSAGE = "AI 服务暂时异常，请稍后重试"
CHAT_ERROR_MESSAGE = "抱歉，AI 服务当前不可用，请稍后重试。"


def design_error_fallback(state: AppState) -> AppState:
    """将设计节点异常转换为工作流可路由的错误状态。"""
    state["intent"] = "error"
    state["design_output"] = {
        "intent": "error",
        "message": DESIGN_ERROR_MESSAGE,
        "error_type": "internal",
    }
    return state


def chat_error_fallback(state: AppState) -> AppState:
    """将聊天节点异常转换为稳定回复并保留消息历史。"""
    state["chat_response"] = CHAT_ERROR_MESSAGE
    state["messages"] = [
        *state.get("messages", []),
        AIMessage(content=CHAT_ERROR_MESSAGE),
    ]
    return state


def node_handler(
    node_name: str = "",
    fallback: NodeFunction = design_error_fallback,
) -> Callable[[NodeFunction], NodeFunction]:
    """统一记录节点耗时、异常，并返回对应工作流的兜底状态。"""

    def decorator(func: NodeFunction) -> NodeFunction:
        @wraps(func)
        def wrapper(state: AppState) -> AppState:
            name = node_name or func.__name__
            start_time = time.time()

            # session_id 从 context 读取，不从 state
            session_id = get_session_id()

            # 记录进入节点前的 chat_response，避免打印历史残留回复
            old_chat_response = str(state.get("chat_response", "") or "")

            try:
                result = func(state)
                elapsed_ms = int((time.time() - start_time) * 1000)

                # 仅记录本节点新产生的 AI 响应，避免历史状态误导排障
                chat_response = str(result.get("chat_response", "") or "")
                if chat_response and chat_response != old_chat_response:
                    preview = (
                        chat_response.replace("\r\n", "\n")
                        .replace("\r", "\n")
                        .replace("\n", "\\n")
                    )
                    logger.debug(f"[AI回复] {name} | {preview[:120]}...")

                logger.info(
                    f"[{name}] 执行完成, 耗时{elapsed_ms}ms [{get_request_id()}] [{session_id}]"
                )

                return result
            except GraphInterrupt:
                raise
            except NODE_EXECUTION_ERRORS as e:
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.error(
                    f"[{name}] 执行失败: {e!s}, 耗时{elapsed_ms}ms [{get_request_id()}] [{session_id}]"
                )
                return fallback(state)

        return wrapper

    return decorator
