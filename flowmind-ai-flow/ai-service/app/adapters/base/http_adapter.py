"""
FlowMind 智能流程设计服务 - HTTP 模型适配器实现

本模块提供基于 HTTP 的模型适配器实现。
依赖于 adapter.py 中的抽象基类。

调用链:
    generate(prompt) ──────────────┐
                                   ├──→ _generate_core(messages)
    generate_with_messages(messages) ──┘
"""

import json
import time
from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import requests

from app.adapters.base.adapter import (
    ModelAdapter,
    ModelConfig,
    ModelResponse,
)
from app.adapters.base.errors import ModelErrorCode, ModelError, classify_error
from app.infra.logger import logger


@dataclass
class HttpAdapterConfig:
    """HTTP 适配器配置"""

    # 适配器名称
    name: str
    # API URL（可以是完整 URL 或端点）
    api_url: str
    # 是否需要 API Key
    requires_api_key: bool = True
    # API Key 请求头名称
    api_key_header: str = "Authorization"
    # API Key 前缀（如 "Bearer "）
    api_key_prefix: str = "Bearer "
    # 请求体构建函数
    payload_builder: Callable[[list[dict], dict], dict] | None = None
    # 响应解析函数
    response_parser: Callable[[dict, str], ModelResponse] | None = None
    # 额外请求头
    extra_headers: dict[str, str] = field(default_factory=dict)
    # 额外请求参数
    extra_params: dict[str, Any] = field(default_factory=dict)


