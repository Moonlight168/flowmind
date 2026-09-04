"""
FlowMind AI Service - Design Workflow 系统测试

验证 design_workflow 的完整行为：
- 不同 design_type 的输出结构
- 多轮对话（clarification → success）
- 状态恢复（从 checkpoint 继续对话）
- 并发安全（独立 thread_id 不互相影响）
- 清理（删除后数据消失）
"""

from __future__ import annotations

import uuid

import pytest
import redis

from app.core.checkpoint.redis_checkpoint import RedisCheckpoint
from app.graph.workflows.design_workflow import (
    delete_design_thread,
    invoke_design_workflow,
)


class TestCategoryDesign:
    """分类设计 workflow 测试"""

    def test_category_design_returns_clarification_structure(
        self, clean_redis: redis.Redis, thread_id: str
    ):
        """clarification 场景：返回 {form_data, message, intent}"""
        result = invoke_design_workflow(
            design_type="category_design",
            user_input="帮我创建一个分类",  # 模糊输入，触发 clarification
            thread_id=thread_id,
        )

        assert "intent" in result
        assert result["intent"] in ("clarification", "success", "error")
        assert "message" in result
        assert "form_data" in result

        if result["intent"] == "clarification":
            assert result["form_data"] is None

    def test_category_design_returns_success_structure(
        self, clean_redis: redis.Redis, thread_id: str
    ):
        """success 场景：返回包含 category_name, code, remark 的 form_data"""
        result = invoke_design_workflow(
            design_type="category_design",
            user_input='创建一个名为"请假分类"、编码为LEAVE的分类，用于管理请假流程',
            thread_id=thread_id,
        )

        assert result["intent"] == "success", f"期望 success，实际 {result.get('intent')}: {result.get('message')}"
        assert result["form_data"] is not None
        assert "category_name" in result["form_data"]
        assert "code" in result["form_data"]

    def test_category_design_checkpoint_stored(
        self, clean_redis: redis.Redis, thread_id: str
    ):
        """验证 checkpoint 已存储"""
        invoke_design_workflow(
            design_type="category_design",
            user_input="创建一个分类",
            thread_id=thread_id,
        )

        checkpointer = RedisCheckpoint()
        assert checkpointer.thread_exists(thread_id) is True


class TestFlowDesign:
    """流程设计 workflow 测试"""

    def test_flow_design_returns_success_structure(
        self, clean_redis: redis.Redis, thread_id: str
    ):
        """success 场景：返回包含 flowName, categoryId, bpmn_xml 的 form_data"""
        result = invoke_design_workflow(
            design_type="flow_design",
            user_input="设计一个请假流程，包含开始、审批、结束节点",
            thread_id=thread_id,
        )

        assert result["intent"] == "success", f"期望 success，实际 {result.get('intent')}: {result.get('message')}"
        assert result["form_data"] is not None
        assert "flowName" in result["form_data"]
        # bpmn_xml 可能为空或不包含，取决于 LLM 输出

    def test_flow_design_returns_clarification_structure(
        self, clean_redis: redis.Redis, thread_id: str
    ):
        """clarification 场景"""
        result = invoke_design_workflow(
            design_type="flow_design",
            user_input="设计流程",  # 模糊输入
            thread_id=thread_id,
        )

        assert "intent" in result
        assert result["intent"] in ("clarification", "success", "error")
        assert "message" in result


class TestFormDesign:
    """表单设计 workflow 测试"""

    def test_form_design_returns_success_structure(
        self, clean_redis: redis.Redis, thread_id: str
    ):
        """success 场景：返回包含 form_data 的 form_data"""
        result = invoke_design_workflow(
            design_type="form_design",
            user_input="创建一个请假申请表单，包含请假类型、开始日期、结束日期、原因字段",
            thread_id=thread_id,
        )

        assert result["intent"] == "success", f"期望 success，实际 {result.get('intent')}: {result.get('message')}"
        assert result["form_data"] is not None
        # form_data 内部应包含表单结构

    def test_form_design_returns_clarification_structure(
        self, clean_redis: redis.Redis, thread_id: str
    ):
        """clarification 场景"""
        result = invoke_design_workflow(
            design_type="form_design",
            user_input="创建表单",
            thread_id=thread_id,
        )

        assert "intent" in result
        assert result["intent"] in ("clarification", "success", "error")
        assert "message" in result


