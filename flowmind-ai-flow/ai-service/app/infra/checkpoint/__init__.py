"""
FlowMind 智能流程设计服务 - 检查点单例

design/chat 两个 workflow 共享同一个 Redis checkpoint 实例。
"""

import time

from langgraph.checkpoint.memory import MemorySaver
from redis import RedisError

from app.config.settings import settings
from app.infra.checkpoint.redis import RedisCheckpoint
from app.infra.logger import logger

# 依赖未就绪时的重试间隔（秒）
_DEPENDENCY_RETRY_INTERVAL_SECONDS = 2.0


def _connect_checkpointer() -> RedisCheckpoint:
    """连接 Redis checkpoint，未就绪时在等待上限内反复重试。

    容器重启时 Redis 可能尚未就绪（DNS 解析不到 / 端口未监听），此处轮询等待。
    本地调试显式允许内存降级时不等待，直接快速失败。
    """
    checkpointer = RedisCheckpoint()
    wait_seconds = (
        0
        if settings.app.allow_memory_fallback
        else settings.app.startup_dependency_wait_seconds
    )
    deadline = time.monotonic() + wait_seconds
    while True:
        try:
            checkpointer.redis.ping()
            return checkpointer
        except (RedisError, OSError) as exc:
            if time.monotonic() >= deadline:
                raise
            logger.warning(
                f"Redis checkpoint 未就绪，{_DEPENDENCY_RETRY_INTERVAL_SECONDS}秒后重试: {exc!s}"
            )
            time.sleep(_DEPENDENCY_RETRY_INTERVAL_SECONDS)


try:
    checkpointer = _connect_checkpointer()
except (RedisError, OSError, ValueError, TypeError) as exc:
    # 会话数据必须可靠：Redis 连不上直接拒绝启动，避免生产静默降级为
    # 内存存储（重启即丢会话、会话锁失效）。显式配置 APP_ALLOW_MEMORY_FALLBACK=true
    # 才允许内存降级，仅供无 Redis 的本地调试。
    if not settings.app.allow_memory_fallback:
        raise RuntimeError(
            "Redis checkpoint 初始化失败，拒绝启动（本地调试可设置 "
            "APP_ALLOW_MEMORY_FALLBACK=true 允许内存降级）"
        ) from exc
    logger.warning(f"Redis checkpoint 初始化失败，降级到 MemorySaver: {exc!s}")
    checkpointer = MemorySaver()


def thread_exists(thread_id: str) -> bool:
    """兼容 RedisCheckpoint 与 MemorySaver 的线程存在性查询。"""
    exists = getattr(checkpointer, "thread_exists", None)
    if callable(exists):
        return bool(exists(thread_id))
    config = {"configurable": {"thread_id": thread_id}}
    return checkpointer.get_tuple(config) is not None


def save_preview(thread_id: str, user_input: str) -> None:
    """Redis 支持会话预览；MemorySaver debug 降级时安全跳过。"""
    saver = getattr(checkpointer, "save_preview", None)
    if callable(saver):
        saver(thread_id, user_input)


__all__ = ["checkpointer", "save_preview", "thread_exists"]
