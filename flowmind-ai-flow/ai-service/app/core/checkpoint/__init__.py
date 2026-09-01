"""
FlowMind 智能流程设计服务 - 检查点单例

design/chat 两个 workflow 共享同一个 Redis checkpoint 实例。
"""

from langgraph.checkpoint.memory import MemorySaver
from redis import RedisError

from app.config.settings import settings
from app.core.checkpoint.redis_checkpoint import RedisCheckpoint
from app.infra.logger import logger

try:
    checkpointer = RedisCheckpoint()
    checkpointer.redis.ping()
except (RedisError, OSError, ValueError, TypeError) as exc:
    if not settings.app.debug:
        raise RuntimeError("Redis checkpoint 初始化失败，生产环境禁止降级") from exc
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