class HttpModelAdapter(ModelAdapter):
    """HTTP 模型适配器基类

    提供通用的 HTTP 请求处理、错误处理和响应解析功能。
    子类只需实现具体的请求构建和响应解析逻辑。

    调用链:
        generate(prompt) ──────────────┐
                                       ├──→ _generate_core(messages)
        generate_with_messages(messages) ──┘
    """

    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """生成文本（单轮对话入口）

        Args:
            prompt: 输入提示词
            **kwargs: 额外参数（包括 messages_for_log 用于日志）

        Returns:
            模型响应
        """
        messages_for_log = kwargs.pop("messages_for_log", None)

        if messages_for_log:
            messages = messages_for_log
        else:
            messages = [{"role": "user", "content": prompt}]

        return self._generate_core(
            messages,
            **kwargs
        )

    def generate_with_messages(
        self, messages: list[dict[str, str]], **kwargs
    ) -> ModelResponse:
        """使用消息列表生成文本（多轮对话入口）

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            **kwargs: 额外参数

        Returns:
            模型响应
        """
        return self._generate_core(messages, **kwargs)

    def _generate_core(
        self, messages: list[dict[str, str]], **kwargs
    ) -> ModelResponse:
        """核心实现 - HTTP 请求、错误处理、响应解析

        Args:
            messages: 消息列表
            **kwargs: 额外参数，health_check 为 True 时静默默认日志

        Returns:
            模型响应
        """
        start_time = time.time()

        try:
            url = self._get_api_url()
            headers = self._build_headers()
            payload = self._build_payload(messages, **kwargs)

            is_health_check = kwargs.get("health_check", False)

            if not is_health_check:
                logger.debug(f"[{self._get_adapter_name()}] 请求 URL: {url}")
                logger.debug(f"[{self._get_adapter_name()}] Messages: {len(messages)} 条")
                logger.debug(f"[{self._get_adapter_name()}] Payload: {self._format_payload(payload)}")

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.config.timeout,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if not is_health_check:
                logger.debug(f"[{self._get_adapter_name()}] 响应状态码：{response.status_code}")

            if response.status_code != 200:
                return self._handle_error_response(response, is_health_check)

            response.raise_for_status()
            result = self._parse_response(response.json())

            if not is_health_check:
                self._log_success_response(
                    messages=messages,
                    result=result,
                    latency_ms=latency_ms,
                )

            return result

        except ModelError:
            raise
        except requests.Timeout as e:
            return self._handle_exception(e, "请求超时", ModelErrorCode.TIMEOUT_ERROR, is_health_check)
        except requests.ConnectionError as e:
            return self._handle_exception(e, "连接错误", ModelErrorCode.NETWORK_ERROR, is_health_check)
        except requests.HTTPError as e:
            return self._handle_http_error(e, is_health_check)
        except (KeyError, ValueError) as e:
            return self._handle_exception(e, "响应解析错误", ModelErrorCode.PARSE_ERROR, is_health_check)
        except Exception as e:
            return self._handle_exception(e, "未知错误", ModelErrorCode.UNKNOWN_ERROR, is_health_check)

    def _get_adapter_name(self) -> str:
        """获取适配器名称，用于日志"""
        return self.config.model_name

    def _log_success_response(
        self,
        messages: list[dict[str, str]],
        result: ModelResponse,
        latency_ms: int,
    ) -> None:
        """记录成功响应的详细日志

        Args:
            messages: 请求消息列表
            result: 解析后的响应
            latency_ms: 延迟（毫秒）
        """
        tokens = result.usage or {}
        node_name = self._get_adapter_name()
        model_name = self.config.model_name

        logger.bind(
            node=node_name,
            model_name=model_name,
        ).info(
            "LLM调用",
            tokens_in=tokens.get("prompt_tokens", 0),
            tokens_out=tokens.get("completion_tokens", 0),
            latency_ms=latency_ms,
        )

    def _format_payload(self, payload: dict) -> str:
        """格式化 payload 输出（精简模式）

        Args:
            payload: 请求 payload

        Returns:
            精简的 payload 字符串表示
        """
        model = payload.get("model", "unknown")
        messages = payload.get("messages", [])
        msg_count = len(messages)
        temperature = payload.get("temperature", "N/A")

        has_schema = "response_format" in payload

        parts = [f"model={model}", f"messages={msg_count}条"]
        if has_schema:
            parts.append("JSON Schema")
        parts.append(f"temp={temperature}")

        return ", ".join(parts)

    @abstractmethod
    def _get_api_url(self) -> str:
        """获取 API URL"""
        pass

    @abstractmethod
    def _build_headers(self) -> dict[str, str]:
        """构建请求头"""
        pass

    @abstractmethod
    def _build_payload(
        self, messages: list[dict[str, str]], **kwargs
    ) -> dict[str, Any]:
        """构建请求体"""
        pass

    @abstractmethod
    def _parse_response(self, response: dict[str, Any]) -> ModelResponse:
        """解析响应"""
        pass

    def _handle_exception(
        self, error: Exception, message: str, error_type: ModelErrorCode, is_health_check: bool = False
    ) -> ModelResponse:
        """处理异常"""
        bound_logger = logger.bind(node=self._get_adapter_name(), model_name=self.config.model_name)
        log_msg = f"[{self._get_adapter_name()}] {message}: {error}"
        if is_health_check:
            bound_logger.debug(log_msg)
        else:
            bound_logger.error(log_msg)
        if error_type in (ModelErrorCode.NETWORK_ERROR, ModelErrorCode.TIMEOUT_ERROR,
                          ModelErrorCode.SERVICE_ERROR):
            self._is_healthy = False
        raise ModelError(
            error_type=error_type,
            message=f"[{self._get_adapter_name()}] {message}: {error}",
            model_name=self.config.model_name,
            original_error=error,
        )

    def _handle_http_error(self, error: requests.HTTPError, is_health_check: bool = False) -> ModelResponse:
        """处理 HTTP 错误"""
        error_type = classify_error(error)
        bound_logger = logger.bind(node=self._get_adapter_name(), model_name=self.config.model_name)
        log_msg = f"[{self._get_adapter_name()}] HTTP 错误：{error}"
        if is_health_check:
            bound_logger.debug(log_msg)
        else:
            bound_logger.error(log_msg)
        if error.response.status_code >= 500:
            self._is_healthy = False
        raise ModelError(
            error_type=error_type,
            message=f"[{self._get_adapter_name()}] HTTP 错误：{error}",
            model_name=self.config.model_name,
            original_error=error,
        )

    def _handle_error_response(self, response: requests.Response, is_health_check: bool = False) -> ModelResponse:
        """处理错误响应，子类可覆盖以实现特定错误处理"""
        try:
            error_data = response.json()
            error_code = error_data.get("code") or error_data.get("error", {}).get("code", "unknown")
            error_message = error_data.get("message") or error_data.get("error", {}).get("message", response.text)
        except json.JSONDecodeError:
            error_code = "unknown"
            error_message = response.text

        model_name = self.config.model_name
        bound_logger = logger.bind(node=self._get_adapter_name(), model_name=model_name)
        log_msg = f"[{self._get_adapter_name()}] API 错误 [{response.status_code}]: {error_code} - {error_message}"
        if is_health_check:
            bound_logger.debug(log_msg)
        else:
            bound_logger.error(log_msg)

        if response.status_code == 401:
            self._is_healthy = False
            raise ModelError(
                error_type=ModelErrorCode.AUTH_ERROR,
                message=f"[{self._get_adapter_name()}] 认证失败：{error_message}",
                model_name=self.config.model_name,
            )
        elif response.status_code == 429:
            raise ModelError(
                error_type=ModelErrorCode.RATE_LIMIT_ERROR,
                message=f"{self._get_adapter_name()} 限流：{error_message}",
                model_name=self.config.model_name,
            )
        elif response.status_code >= 500:
            self._is_healthy = False
            raise ModelError(
                error_type=ModelErrorCode.SERVICE_ERROR,
                message=f"{self._get_adapter_name()} 服务错误：{error_message}",
                model_name=self.config.model_name,
            )
        else:
            raise ModelError(
                error_type=classify_error(Exception(error_message), response.status_code),
                message=f"{self._get_adapter_name()} API 错误：{error_code} - {error_message}",
                model_name=self.config.model_name,
            )


