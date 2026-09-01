"""
FlowMind 智能流程设计服务 - 请求级缓存

同一请求内避免重复查询后端（review 校验上下文）。
调用入口用 scope() 建立并清理 ContextVar，避免复用 worker 时跨请求串数据。
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

_cache: ContextVar[dict | None] = ContextVar("request_cache", default=None)


@contextmanager
def scope() -> Iterator[None]:
    """建立一次调用独享的缓存，并在调用结束后恢复上层上下文。"""
    token = _cache.set({})
    try:
        yield
    finally:
        _cache.reset(token)


def get(key: str, factory: Callable[[], Any]) -> Any:
    """取缓存，未命中用 factory() 计算并缓存（空结果也缓存，失败不缓存）"""
    cache = _cache.get()
    if cache is None:
        cache = {}
        _cache.set(cache)
    if key not in cache:
        cache[key] = factory()
    return cache[key]
