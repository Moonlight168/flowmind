"""
FlowMind 智能流程设计服务 - Redis 检查点存储

本模块实现基于 Redis 的对话存储，支持：
- 对话状态持久化（存储/恢复）
- 对话列表查询（支持预览、时间）
- 对话删除

Key 结构：
- checkpoint:design:{thread_id}:{checkpoint_id} - LangGraph 内部检查点
- chat:thread:{thread_id} - 简化版对话数据（供列表查询用）
- chat:threads - 所有对话 thread_id 集合
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import ormsgpack
import redis
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    JsonPlusSerializer,
)

from app.config.settings import SECONDS_PER_HOUR, settings

logger = logging.getLogger(__name__)


class RedisCheckpoint(BaseCheckpointSaver):
    """Redis 对话存储（LangGraph 检查点标准接口 + 简化列表管理）"""

    # LangGraph 内部前缀
    CHECKPOINT_PREFIX = "checkpoint"
    METADATA_PREFIX = "metadata"

    # 简化版 key 前缀
    CHAT_PREFIX = "chat"
    CHAT_THREADS_KEY = "chat:threads"

    def __init__(
        self,
        redis_url: str | None = None,
        ttl_hours: int | None = None,
    ):
        super().__init__(serde=JsonPlusSerializer())

        if redis_url:
            self.redis = redis.from_url(redis_url)
        else:
            self.redis = redis.Redis(
                host=settings.redis.host,
                port=settings.redis.port,
                db=settings.redis.db,
                password=settings.redis.password,
                decode_responses=False,
            )

        ttl = (
            ttl_hours if ttl_hours is not None else settings.redis.checkpoint_ttl_hours
        )
        self.ttl_seconds = ttl * SECONDS_PER_HOUR

        logger.info(f"RedisCheckpoint initialized, TTL={ttl}h")

    def _checkpoint_key(self, thread_id: str, ns: str = "") -> str:
        """LangGraph 检查点键"""
        return f"{self.CHECKPOINT_PREFIX}:{ns}:{thread_id}"

    def _metadata_key(self, thread_id: str, ns: str = "") -> str:
        """LangGraph 元数据键"""
        return f"{self.METADATA_PREFIX}:{ns}:{thread_id}"

    def _chat_thread_key(self, thread_id: str) -> str:
        """简化版对话数据键"""
        return f"{self.CHAT_PREFIX}:thread:{thread_id}"

    @staticmethod
    def _sanitize_checkpoint(checkpoint: Checkpoint) -> Checkpoint:
        """移除不应持久化的敏感字段"""
        if not isinstance(checkpoint, dict):
            return checkpoint

        channel_values = checkpoint.get("channel_values")
        if isinstance(channel_values, dict) and "auth_token" in channel_values:
            channel_values = dict(channel_values)
            channel_values.pop("auth_token", None)
            checkpoint = {**checkpoint, "channel_values": channel_values}

        return checkpoint

    def get(self, config: RunnableConfig) -> Checkpoint | None:
        """获取单个检查点"""
        tuple_data = self.get_tuple(config)
        return tuple_data.checkpoint if tuple_data else None

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """获取单个检查点及其元数据"""
        configurable = config["configurable"]
        thread_id = configurable["thread_id"]
        ns = configurable.get("checkpoint_ns", "")

        key = self._checkpoint_key(thread_id, ns)
        data = self.redis.get(key)
        if not data:
            return None

        self.redis.expire(key, self.ttl_seconds)

        typed = ormsgpack.unpackb(data)
        payload = self.serde.loads_typed(typed)
        logger.debug(f"Got checkpoint from Redis: thread_id={thread_id}")
        return CheckpointTuple(
            config=config,
            checkpoint=payload["checkpoint"],
            metadata=payload["metadata"],
        )

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """保存检查点"""
        configurable = config["configurable"]
        thread_id = configurable["thread_id"]
        ns = configurable.get("checkpoint_ns", "")

        sanitized_checkpoint = self._sanitize_checkpoint(checkpoint)

        # 保存 LangGraph 检查点
        payload = {
            "checkpoint": sanitized_checkpoint,
            "metadata": metadata,
            "new_versions": new_versions,
        }
        key = self._checkpoint_key(thread_id, ns)
        typed = self.serde.dumps_typed(payload)
        self.redis.setex(key, self.ttl_seconds, ormsgpack.packb(typed))

        # 保存简化版数据（用于列表查询）
        self._save_chat_thread(thread_id, sanitized_checkpoint)

        logger.debug(f"Checkpoint saved: thread_id={thread_id}")

        return {
            **config,
            "configurable": {
                **configurable,
                "checkpoint_id": checkpoint["id"],
            },
        }

    def _save_chat_thread(self, thread_id: str, checkpoint: Checkpoint) -> None:
        """保存简化版对话数据"""
        try:
            # 提取第一条用户消息作为预览
            preview = "新对话"
            updated_at = datetime.now().isoformat()

            channel_values = (
                checkpoint.get("channel_values", {})
                if isinstance(checkpoint, dict)
                else {}
            )
            messages = (
                channel_values.get("messages", [])
                if isinstance(channel_values, dict)
                else []
            )

            for msg in messages:
                if hasattr(msg, "type") and msg.type == "human":
                    content = msg.content if hasattr(msg, "content") else ""
                    if content:
                        preview = content[:50] + ("..." if len(content) > 50 else "")
                    break
                elif isinstance(msg, dict) and msg.get("type") == "human":
                    content = msg.get("content", "")
                    if content:
                        preview = content[:50] + ("..." if len(content) > 50 else "")
                    break

            # 存储简化版数据
            thread_key = self._chat_thread_key(thread_id)
            thread_data = {
                "thread_id": thread_id,
                "preview": preview,
                "updated_at": updated_at,
            }
            self.redis.setex(thread_key, self.ttl_seconds, ormsgpack.packb(thread_data))

            # 添加到线程集合
            self.redis.sadd(self.CHAT_THREADS_KEY, thread_id)
            self.redis.expire(self.CHAT_THREADS_KEY, self.ttl_seconds)

        except Exception as e:
            logger.warning(f"Failed to save chat thread: {e}")

    def save_preview(self, thread_id: str, user_input: str, ns: str = "") -> None:
        """保存用户输入作为预览"""
        try:
            preview = user_input[:50] + ("..." if len(user_input) > 50 else "")
            updated_at = datetime.now().isoformat()

            # 更新简化版数据
            thread_key = self._chat_thread_key(thread_id)
            existing = self.redis.get(thread_key)
            if existing:
                try:
                    thread_data = ormsgpack.unpackb(existing)
                    thread_data["preview"] = preview
                    thread_data["updated_at"] = updated_at
                    self.redis.setex(
                        thread_key, self.ttl_seconds, ormsgpack.packb(thread_data)
                    )
                except Exception:
                    pass
            else:
                thread_data = {
                    "thread_id": thread_id,
                    "preview": preview,
                    "updated_at": updated_at,
                }
                self.redis.setex(
                    thread_key, self.ttl_seconds, ormsgpack.packb(thread_data)
                )

            # 添加到线程集合
            self.redis.sadd(self.CHAT_THREADS_KEY, thread_id)
            self.redis.expire(self.CHAT_THREADS_KEY, self.ttl_seconds)

        except Exception as e:
            logger.warning(f"Failed to save preview: {e}")

    def list(
        self,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> list[CheckpointTuple]:
        """列出指定线程的检查点"""
        if not config:
            return []

        configurable = config["configurable"]
        thread_id = configurable.get("thread_id")
        if not thread_id:
            return []

        key = self._checkpoint_key(thread_id)
        data = self.redis.get(key)
        if not data:
            return []

        typed = ormsgpack.unpackb(data)
        payload = self.serde.loads_typed(typed)
        return [
            CheckpointTuple(
                config=config,
                checkpoint=payload["checkpoint"],
                metadata=payload["metadata"],
            )
        ]

    def delete_thread(self, thread_id: str, ns: str = "") -> None:
        """删除对话"""
        # 删除 LangGraph 检查点
        checkpoint_key = self._checkpoint_key(thread_id, ns)
        metadata_key = self._metadata_key(thread_id, ns)
        self.redis.delete(checkpoint_key)
        self.redis.delete(metadata_key)

        # 删除简化版数据
        thread_key = self._chat_thread_key(thread_id)
        self.redis.delete(thread_key)

        # 从线程集合中移除
        self.redis.srem(self.CHAT_THREADS_KEY, thread_id)

        logger.info(f"Deleted thread: thread_id={thread_id}")

    def list_threads(self, limit: int = 100) -> list[dict]:
        """列出所有对话（带预览、时间）"""
        try:
            threads = []

            # 从简化版数据中获取列表
            thread_ids = self.redis.smembers(self.CHAT_THREADS_KEY)
            if not thread_ids:
                return []

            for thread_id_bytes in thread_ids:
                thread_id = (
                    thread_id_bytes.decode()
                    if isinstance(thread_id_bytes, bytes)
                    else thread_id_bytes
                )
                thread_key = self._chat_thread_key(thread_id)
                data = self.redis.get(thread_key)

                if data:
                    try:
                        thread_data = ormsgpack.unpackb(data)
                        threads.append(
                            {
                                "thread_id": thread_data.get("thread_id", thread_id),
                                "preview": thread_data.get("preview", "新对话"),
                                "updated_at": thread_data.get("updated_at"),
                            }
                        )
                    except Exception as e:
                        logger.debug(f"Failed to parse thread data: {e}")
                        threads.append(
                            {
                                "thread_id": thread_id,
                                "preview": "新对话",
                                "updated_at": None,
                            }
                        )

                if len(threads) >= limit:
                    break

            # 按更新时间倒序
            threads.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
            return threads

        except Exception as e:
            logger.error(f"Failed to list threads: {e}")
            return []

    def thread_exists(self, thread_id: str, ns: str = "") -> bool:
        """检查对话是否存在"""
        return self.redis.sismember(self.CHAT_THREADS_KEY, thread_id)

    def get_or_create_thread_id(self, user_key: str | None = None) -> str:
        """获取或创建新的线程ID"""
        import uuid

        return user_key or f"thread_{uuid.uuid4().hex[:16]}"

    def put_writes(
        self,
        config: RunnableConfig,
        writes: list[tuple[str, Any]],
        task_id: str,
    ) -> None:
        """保存写入（用于中断恢复）"""
        configurable = config["configurable"]
        thread_id = configurable["thread_id"]
        ns = configurable.get("checkpoint_ns", "")

        key = f"writes:{ns}:{thread_id}:{task_id}"
        typed = self.serde.dumps_typed(writes)
        self.redis.setex(key, self.ttl_seconds, ormsgpack.packb(typed))
        logger.debug(f"Writes saved: thread_id={thread_id}, task_id={task_id}")
