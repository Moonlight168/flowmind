"""
FlowMind 智能流程设计服务 - 节点基类

本模块提供节点装饰器，用于统一错误处理和日志记录。
日志采用三级级别（DEBUG/INFO/ERROR），通过LOG_LEVEL环境变量配置。
"""

import time
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

from app.graph.state.app_state import AppState
from app.infra.logger import (
    get_request_id,
    get_session_id,
    logger,
)

T = TypeVar("T", bound=AppState)


def node_handler(node_name: str = ""):
    """节点处理器装饰器。"""

    def decorator(func: Callable[[T], T]) -> Callable[[T], T]:
        @wraps(func)
        def wrapper(state: T) -> T:
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
            except Exception as e:
                # LangGraph interrupt() 在首次命中时会抛 GraphInterrupt 触发暂停，不能吞掉
                if e.__class__.__name__ == "GraphInterrupt":
                    raise

                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.error(
                    f"[{name}] 执行失败: {e!s}, 耗时{elapsed_ms}ms [{get_request_id()}] [{session_id}]"
                )
                return state

        return wrapper

    return decorator
