"""
FlowMind 智能流程设计服务 - 统一模型运行时

本模块集中处理模型实例缓存、任务参数和运行时 Provider 降级。
"""

import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any, TypeVar

import httpx
from langchain_openai import ChatOpenAI
from openai import OpenAIError

from app.config.settings import settings
from app.infra.logger import logger
from app.infra.observability import observe_model_attempt, record_observation_output

T = TypeVar("T")
ModelBuilder = Callable[[str, dict[str, Any], str | None], Any]
ModelOperation = Callable[[Any], T]
PROVIDER_RUNTIME_ERRORS = (
    OpenAIError,
    httpx.HTTPError,
    ConnectionError,
    TimeoutError,
    OSError,
    RuntimeError,
)
MODEL_CONFIG_ERRORS = (ValueError, TypeError, KeyError, AttributeError)
_runtime: "ModelRuntime | None" = None
_runtime_lock = threading.RLock()


class ModelExhaustedError(RuntimeError):
    """所有符合任务能力要求的模型都不可用。"""


class PartialStreamError(Exception):
    """模型已输出部分内容后流式连接中断，禁止自动重放。"""


@dataclass(frozen=True)
class ModelRuntimeConfig:
    """模型运行时降级配置。"""

    enabled: bool = True
    max_retries: int = 3
    retry_interval: float = 1.0


