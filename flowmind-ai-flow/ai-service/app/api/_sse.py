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
from queue import Queue
from threading import Thread
from typing import Any

_SENTINEL = object()


def to_async_stream(
    source: Iterator[Any], maxsize: int = 64
) -> AsyncIterator[Any]:
    """把同步生成器事件桥接为异步生成器（单工作线程执行 source）。"""

    async def generator() -> AsyncIterator[Any]:
        queue: Queue = Queue(maxsize=maxsize)

        def run() -> None:
            try:
                for item in source:
                    queue.put(item)
            except BaseException as exc:
                queue.put(exc)
            finally:
                queue.put(_SENTINEL)

        worker = Thread(target=run, daemon=True)
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
            worker.join(timeout=1)

    return generator()
