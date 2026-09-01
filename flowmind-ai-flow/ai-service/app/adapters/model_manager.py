"""
FlowMind 智能流程设计服务 - 模型管理器

本模块提供统一的模型管理器，实现多模型优先级降级。
"""

import threading
from collections.abc import Collection
from dataclasses import dataclass

from langchain_openai import ChatOpenAI

from app.infra.logger import logger


@dataclass
class ModelManagerConfig:
    """模型管理器配置"""

    enabled: bool = True
    max_retries: int = 3
    retry_interval: float = 1.0


class ModelManager:
    """统一的模型管理器

    职责：多模型优先级降级。设计任务经 create_react_agent（ReAct）+ chat 直接调用，
    均通过本类创建 ChatOpenAI。
    """

    def __init__(
        self,
        providers: dict[str, dict],
        priority: list[str],
        config: ModelManagerConfig | None = None,
    ):
        self._providers = providers
        self._priority = priority
        self._config = config or ModelManagerConfig()
        self._current_provider: str | None = None
        self._llm_cache: dict[tuple[str, str | None], ChatOpenAI] = {}
        self._cache_lock = threading.RLock()

    TASK_TEMPERATURE_CONFIG = {
        "category_design": {"temperature": 0.3},
        "flow_design": {"temperature": 0.3},
        "form_design": {"temperature": 0.3},
        "chat": {"temperature": 0.8},
        "compress": {"temperature": 0.0, "max_tokens": 300},
        "intent": {"temperature": 0.0, "max_tokens": 200},
    }

    def create_llm(
        self,
        task_name: str | None = None,
        structured: bool = False,
        excluded_providers: Collection[str] = (),
    ) -> "ChatOpenAI":
        """创建 ChatOpenAI 实例，失败时自动降级到下一优先级模型

        structured=True 时只选 supports_structured_output 的模型（结构化输出用）。
        """
        llm, _ = self.create_llm_with_provider(
            task_name=task_name,
            structured=structured,
            excluded_providers=excluded_providers,
        )
        return llm

    def create_llm_with_provider(
        self,
        task_name: str | None = None,
        structured: bool = False,
        excluded_providers: Collection[str] = (),
    ) -> tuple["ChatOpenAI", str]:
        """创建模型并返回 provider，供调用失败后跳过故障 provider。"""
        candidates = [
            name
            for name in self.get_available_providers()
            if name not in excluded_providers
        ]
        if structured:
            candidates = [
                name
                for name in candidates
                if self._providers.get(name, {}).get("supports_structured_output", True)
            ]
        last_error: Exception | None = None

        for name in candidates:
            config = self._providers.get(name)
            if not config:
                continue
            try:
                llm = self._get_or_create_llm(name, task_name)
                self._current_provider = name
                return llm, name
            except (ValueError, TypeError, KeyError, AttributeError) as e:
                last_error = e
                logger.warning(f"[ModelManager] 模型 [{name}] 调用失败，尝试降级: {e}")
                continue

        raise last_error or RuntimeError("所有模型都不可用")

    def _get_or_create_llm(self, name: str, task_name: str | None) -> "ChatOpenAI":
        """按 (provider, task_name) 缓存 ChatOpenAI 实例（实例无状态可复用）"""
        key = (name, task_name)
        with self._cache_lock:
            cached = self._llm_cache.get(key)
            if cached is not None:
                return cached
            llm = self._build_llm(self._providers[name], task_name)
            self._llm_cache[key] = llm
            return llm

    def _build_llm(self, config: dict, task_name: str | None) -> "ChatOpenAI":
        """从配置构建 ChatOpenAI 实例"""
        params = {
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 2000),
        }
        if task_name in self.TASK_TEMPERATURE_CONFIG:
            params.update(self.TASK_TEMPERATURE_CONFIG[task_name])

        return ChatOpenAI(
            model=config.get("model_name", ""),
            base_url=config.get("base_url", "").rstrip("/"),
            api_key=config.get("api_key") or "not-needed",
            temperature=params["temperature"],
            max_tokens=params["max_tokens"],
            timeout=config.get("timeout", 60),
        )

    def get_available_providers(self) -> list[str]:
        """获取可用提供商列表（按优先级排序）"""
        return [name for name in self._priority if name in self._providers]

    def get_current_provider(self) -> str | None:
        """获取当前提供商（failover 成功后记录的那个）"""
        if self._current_provider and self._current_provider in self._providers:
            return self._current_provider
        available = self.get_available_providers()
        return available[0] if available else None
