"""
FlowMind 智能流程设计服务 - SSE 同步生成器桥接

Starlette 迭代同步生成器时每个 chunk 都在线程池的不同 context copy 里执行，
导致生成器内 contextvar（prompt_metadata / request_cache / 观测）的 token
在退出时因 "created in a different Context" 而 reset 失败。

本模块把同步生成器放进单一工作线程跑完，再通过队列把事件逐条送回异步生成器，
保证 contextvar 的 set/reset 始终发生在同一个上下文，同时保留实时推送。

本模块是流式链路的收口边界：已知异常经队列传递，未知异常由 Future 保留。
调用方可将异常转换为安全的终止事件；未提供转换器时原样抛出。
"""

import asyncio
import json
from collections.abc import AsyncIterator, Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from contextvars import copy_context
from queue import Full, Queue
from threading import Event
from typing import Any

from app.core.exceptions import EXPECTED_RUNTIME_ERRORS, ErrorCode
from app.infra.logger import logger

_SENTINEL = object()
_QUEUE_PUT_TIMEOUT_SECONDS = 0.1


def stream_error_event(exc: Exception, trace_id: str) -> str:
    """流式响应已开始，记录原始异常并返回不含内部细节的错误事件。"""
    logger.error("SSE 工作线程失败", exc_info=(type(exc), exc, exc.__traceback__))
    event = {
        "type": "error",
        "status": "error",
        "error_type": ErrorCode.INTERNAL.value,
        "retryable": True,
        "message": "AI 服务暂时异常，请稍后重试",
        "trace_id": trace_id,
    }
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def _put_unless_stopped(queue: Queue, item: Any, stopped: Event) -> bool:
    while not stopped.is_set():
        try:
            queue.put(item, timeout=_QUEUE_PUT_TIMEOUT_SECONDS)
            return True
        except Full:
            continue
    return False


def _consume_source(source: Iterator[Any], queue: Queue, stopped: Event) -> None:
    try:
        for item in source:
            if not _put_unless_stopped(queue, item, stopped):
                break
    except EXPECTED_RUNTIME_ERRORS as exc:
        # 已知异常经队列转交；白名单外的异常由执行器 Future 保存。
        _put_unless_stopped(queue, exc, stopped)
    finally:
        close = getattr(source, "close", None)
        try:
            if callable(close):
                close()
        except EXPECTED_RUNTIME_ERRORS as exc:
            _put_unless_stopped(queue, exc, stopped)
        finally:
            _put_unless_stopped(queue, _SENTINEL, stopped)


def to_async_stream(
    source: Iterator[Any],
    maxsize: int = 64,
    on_error: Callable[[Exception], str] | None = None,
) -> AsyncIterator[Any]:
    """把同步生成器事件桥接为异步生成器（单工作线程执行 source）。"""
    request_context = copy_context()

    async def generator() -> AsyncIterator[Any]:
        queue: Queue = Queue(maxsize=maxsize)
        stopped = Event()
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="sse")
        worker = executor.submit(
            request_context.run, _consume_source, source, queue, stopped
        )
        try:
            while True:
                item = await asyncio.to_thread(queue.get)
                if item is _SENTINEL:
                    # Future 保留白名单外的异常，不能把线程失败当成正常 EOF。
                    item = await asyncio.to_thread(worker.exception)
                    if item is None:
                        break
                if isinstance(item, BaseException):
                    if on_error is not None and isinstance(item, Exception):
                        yield on_error(item)
                        break
                    raise item
                yield item
        finally:
            stopped.set()
            # 无条件投递结束信号，保证仍在阻塞 get 的线程池线程能够退出。
            # （put_nowait 抛 Full 说明队列已满，get 未处于阻塞态，不存在泄漏路径。）
            with suppress(Full):
                queue.put_nowait(_SENTINEL)
            executor.shutdown(wait=False, cancel_futures=True)

    return generator()
