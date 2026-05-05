"""
FlowMind 智能流程设计服务 - LLM 客户端

本模块提供 LLM 服务调用能力，封装模型调用接口（纯基础设施层，属于适配器层）。
"""

import json
import time
from typing import Any

from app.adapters.base.errors import ModelError
from app.adapters.factory import ModelFactory
from app.adapters.model_manager import ModelManager
from app.domain.schemas import SchemaRegistry, build_json_schema
from app.infra.logger import logger


class LLMClient:
    """LLM 客户端 - 纯基础设施，提供 LLM 调用能力"""

    DEFAULT_PARAMS = {
        "temperature": 0.7,
        "max_tokens": 2000,
        "top_p": 0.9,
    }

    # 任务级温度配置
    TASK_TEMPERATURE_CONFIG = {
        "intent_recognition": {"temperature": 0.0},          # 意图识别：确定性输出
        "category_classification": {"temperature": 0.1},      # 分类生成：低温度
        "flow_design": {"temperature": 0.2},                  # 流程设计：低温度
        "flow_modify": {"temperature": 0.2},                 # 流程修改：低温度
        "form_generation": {"temperature": 0.2},              # 表单生成：低温度
        "general": {"temperature": 0.7},                      # 闲聊：保持较高温度
    }

    # 重试配置
    RETRY_CONFIG = {
        "max_attempts": 3,
        "base_delay": 1.0,  # 秒
        "max_delay": 3.0,   # 秒
    }

    def get_task_temperature(self, task_name: str) -> float:
        """获取任务对应的温度参数"""
        return self.TASK_TEMPERATURE_CONFIG.get(task_name, self.DEFAULT_PARAMS)["temperature"]

    def _call_with_retry(
        self,
        call_fn: callable,
        operation_name: str,
    ) -> Any:
        """带重试的通用调用辅助函数

        Args:
            call_fn: 要执行的调用函数（无参数或返回结果）
            operation_name: 操作名称（用于日志）

        Returns:
            调用结果或 None
        """
        last_error = None
        for attempt in range(self.RETRY_CONFIG["max_attempts"]):
            try:
                result = call_fn()
                if result:
                    return result
            except Exception as e:
                last_error = e
                logger.debug(
                    f"LLM {operation_name}失败（第{attempt + 1}/{self.RETRY_CONFIG['max_attempts']}次）：{e!s}"
                )

            # 最后一次不需要等待
            if attempt < self.RETRY_CONFIG["max_attempts"] - 1:
                delay = min(
                    self.RETRY_CONFIG["base_delay"] * (2 ** attempt),
                    self.RETRY_CONFIG["max_delay"],
                )
                logger.debug(f"{delay}秒后重试...")
                time.sleep(delay)

        logger.error(
            f"LLM {operation_name}重试{self.RETRY_CONFIG['max_attempts']}次后仍失败：{last_error!s}"
        )
        return None

    def generate_with_retry(
        self,
        prompt: str,
        adapter_name: str | None = None,
        use_fallback: bool | None = None,
        task_name: str | None = None,
        **kwargs
    ) -> str | None:
        """带重试的LLM生成方法，失败时自动重试"""
        return self._call_with_retry(
            lambda: self.generate(
                prompt,
                adapter_name=adapter_name,
                use_fallback=use_fallback,
                task_name=task_name,
                **kwargs
            ),
            operation_name="调用",
        )

    def generate_messages(
        self,
        messages: list[dict],
        adapter_name: str | None = None,
        use_fallback: bool | None = None,
        task_name: str | None = None,
        **kwargs,
    ) -> str | None:
        """使用 messages 数组生成文本（多轮对话格式）

        Args:
            messages: 对话消息列表 [{"role": "user/assistant/system", "content": "..."}]
            adapter_name: 请求级覆盖的适配器名称
            use_fallback: 请求级覆盖的降级开关
            task_name: 任务名称，用于获取对应的温度配置
            **kwargs: 其他参数

        Returns:
            生成的文本或 None
        """
        try:
            manager = self._ensure_manager()
            effective_params = {**self.DEFAULT_PARAMS}
            if task_name and task_name in self.TASK_TEMPERATURE_CONFIG:
                effective_params.update(self.TASK_TEMPERATURE_CONFIG[task_name])
            effective_params.update(kwargs)

            effective_adapter = adapter_name or self._adapter_name
            effective_fallback = use_fallback if use_fallback is not None else self._use_fallback
            response = manager.generate_with_messages(
                messages,
                adapter_name=effective_adapter,
                fallback_enabled=effective_fallback,
                **effective_params,
            )
            return response.content if response else None
        except ModelError as e:
            logger.error(f"LLM 模型调用失败：{e.message}")
            return None
        except Exception as e:
            logger.error(f"LLM 请求失败（未预期）：{e}", exc_info=True)
            return None

    def generate_json_with_retry(
        self,
        prompt: str,
        adapter_name: str | None = None,
        use_fallback: bool | None = None,
        schema_name: str | None = None,
        task_name: str | None = None,
        **kwargs
    ) -> dict[str, Any] | None:
        """带重试的JSON生成方法，失败时自动重试"""
        return self._call_with_retry(
            lambda: self.generate_json(
                prompt,
                adapter_name=adapter_name,
                use_fallback=use_fallback,
                schema_name=schema_name,
                task_name=task_name,
                **kwargs
            ),
            operation_name="JSON生成",
        )

    def __init__(
        self,
        adapter_name: str | None = None,
        use_fallback: bool = True,
        manager: ModelManager | None = None,
    ):
        """初始化 LLM 客户端

        Args:
            adapter_name: 指定使用的适配器名称
            use_fallback: 是否启用降级策略
            manager: 传入的 ModelManager 实例，用于解耦依赖
        """
        self._adapter_name = adapter_name
        self._use_fallback = use_fallback
        self._manager = manager

    def _ensure_manager(self) -> ModelManager:
        """确保管理器已初始化"""
        if self._manager is None:
            ModelFactory.initialize()
            self._manager = ModelFactory.get_model_manager()
        return self._manager

    def generate(
        self,
        prompt: str,
        adapter_name: str | None = None,
        use_fallback: bool | None = None,
        task_name: str | None = None,
        **kwargs
    ) -> str | None:
        """生成文本

        Args:
            prompt: 提示词
            adapter_name: 请求级覆盖的适配器名称
            use_fallback: 请求级覆盖的降级开关
            task_name: 任务名称，用于获取对应的温度配置
            **kwargs: 其他参数

        Returns:
            生成的文本或 None
        """
        try:
            manager = self._ensure_manager()
            # 合并参数：默认参数 -> 任务级参数 -> 传入参数
            effective_params = {**self.DEFAULT_PARAMS}
            if task_name and task_name in self.TASK_TEMPERATURE_CONFIG:
                effective_params.update(self.TASK_TEMPERATURE_CONFIG[task_name])
            effective_params.update(kwargs)

            # 请求级参数 > 实例级默认值
            effective_adapter = adapter_name or self._adapter_name
            effective_fallback = use_fallback if use_fallback is not None else self._use_fallback
            response = manager.generate(
                prompt,
                adapter_name=effective_adapter,
                fallback_enabled=effective_fallback,
                **effective_params,
            )
            return response.content if response else None
        except ModelError as e:
            logger.error(f"LLM 模型调用失败：{e.message}")
            return None
        except Exception as e:
            logger.error(f"LLM 请求失败（未预期）：{e}", exc_info=True)
            return None

    def generate_json(
        self,
        prompt: str,
        adapter_name: str | None = None,
        use_fallback: bool | None = None,
        schema_name: str | None = None,
        task_name: str | None = None,
        **kwargs
    ) -> dict[str, Any] | None:
        """生成 JSON 格式文本（使用原生 JSON Schema）

        Args:
            prompt: 提示词
            adapter_name: 请求级覆盖的适配器名称
            use_fallback: 请求级覆盖的降级开关
            schema_name: JSON Schema 名称（从 SchemaRegistry 获取）
            task_name: 任务名称，用于获取对应的温度配置
            **kwargs: 其他参数

        Returns:
            解析后的 JSON 字典或 None
        """
        # 如果指定了 schema_name，构建 response_format
        if schema_name:
            schema = SchemaRegistry.get(schema_name)
            if schema:
                response_format = build_json_schema(
                    schema=schema,
                    name=schema_name,
                    strict=True,
                )
                kwargs["response_format"] = response_format

        text = self.generate(
            prompt,
            adapter_name=adapter_name,
            use_fallback=use_fallback,
            task_name=task_name,
            **kwargs
        )
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败：{e}")
            return None

    def get_current_adapter(self) -> str | None:
        """获取当前使用的适配器"""
        return self._ensure_manager().get_current_adapter()

    def get_available_adapters(self) -> dict[str, dict[str, Any]]:
        """获取可用适配器信息"""
        return self._ensure_manager().get_available_adapters_info()

    def with_overrides(
        self,
        adapter_name: str | None = None,
        use_fallback: bool | None = None,
    ) -> "LLMClient":
        """创建参数覆盖的服务包装器

        用于在不创建新实例的情况下，为单次请求覆盖模型选择参数。
        包装器共享底层 manager，但使用请求级的 adapter_name 和 use_fallback。

        Args:
            adapter_name: 请求级覆盖的适配器名称
            use_fallback: 请求级覆盖的降级开关

        Returns:
            新的 LLMClient 包装器实例
        """
        return LLMClient(
            adapter_name=adapter_name,
            use_fallback=use_fallback,
            manager=self._ensure_manager(),  # 共享 manager
        )


# 全局服务实例（使用函数避免模块加载时实例化）
_llm_client_instance: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """获取 LLMClient 单例（延迟初始化）"""
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient()
    return _llm_client_instance