class ModelRuntime:
    """在一个稳定 interface 后统一执行模型调用和 Provider 降级。"""

    TASK_PARAMETERS = {
        "category_design": {"temperature": 0.3},
        "flow_design": {"temperature": 0.3},
        "form_design": {"temperature": 0.3},
        "chat": {"temperature": 0.8},
        "compress": {"temperature": 0.0},
        "intent": {"temperature": 0.0, "max_tokens": 200},
    }

    def __init__(
        self,
        providers: dict[str, dict[str, Any]],
        priority: list[str],
        config: ModelRuntimeConfig | None = None,
        model_builder: ModelBuilder | None = None,
    ) -> None:
        self._providers = providers
        self._priority = priority
        self._config = config or ModelRuntimeConfig()
        self._model_builder = model_builder or self._build_model
        self._model_cache: dict[tuple[str, str | None], Any] = {}
        self._cache_lock = threading.RLock()

    def execute(
        self,
        task_name: str | None,
        operation: ModelOperation[T],
        *,
        structured: bool = False,
    ) -> T:
        """执行一次模型操作，运行时故障时按优先级切换 Provider。"""
        last_error: Exception | None = None
        for attempt, provider in enumerate(self._candidates(structured), start=1):
            if attempt > 1 and self._config.retry_interval > 0:
                time.sleep(self._config.retry_interval)
            try:
                model = self._get_model(provider, task_name)
            except MODEL_CONFIG_ERRORS as exc:
                last_error = exc
                self._log_failure(provider, attempt, exc)
                continue
            try:
                with observe_model_attempt(
                    task_name=task_name,
                    provider=provider,
                    attempt_index=attempt,
                    fallback_enabled=self._config.enabled,
                    structured_required=structured,
                    streaming=False,
                ) as observation:
                    try:
                        result = operation(model)
                    except PROVIDER_RUNTIME_ERRORS as exc:
                        _record_attempt_failure(observation, exc, token_started=False)
                        raise
                    record_observation_output(
                        observation, {"success": True, "token_started": False}
                    )
                    return result
            except PROVIDER_RUNTIME_ERRORS as exc:
                last_error = exc
                self._log_failure(provider, attempt, exc)

        raise ModelExhaustedError("所有符合任务要求的模型都不可用") from last_error

    def stream(
        self,
        task_name: str | None,
        messages: Any,
        *,
        config: dict[str, Any] | None = None,
    ) -> Iterator[Any]:
        """流式调用；首个 token 前允许切换，输出后失败原样抛出。"""
        last_error: Exception | None = None
        for attempt, provider in enumerate(self._candidates(False), start=1):
            if attempt > 1 and self._config.retry_interval > 0:
                time.sleep(self._config.retry_interval)
            try:
                model = self._get_model(provider, task_name)
            except MODEL_CONFIG_ERRORS as exc:
                last_error = exc
                self._log_failure(provider, attempt, exc)
                continue

            emitted = False
            try:
                with observe_model_attempt(
                    task_name=task_name,
                    provider=provider,
                    attempt_index=attempt,
                    fallback_enabled=self._config.enabled,
                    structured_required=False,
                    streaming=True,
                ) as observation:
                    try:
                        for chunk in model.stream(messages, config=config):
                            emitted = True
                            yield chunk
                    except PROVIDER_RUNTIME_ERRORS as exc:
                        _record_attempt_failure(observation, exc, token_started=emitted)
                        raise
                    record_observation_output(
                        observation, {"success": True, "token_started": emitted}
                    )
                return
            except PROVIDER_RUNTIME_ERRORS as exc:
                if emitted:
                    raise PartialStreamError("模型流式响应中断") from exc
                last_error = exc
                self._log_failure(provider, attempt, exc)

        raise ModelExhaustedError("所有符合任务要求的模型都不可用") from last_error

    def describe_providers(self) -> list[dict[str, Any]]:
        """返回按优先级排序且不含连接地址、密钥的 Provider 信息。"""
        return [
            {
                "name": name,
                "model": self._providers[name].get("model_name", ""),
                "priority": index,
                "supports_structured_output": self._providers[name].get(
                    "supports_structured_output", True
                ),
            }
            for index, name in enumerate(self._priority, start=1)
            if name in self._providers
        ]

    def _candidates(self, structured: bool) -> list[str]:
        candidates = [name for name in self._priority if name in self._providers]
        if structured:
            candidates = [
                name
                for name in candidates
                if self._providers[name].get("supports_structured_output", True)
            ]
        attempt_limit = 1 + max(0, self._config.max_retries)
        if not self._config.enabled:
            attempt_limit = 1
        return candidates[:attempt_limit]

    def _get_model(self, provider: str, task_name: str | None) -> Any:
        key = (provider, task_name)
        with self._cache_lock:
            if key not in self._model_cache:
                self._model_cache[key] = self._model_builder(
                    provider, self._providers[provider], task_name
                )
            return self._model_cache[key]

    def _build_model(
        self, provider: str, config: dict[str, Any], task_name: str | None
    ) -> ChatOpenAI:
        params = {
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 2000),
        }
        params.update(self.TASK_PARAMETERS.get(task_name, {}))
        if task_name == "compress":
            params["max_tokens"] = settings.compress.summary_max_tokens
        return ChatOpenAI(
            model=config.get("model_name", ""),
            base_url=config.get("base_url", "").rstrip("/"),
            api_key=config.get("api_key") or "not-needed",
            temperature=params["temperature"],
            max_tokens=params["max_tokens"],
            timeout=config.get("timeout", 60),
        )

    def _log_failure(self, provider: str, attempt: int, error: Exception) -> None:
        logger.warning(
            f"[ModelRuntime] provider={provider} 第 {attempt} 次尝试失败，"
            f"本次 Provider 不可用: {type(error).__name__}"
        )


def initialize_model_runtime() -> ModelRuntime:
    """从当前应用配置初始化全局模型运行时。"""
    global _runtime
    with _runtime_lock:
        if _runtime is None:
            fallback = settings.get_fallback_config()
            _runtime = ModelRuntime(
                providers=settings.get_model_providers(),
                priority=settings.get_model_priority(),
                config=ModelRuntimeConfig(
                    enabled=fallback.get("enabled", True),
                    max_retries=fallback.get("max_retries", 3),
                    retry_interval=fallback.get("retry_interval", 1.0),
                ),
            )
            logger.info(
                f"[ModelRuntime] 初始化完成，Provider="
                f"{[item['name'] for item in _runtime.describe_providers()]}"
            )
        return _runtime


def get_model_runtime() -> ModelRuntime:
    """获取全局模型运行时，尚未初始化时自动初始化。"""
    return initialize_model_runtime()


def reset_model_runtime() -> None:
    """清空全局模型运行时，供测试和配置重载使用。"""
    global _runtime
    with _runtime_lock:
        _runtime = None


def _record_attempt_failure(
    observation: Any | None, error: Exception, *, token_started: bool
) -> None:
    record_observation_output(
        observation,
        {
            "success": False,
            "failure_category": type(error).__name__,
            "token_started": token_started,
        },
    )
