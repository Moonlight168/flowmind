"""
FlowMind 智能流程设计服务 - SSE 同步生成器桥接

Starlette 迭代同步生成器时每个 chunk 都在线程池的不同 context copy 里执行，
导致生成器内 contextvar（prompt_metadata / request_cache / 观测）的 token
在退出时因 "created in a different Context" 而 reset 失败。

本模块把同步生成器放进单一工作线程跑完，再通过队列把事件逐条送回异步生成器，
保证 contextvar 的 set/reset 始终发生在同一个上下文，同时保留实时推送。
"""

import asyncio
from collections.abc import AsyncIterator, Iterator
from contextvars import copy_context
from queue import Full, Queue
from threading import Event, Thread
from typing import Any

_SENTINEL = object()
_QUEUE_PUT_TIMEOUT_SECONDS = 0.1
_SOURCE_ERRORS = (
    RuntimeError,
    ValueError,
    TypeError,
    OSError,
    LookupError,
    AttributeError,
)


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
    except _SOURCE_ERRORS as exc:
        # 跨线程转交后会在请求协程中原样抛出，不在此处吞掉异常。
        _put_unless_stopped(queue, exc, stopped)
    finally:
        close = getattr(source, "close", None)
        try:
            if callable(close):
                close()
        except _SOURCE_ERRORS as exc:
            _put_unless_stopped(queue, exc, stopped)
        finally:
            _put_unless_stopped(queue, _SENTINEL, stopped)


def to_async_stream(source: Iterator[Any], maxsize: int = 64) -> AsyncIterator[Any]:
    """把同步生成器事件桥接为异步生成器（单工作线程执行 source）。"""
    request_context = copy_context()

    async def generator() -> AsyncIterator[Any]:
        queue: Queue = Queue(maxsize=maxsize)
        stopped = Event()
        worker = Thread(
            target=request_context.run,
            args=(_consume_source, source, queue, stopped),
            daemon=True,
        )
        worker.start()
        try:
            while True:
                item = await asyncio.to_thread(queue.get)
                if item is _SENTINEL:
                    break
                if isinstance(item, BaseException):
                    raise item
                yield item
        finally:
            stopped.set()
            await asyncio.to_thread(worker.join, 1)

    return generator()
