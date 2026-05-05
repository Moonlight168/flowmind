"""
FlowMind 智能流程设计服务 - 模型适配器抽象基类

本模块定义模型适配器的抽象接口和通用数据结构。
不包含任何 HTTP 实现细节。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ModelConfig:
    """模型配置"""

    model_name: str
    base_url: str
    api_key: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 0.9
    timeout: int = 60
    extra_params: dict[str, Any] = field(default_factory=dict)
    # 结构化输出配置
    response_format: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = {
            "model_name": self.model_name,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "timeout": self.timeout,
        }
        if self.api_key is not None:
            result["api_key"] = self.api_key
        if self.extra_params:
            result.update(self.extra_params)
        if self.response_format is not None:
            result["response_format"] = self.response_format
        return result


@dataclass
class ModelResponse:
    """模型响应"""

    content: str
    model_name: str
    usage: dict[str, int] | None = None
    raw_response: dict[str, Any] | None = None
    success: bool = True
    error_message: str | None = None


class ModelAdapter(ABC):
    """模型适配器抽象基类

    定义模型适配器的统一接口，不包含具体实现。
    具体实现由子类（如 HttpModelAdapter）提供。
    """

    def __init__(self, config: ModelConfig):
        self.config = config
        self._is_healthy = True

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """生成文本（单轮对话入口）

        Args:
            prompt: 输入提示词
            **kwargs: 额外参数

        Returns:
            模型响应
        """
        pass

    @abstractmethod
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
        pass

    @property
    def model_name(self) -> str:
        """模型名称"""
        return self.config.model_name

    def _merge_params(self, **kwargs) -> dict[str, Any]:
        """合并参数

        Args:
            **kwargs: 额外参数

        Returns:
            合并后的参数字典
        """
        params = {
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
        }
        params.update(kwargs)
        return params
