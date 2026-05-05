"""
FlowMind 智能流程设计服务 - 模型工厂

本模块实现模型适配器的工厂类，根据配置创建适配器实例并统一管理。

架构说明：
- 默认使用 OpenAICompatibleAdapter（统一 OpenAI 兼容格式）
- 保留专用适配器（vllm_adapter.py, qwen_adapter.py, doubao_adapter.py）作为定制化扩展点
- 当某个模型需要特殊处理时，可使用对应的专用适配器
"""

import threading
from typing import Any

from app.adapters.base import ModelAdapter, ModelConfig
from app.adapters.llm.openai_adapter import OpenAICompatibleAdapter
from app.adapters.model_manager import ModelManager, ModelManagerConfig
from app.config.settings import settings
from app.infra.logger import logger


class ModelFactory:
    """模型工厂

    使用类方法管理模型适配器的创建和生命周期。
    """

    _adapters: dict[str, ModelAdapter] = {}
    _model_manager: ModelManager | None = None
    _initialized: bool = False
    _lock = threading.RLock()

    @classmethod
    def create_adapter(cls, name: str, config: dict[str, Any]) -> ModelAdapter:
        """创建适配器实例

        Args:
            name: 适配器名称（如 vllm, qwen, doubao）
            config: 适配器配置

        Returns:
            模型适配器实例
        """
        model_config = ModelConfig(
            model_name=config.get("model_name", ""),
            base_url=config.get("base_url", ""),
            api_key=config.get("api_key"),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 2000),
            top_p=config.get("top_p", 0.9),
            timeout=config.get("timeout", 60),
        )

        return OpenAICompatibleAdapter(name, model_config)

    @classmethod
    def initialize(cls) -> None:
        """初始化模型工厂（线程安全）"""
        with cls._lock:
            if cls._initialized:
                logger.debug("[ModelFactory] 已初始化，跳过重复初始化")
                return

            providers = settings.get_model_providers()
            priority = settings.get_model_priority()
            fallback_config = settings.get_fallback_config()

            logger.info(f"[ModelFactory] 模型优先级配置：{priority}")
            logger.info(f"[ModelFactory] 可用模型提供商：{list(providers.keys())}")

            # 按照优先级顺序加载适配器
            sorted_names = sorted(
                providers.keys(),
                key=lambda x: priority.index(x) if x in priority else len(priority),
            )

            logger.info(f"[ModelFactory] 按优先级排序后的加载顺序：{sorted_names}")

            for name in sorted_names:
                config = providers[name]
                try:
                    adapter = cls.create_adapter(name, config)
                    cls._adapters[name] = adapter
                    logger.info(f"[ModelFactory] 已加载模型适配器：{name}")
                # 捕获适配器创建异常，记录错误但继续加载其他适配器
                except Exception as e:
                    logger.error(f"[ModelFactory] 加载模型适配器失败 [{name}]: {e}")

            valid_priority = [p for p in priority if p in cls._adapters]
            if not valid_priority and cls._adapters:
                valid_priority = list(cls._adapters.keys())

            logger.info(f"[ModelFactory] 有效优先级列表：{valid_priority}")

            cls._model_manager = ModelManager(
                adapters=cls._adapters,
                priority=valid_priority,
                config=ModelManagerConfig(
                    enabled=fallback_config.get("enabled", True),
                    max_retries=fallback_config.get("max_retries", 3),
                    retry_interval=fallback_config.get("retry_interval", 1.0),
                ),
            )

            cls._initialized = True
            logger.info(
                f"[ModelFactory] 初始化完成，已加载 {len(cls._adapters)} 个适配器，"
                f"优先级顺序：{valid_priority}"
            )

    @classmethod
    def get_adapter(cls, name: str) -> ModelAdapter | None:
        """获取指定适配器"""
        if not cls._initialized:
            cls.initialize()
        return cls._adapters.get(name)

    @classmethod
    def get_all_adapters(cls) -> dict[str, ModelAdapter]:
        """获取所有适配器的副本"""
        if not cls._initialized:
            cls.initialize()
        return cls._adapters.copy()

    @classmethod
    def get_model_manager(cls) -> ModelManager:
        """获取模型管理器"""
        if not cls._initialized:
            cls.initialize()

        if cls._model_manager is None:
            raise RuntimeError("模型管理器未初始化")

        return cls._model_manager

    @classmethod
    def generate(
        cls,
        prompt: str,
        adapter_name: str | None = None,
        fallback_enabled: bool = True,
        **kwargs,
    ) -> Any:
        """生成文本"""
        if not cls._initialized:
            cls.initialize()

        return cls._model_manager.generate(
            prompt,
            adapter_name=adapter_name,
            fallback_enabled=fallback_enabled,
            **kwargs,
        )

    @classmethod
    def generate_with_messages(
        cls,
        messages: list[dict[str, str]],
        adapter_name: str | None = None,
        fallback_enabled: bool = True,
        **kwargs,
    ) -> Any:
        """使用消息列表生成文本"""
        if not cls._initialized:
            cls.initialize()

        return cls._model_manager.generate_with_messages(
            messages,
            adapter_name=adapter_name,
            fallback_enabled=fallback_enabled,
            **kwargs,
        )

    @classmethod
    def add_adapter(cls, name: str, config: dict[str, Any]) -> None:
        """添加适配器"""
        with cls._lock:
            if not cls._initialized:
                cls.initialize()

            adapter = cls.create_adapter(name, config)
            cls._adapters[name] = adapter
            cls._model_manager.add_adapter(name, adapter)
            logger.info(f"已添加模型适配器：{name}")

    @classmethod
    def remove_adapter(cls, name: str) -> bool:
        """移除适配器"""
        with cls._lock:
            if not cls._initialized:
                cls.initialize()

            if name not in cls._adapters:
                return False

            del cls._adapters[name]
            cls._model_manager.remove_adapter(name)
            logger.info(f"已移除模型适配器：{name}")
            return True

    @classmethod
    def is_initialized(cls) -> bool:
        """是否已初始化"""
        return cls._initialized

    @classmethod
    def update_priority(cls, priority: list[str]) -> None:
        """更新模型优先级

        Args:
            priority: 新的优先级列表
        """
        if not cls._initialized:
            cls.initialize()
        if cls._model_manager:
            cls._model_manager.update_priority(priority)

    @classmethod
    def update_fallback_config(
        cls,
        enabled: bool | None = None,
        max_retries: int | None = None,
        retry_interval: float | None = None,
    ) -> None:
        """更新降级配置

        Args:
            enabled: 是否启用降级
            max_retries: 最大重试次数
            retry_interval: 重试间隔
        """
        if not cls._initialized:
            cls.initialize()
        if cls._model_manager:
            cls._model_manager.update_config(
                enabled=enabled,
                max_retries=max_retries,
                retry_interval=retry_interval,
            )

    @classmethod
    def reset(cls) -> None:
        """重置工厂状态"""
        with cls._lock:
            cls._adapters.clear()
            cls._model_manager = None
            cls._initialized = False

            logger.info("ModelFactory 已重置")
