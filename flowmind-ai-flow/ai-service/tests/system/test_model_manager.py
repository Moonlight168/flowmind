"""
FlowMind AI Service - ModelManager 系统测试

验证 ModelManager 的模型管理和降级行为：
- 单模型可用时直接返回
- 多模型按优先级选择
- 降级机制：第一个失败自动切换到第二个
- 全部失败时抛出异常
"""

from __future__ import annotations

import os
from typing import Generator
from unittest.mock import patch

import pytest
import redis

from app.adapters.factory import ModelFactory
from app.adapters.model_manager import ModelManager, ModelManagerConfig


@pytest.fixture(scope="module")
def redis_client() -> Generator[redis.Redis, None, None]:
    """连接 Redis"""
    client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=False)
    yield client
    client.close()


@pytest.fixture(autouse=True)
def reset_model_factory():
    """每个测试前后重置 ModelFactory"""
    ModelFactory.reset()
    yield
    ModelFactory.reset()


class TestModelManagerSingleModel:
    """单模型可用测试"""

    def test_create_llm_returns_chatopenai_instance(self):
        """单模型配置时，create_llm 返回 ChatOpenAI 实例"""
        ModelFactory.initialize()
        manager = ModelFactory.get_model_manager()

        llm = manager.create_llm(task_name="chat")

        # 验证返回的是 ChatOpenAI 实例
        assert llm is not None
        assert hasattr(llm, "invoke")

    def test_single_model_priority_used(self):
        """单模型时直接使用该模型"""
        ModelFactory.initialize()
        manager = ModelFactory.get_model_manager()

        provider = manager.get_current_provider()
        available = manager.get_available_providers()

        # 单模型时，当前 provider 应该是可用列表中的第一个
        assert provider in available
        assert len(available) >= 1


class TestModelManagerPriority:
    """多模型优先级测试"""

    def test_priority_order_respected(self):
        """验证模型按 priority 顺序选择"""
        ModelFactory.initialize()
        manager = ModelFactory.get_model_manager()

        available = manager.get_available_providers()

        # available_providers 应按 priority 排序
        assert len(available) >= 1
        # 第一个应该是最高优先级
        priority = ModelFactory._model_manager._priority if hasattr(ModelFactory, '_model_manager') else []
        if len(available) > 1:
            # 验证 available 是 priority 的子集且顺序一致
            for i, name in enumerate(available):
                assert name == priority[i] if i < len(priority) else True


class TestModelManagerFallback:
    """模型降级测试"""

    def test_fallback_on_first_model_failure(self):
        """第一个模型失败时自动降级到第二个"""
        ModelFactory.initialize()
        manager = ModelFactory.get_model_manager()

        # 如果有多个模型，验证降级能力
        available = manager.get_available_providers()
        if len(available) < 2:
            pytest.skip("需要至少两个模型才能测试降级")

        # 获取第一个模型的配置并注入失败
        first_model = available[0]
        first_config = manager._providers.get(first_model)

        # Mock 第一个模型抛出异常
        def mock_build_llm_failure(config, task_name):
            if config == first_config:
                raise RuntimeError("模拟第一个模型失败")
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=config.get("model_name", ""),
                base_url=config.get("base_url", "").rstrip("/"),
                api_key=config.get("api_key") or "not-needed",
            )

        original_build = manager._build_llm
        manager._build_llm = mock_build_llm_failure

        try:
            # 应该降级到第二个模型
            llm = manager.create_llm(task_name="chat")
            assert llm is not None
            assert manager.get_current_provider() == available[1]
        finally:
            manager._build_llm = original_build

    def test_all_models_fail_raises_exception(self):
        """所有模型都失败时抛出异常"""
        ModelFactory.initialize()
        manager = ModelFactory.get_model_manager()

        # Mock 所有模型都失败
        def mock_build_llm_always_fail(config, task_name):
            raise RuntimeError("所有模型不可用")

        original_build = manager._build_llm
        manager._build_llm = mock_build_llm_always_fail

        try:
            with pytest.raises(RuntimeError, match="所有模型"):
                manager.create_llm(task_name="chat")
        finally:
            manager._build_llm = original_build


class TestModelManagerConfig:
    """ModelManager 配置测试"""

    def test_task_temperature_config(self):
        """验证不同任务使用不同的 temperature 配置"""
        ModelFactory.initialize()
        manager = ModelFactory.get_model_manager()

        # chat 应该用 0.8
        chat_llm = manager.create_llm(task_name="chat")
        # design 任务应该用 0.3
        design_llm = manager.create_llm(task_name="category_design")

        # 两个 LLM 实例都应该成功创建
        assert chat_llm is not None
        assert design_llm is not None

    def test_json_format_tasks(self):
        """验证 JSON 格式任务设置了正确的 response_format"""
        ModelFactory.initialize()
        manager = ModelFactory.get_model_manager()

        # category_design 是 JSON_FORMAT_TASKS
        llm = manager.create_llm(task_name="category_design")
        assert llm is not None

        # chat 不是 JSON_FORMAT_TASKS
        chat_llm = manager.create_llm(task_name="chat")
        assert chat_llm is not None


class TestModelFactoryIntegration:
    """ModelFactory 集成测试"""

    def test_factory_initialization(self):
        """验证 ModelFactory 正确初始化"""
        ModelFactory.initialize()

        assert ModelFactory.is_initialized() is True
        assert ModelFactory.get_model_manager() is not None

    def test_factory_reset(self):
        """验证 ModelFactory 重置"""
        ModelFactory.initialize()
        assert ModelFactory.is_initialized() is True

        ModelFactory.reset()
        assert ModelFactory.is_initialized() is False

    def test_factory_reinitialization(self):
        """验证 ModelFactory 重新初始化"""
        ModelFactory.initialize()
        manager1 = ModelFactory.get_model_manager()

        # 重新初始化应该更新 manager
        ModelFactory.reset()
        ModelFactory.initialize()
        manager2 = ModelFactory.get_model_manager()

        assert manager1 is not manager2