class StandardHttpAdapter(HttpModelAdapter):
    """标准 HTTP 模型适配器

    提供开箱即用的 HTTP 适配器实现，通过配置替代继承减少子类代码。
    """

    def __init__(
        self,
        config: ModelConfig,
        adapter_config: HttpAdapterConfig,
    ):
        self.adapter_config = adapter_config
        super().__init__(config)

    def _get_adapter_name(self) -> str:
        """获取适配器名称"""
        return self.adapter_config.name

    def _get_api_url(self) -> str:
        """获取 API URL"""
        if not self.adapter_config.api_url:
            return self.config.base_url.rstrip("/")
        if self.adapter_config.api_url.startswith("http"):
            return self.adapter_config.api_url
        base = self.config.base_url.rstrip("/")
        endpoint = self.adapter_config.api_url.lstrip("/")
        return f"{base}/{endpoint}"

    def _build_headers(self) -> dict[str, str]:
        """构建请求头"""
        headers = {"Content-Type": "application/json"}
        headers.update(self.adapter_config.extra_headers)

        if self.adapter_config.requires_api_key and self.config.api_key:
            header_name = self.adapter_config.api_key_header
            prefix = self.adapter_config.api_key_prefix
            headers[header_name] = f"{prefix}{self.config.api_key}"

        return headers

    def _build_payload(
        self, messages: list[dict[str, str]], **kwargs
    ) -> dict[str, Any]:
        """构建请求体"""
        builder = self.adapter_config.payload_builder
        if builder:
            params = self._merge_params(**kwargs)
            params["model_name"] = self.config.model_name
            return builder(messages, params)

        params = self._merge_params(**kwargs)
        return {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": params["temperature"],
            "max_tokens": params["max_tokens"],
            "top_p": params["top_p"],
        }

    def _parse_response(self, response: dict[str, Any]) -> ModelResponse:
        """解析响应"""
        parser = self.adapter_config.response_parser
        if parser:
            return parser(response, self.config.model_name)

        choices = response.get("choices", [])
        first_choice = choices[0] if choices else {}
        message = first_choice.get("message", {})
        content = message.get("content", "") if isinstance(message, dict) else ""
        usage = response.get("usage", {})

        return ModelResponse(
            content=content,
            model_name=self.config.model_name,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            raw_response=response,
            success=True,
        )


def parse_openai_response(
    response: dict[str, Any], model_name: str
) -> ModelResponse:
    """解析 OpenAI 格式响应"""
    choices = response.get("choices", [])
    first_choice = choices[0] if choices else {}
    message = first_choice.get("message", {})
    content = message.get("content", "") if isinstance(message, dict) else ""
    usage = response.get("usage", {})

    return ModelResponse(
        content=content,
        model_name=model_name,
        usage={
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        },
        raw_response=response,
        success=True,
    )


def build_openai_compatible_payload(messages: list[dict], params: dict) -> dict[str, Any]:
    """构建 OpenAI 兼容 API 请求体

    Args:
        messages: 消息列表
        params: 参数配置

    Returns:
        请求体字典
    """
    payload = {
        "model": params.get("model_name", ""),
        "messages": messages,
        "temperature": params["temperature"],
        "max_tokens": params["max_tokens"],
        "top_p": params["top_p"],
    }
    if params.get("response_format"):
        payload["response_format"] = params["response_format"]
    if params.get("thinking"):
        payload["thinking"] = {"type": "enabled"}
    return payload


def build_json_schema(
    schema: dict[str, Any],
    name: str,
    description: str = "",
    strict: bool = True,
) -> dict[str, Any]:
    """构建 JSON Schema 格式的 response_format

    Args:
        schema: JSON Schema 定义
        name: Schema 名称
        description: Schema 描述（可选）
        strict: 是否启用严格模式（默认 True）

    Returns:
        response_format 配置，可直接用于 API 请求
    """
    result = {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "schema": schema,
            "strict": strict,
        }
    }
    if description:
        result["json_schema"]["description"] = description
    return result
