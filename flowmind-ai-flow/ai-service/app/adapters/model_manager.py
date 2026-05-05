"""
FlowMind 智能流程设计服务 - 统一的模型管理器

本模块提供统一的模型管理器，整合适配器管理、优先级调度和自动降级功能。
"""

from dataclasses import dataclass
from typing import Any

from app.adapters.base import ModelAdapter, ModelResponse
from app.adapters.base.errors import ModelErrorCode, ModelError
from app.infra.logger import logger


@dataclass
class ModelManagerConfig:
    """模型管理器配置"""

    enabled: bool = True
    max_retries: int = 3
    retry_interval: float = 1.0


class ModelManager:
    """统一的模型管理器

    职责:
    - 适配器统一管理
    - 优先级调度
    - 自动降级 (内置)
    """

    def __init__(
        self,
        adapters: dict[str, ModelAdapter],
        priority: list[str],
        config: ModelManagerConfig | None = None,
    ):
        self._adapters = adapters
        self._priority = priority
        self._config = config or ModelManagerConfig()
        self._current_adapter: str | None = None
        self._last_available_adapters: list[str] = []

    def generate(
        self,
        prompt: str,
        adapter_name: str | None = None,
        fallback_enabled: bool = True,
        **kwargs,
    ) -> ModelResponse:
        """生成文本

        Args:
            prompt: 提示词
            adapter_name: 指定适配器名称
            fallback_enabled: 是否启用降级策略
            **kwargs: 额外参数

        Returns:
            模型响应
        """
        if adapter_name:
            logger.debug(f"[ModelManager] 指定适配器：{adapter_name}")
            return self._generate_with_adapter(adapter_name, False, prompt, **kwargs)

        if fallback_enabled:
            return self._generate_with_fallback(False, prompt, **kwargs)
        else:
            available = self.get_available_adapters()
            if not available:
                raise ModelError(
                    error_type=ModelErrorCode.SERVICE_ERROR,
                    message="没有可用的模型适配器",
                )
            return self._generate_with_adapter(available[0], False, prompt, **kwargs)

    def generate_with_messages(
        self,
        messages: list[dict[str, str]],
        adapter_name: str | None = None,
        fallback_enabled: bool = True,
        **kwargs,
    ) -> ModelResponse:
        """使用消息列表生成文本

        Args:
            messages: 消息列表
            adapter_name: 指定适配器名称
            fallback_enabled: 是否启用降级策略
            **kwargs: 额外参数

        Returns:
            模型响应
        """
        if adapter_name:
            logger.debug(f"[ModelManager] 指定适配器 (messages): {adapter_name}")
            return self._generate_with_adapter(adapter_name, True, messages, **kwargs)

        if fallback_enabled:
            return self._generate_with_fallback(True, messages, **kwargs)
        else:
            available = self.get_available_adapters()
            if not available:
                raise ModelError(
                    error_type=ModelErrorCode.SERVICE_ERROR,
                    message="没有可用的模型适配器",
                )
            return self._generate_with_adapter(available[0], True, messages, **kwargs)

    def get_available_adapters(self) -> list[str]:
        """获取可用适配器列表 (按优先级排序)"""
        return [name for name in self._priority if name in self._adapters]

    def get_available_adapters_info(self) -> dict[str, dict[str, Any]]:
        """获取适配器详细信息"""
        return {
            name: {
                "model_name": adapter.model_name,
                "is_available": True,
            }
            for name, adapter in self._adapters.items()
        }

    def get_current_adapter(self) -> str | None:
        """获取当前使用的适配器"""
        return self._current_adapter

    def add_adapter(self, name: str, adapter: ModelAdapter) -> None:
        """添加适配器"""
        self._adapters[name] = adapter
        if name not in self._priority:
            self._priority.append(name)
        logger.info(f"已添加模型适配器：{name}")

    def remove_adapter(self, name: str) -> bool:
        """移除适配器"""
        if name in self._adapters:
            del self._adapters[name]
            if name in self._priority:
                self._priority.remove(name)
            logger.info(f"已移除模型适配器：{name}")
            return True
        return False

    def update_priority(self, priority: list[str]) -> None:
        """更新模型优先级

        Args:
            priority: 新的优先级列表
        """
        self._priority = priority
        logger.info(f"已更新模型优先级：{priority}")

    def update_config(
        self,
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
        if enabled is not None:
            self._config.enabled = enabled
        if max_retries is not None:
            self._config.max_retries = max_retries
        if retry_interval is not None:
            self._config.retry_interval = retry_interval
        logger.info(f"已更新降级配置：enabled={self._config.enabled}, max_retries={self._config.max_retries}")

    def _generate_with_adapter(
        self,
        adapter_name: str,
        use_messages: bool,
        input_data: Any,
        **kwargs,
    ) -> ModelResponse:
        """使用指定适配器生成
        """
        adapter = self._adapters.get(adapter_name)

        self._current_adapter = adapter_name

        if use_messages:
            return adapter.generate_with_messages(input_data, **kwargs)
        else:
            return adapter.generate(input_data, **kwargs)

    def _generate_with_fallback(
        self,
        use_messages: bool,
        input_data: Any,
        **kwargs,
    ) -> ModelResponse:
        """带降级机制的生成 - 按优先级遍历适配器，直到成功为止
        """
        last_error: ModelError | None = None
        available = self.get_available_adapters()

        if available != self._last_available_adapters:
            logger.debug(f"[ModelManager] 可用适配器：{available}")
            self._last_available_adapters = available.copy()

        for attempt, adapter_name in enumerate(available, 1):
            try:
                adapter = self._adapters[adapter_name]
                self._current_adapter = adapter_name

                if use_messages:
                    response = adapter.generate_with_messages(input_data, **kwargs)
                else:
                    response = adapter.generate(input_data, **kwargs)

                logger.debug(f"[ModelManager] {adapter_name} 调用成功")
                return response

            except ModelError as e:
                last_error = e
                logger.warning(
                    f"[ModelManager] {adapter_name} 调用失败",
                    error_type=e.error_type.value if hasattr(e.error_type, 'value') else str(e.error_type),
                    message=e.message,
                )

                if not e.is_recoverable():
                    logger.error("[ModelManager] 遇到不可恢复错误，终止降级链")
                    raise

                if self._config.enabled:
                    continue
                else:
                    logger.warning("[ModelManager] 降级策略已禁用，终止调用链")
                    raise

        raise last_error or ModelError(
            error_type=ModelErrorCode.SERVICE_ERROR,
            message="所有适配器都不可用",
        )
