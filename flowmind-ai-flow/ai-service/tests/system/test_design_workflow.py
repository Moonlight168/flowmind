"""
FlowMind AI Service - Design Workflow 系统测试

使用真实模型与 Redis，验证集成测试（mock LLM）无法覆盖的链路：
- SSE 接口端到端（真实模型 + Redis checkpoint）
- Redis checkpoint 持久化
- 多轮对话续接
- 会话删除清理

各 design_type 的输出结构、review 重试与死循环检测等确定性逻辑
由 tests/integration/test_design_chain.py 覆盖，此处不重复。
"""

from __future__ import annotations

import json

import redis
from fastapi.testclient import TestClient

from app.api.design import _design_thread_id
from app.core.auth import TokenUser
from app.graph.design_graph import (
    delete_design_thread,
    invoke_design_workflow,
)
from app.infra.checkpoint.redis import RedisCheckpoint

# 与 conftest.auth_headers 注入的网关身份保持一致，用于复算会话隔离键
GATEWAY_USER = TokenUser(user_id=1, username="system-test", user_key="system-test")


def _checkpoint_exists(thread_id: str) -> bool:
    """当前实现只把 chat:* 前缀线程写入简化列表，设计线程需按 checkpoint 键判断。"""
    checkpointer = RedisCheckpoint()
    config = {"configurable": {"thread_id": thread_id}}
    return checkpointer.get_tuple(config) is not None


def _read_sse_events(
    client: TestClient, payload: dict, headers: dict[str, str]
) -> tuple[int, str, list[dict]]:
    with client.stream(
        "POST", "/design/category", json=payload, headers=headers
    ) as response:
        events = [
            json.loads(line.removeprefix("data: "))
            for line in response.iter_lines()
            if line.startswith("data: ")
        ]
        return response.status_code, response.headers["content-type"], events


class TestCategoryDesign:
    """分类设计 workflow 测试"""

    def test_category_design_checkpoint_stored(
        self, clean_redis: redis.Redis, thread_id: str
    ):
        """验证 checkpoint 已存储"""
        invoke_design_workflow(
            design_type="category_design",
            user_input="创建一个分类",
            thread_id=thread_id,
        )

        assert _checkpoint_exists(thread_id) is True

    def test_category_design_sse_uses_real_model_and_redis(
        self,
        clean_redis: redis.Redis,
        client: TestClient,
        auth_headers: dict[str, str],
        thread_id: str,
    ):
        """SSE 接口应通过真实模型与 Redis 返回进度及最终结果。"""
        payload = {
            "user_input": "创建费用报销分类，编码 EXPENSE",
            "thread_id": thread_id,
        }

        api_thread_id = _design_thread_id(
            "category_design", GATEWAY_USER, conversation_id=thread_id
        )
        try:
            status, content_type, events = _read_sse_events(
                client, payload, auth_headers
            )
            assert status == 200
            assert content_type.startswith("text/event-stream")
            assert any(event.get("type") == "progress" for event in events)
            done = next(event for event in events if event.get("type") == "done")
            assert done["intent"] == "success"
            assert done["form_data"]["code"].upper() == "EXPENSE"
            assert _checkpoint_exists(api_thread_id) is True
        finally:
            delete_design_thread(api_thread_id)


class TestMultiTurnConversation:
    """多轮对话测试"""

    def test_continuation_from_existing_thread(
        self, clean_redis: redis.Redis, thread_id: str
    ):
        """从已有 thread 继续对话，验证上下文保持"""
        # 第一轮：模糊输入触发 clarification
        invoke_design_workflow(
            design_type="category_design",
            user_input="帮我创建一个分类",
            thread_id=thread_id,
        )

        # 第二轮：补充具体信息
        result2 = invoke_design_workflow(
            design_type="category_design",
            user_input='分类名称是"采购申请"，编码是PURCHASE',
            thread_id=thread_id,
        )

        # 第一轮可能是 clarification；第二轮可能成功或继续追问
        assert "intent" in result2
        assert result2["intent"] in ("clarification", "success")


class TestCleanup:
    """清理测试"""

    def test_delete_design_thread_removes_checkpoint(
        self, clean_redis: redis.Redis, thread_id: str
    ):
        """删除后 checkpoint 数据消失"""
        invoke_design_workflow(
            design_type="category_design",
            user_input="创建一个分类",
            thread_id=thread_id,
        )

        assert _checkpoint_exists(thread_id) is True

        delete_design_thread(thread_id)

        assert _checkpoint_exists(thread_id) is False
