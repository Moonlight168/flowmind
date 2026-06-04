"""
FlowMind 智能流程设计服务 - 模型工厂

本模块实现模型管理器的工厂类，根据配置创建 LangChain ChatOpenAI 实例并统一管理。
主流程使用 LangChain create_react_agent 或直接调用 ChatOpenAI，ModelManager 负责多模型优先级降级。
"""

import threading

from app.adapters.model_manager import ModelManager, ModelManagerConfig
from app.config.settings import settings
from app.infra.logger import logger


class ModelFactory:
    """模型工厂

    使用类方法管理模型创建和生命周期。
    主流程使用 LangChain，ModelManager 负责多模型优先级降级。
    """

    _model_manager: ModelManager | None = None
    _initialized: bool = False
    _lock = threading.RLock()

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

            valid_priority = [p for p in priority if p in providers]
            if not valid_priority:
                valid_priority = list(providers.keys())

            logger.info(f"[ModelFactory] 有效优先级列表：{valid_priority}")

            cls._model_manager = ModelManager(
                providers=providers,
                priority=valid_priority,
                config=ModelManagerConfig(
                    enabled=fallback_config.get("enabled", True),
                    max_retries=fallback_config.get("max_retries", 3),
                    retry_interval=fallback_config.get("retry_interval", 1.0),
                ),
            )

            cls._initialized = True
            logger.info(
                f"[ModelFactory] 初始化完成，提供商数量：{len(providers)}，"
                f"优先级顺序：{valid_priority}"
            )

    @classmethod
    def get_model_manager(cls) -> ModelManager:
        """获取模型管理器"""
        if not cls._initialized:
            cls.initialize()
        if cls._model_manager is None:
            raise RuntimeError("模型管理器未初始化")
        return cls._model_manager

    @classmethod
    def is_initialized(cls) -> bool:
        """是否已初始化"""
        return cls._initialized

    @classmethod
    def reset(cls) -> None:
        """重置工厂状态"""
        with cls._lock:
            cls._model_manager = None
            cls._initialized = False
            logger.info("ModelFactory 已重置")