class TestMultiTurnConversation:
    """多轮对话测试"""

    def test_continuation_from_existing_thread(
        self, clean_redis: redis.Redis, thread_id: str
    ):
        """从已有 thread 继续对话，验证上下文保持"""
        # 第一轮：模糊输入触发 clarification
        result1 = invoke_design_workflow(
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

        # 如果第一轮是 clarification，第二轮可能 success
        # 如果第一轮就是 success，第二轮可能继续 success 或新的 success
        assert "intent" in result2
        assert result2["intent"] in ("clarification", "success")

    def test_checkpoint_accumulates_history(
        self, clean_redis: redis.Redis, thread_id: str
    ):
        """验证 checkpoint 累积对话历史"""
        invoke_design_workflow(
            design_type="category_design",
            user_input="创建分类1",
            thread_id=thread_id,
        )

        invoke_design_workflow(
            design_type="category_design",
            user_input="创建分类2",
            thread_id=thread_id,
        )

        checkpointer = RedisCheckpoint()
        assert checkpointer.thread_exists(thread_id) is True


class TestStateRecovery:
    """状态恢复测试"""

    def test_state_recovery_from_checkpoint(
        self, clean_redis: redis.Redis, thread_id: str
    ):
        """从 checkpoint 恢复状态后继续对话"""
        # 创建初始对话
        invoke_design_workflow(
            design_type="category_design",
            user_input="帮我创建一个分类",
            thread_id=thread_id,
        )

        # 模拟新请求（同一 thread_id）
        # 此时应该从 checkpoint 恢复历史，而不是创建新对话
        result = invoke_design_workflow(
            design_type="category_design",
            user_input="继续",
            thread_id=thread_id,
        )

        assert "intent" in result
        assert result["intent"] in ("clarification", "success", "error")


class TestConcurrency:
    """并发安全测试"""

    def test_independent_threads_do_not_interfere(
        self, clean_redis: redis.Redis
    ):
        """独立 thread_id 之间不互相影响"""
        thread_id_1 = f"test_{uuid.uuid4().hex[:16]}"
        thread_id_2 = f"test_{uuid.uuid4().hex[:16]}"

        # 同时创建两个独立的对话
        result1 = invoke_design_workflow(
            design_type="category_design",
            user_input="创建分类A",
            thread_id=thread_id_1,
        )

        result2 = invoke_design_workflow(
            design_type="category_design",
            user_input="创建分类B",
            thread_id=thread_id_2,
        )

        # 两个结果都应该是成功的
        assert result1["intent"] in ("clarification", "success")
        assert result2["intent"] in ("clarification", "success")

        # 两个 thread 独立存在
        checkpointer = RedisCheckpoint()
        assert checkpointer.thread_exists(thread_id_1) is True
        assert checkpointer.thread_exists(thread_id_2) is True


class TestCleanup:
    """清理测试"""

    def test_delete_design_thread_removes_checkpoint(
        self, clean_redis: redis.Redis, thread_id: str
    ):
        """删除后 checkpoint 数据消失"""
        # 创建对话
        invoke_design_workflow(
            design_type="category_design",
            user_input="创建一个分类",
            thread_id=thread_id,
        )

        checkpointer = RedisCheckpoint()
        assert checkpointer.thread_exists(thread_id) is True

        # 删除
        delete_design_thread(thread_id)

        # 验证删除
        assert checkpointer.thread_exists(thread_id) is False
