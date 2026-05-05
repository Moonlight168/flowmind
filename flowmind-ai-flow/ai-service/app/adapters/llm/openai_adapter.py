"""
FlowMind 智能流程设计服务 - OpenAI 兼容格式通用适配器

本模块提供统一的 OpenAI 兼容格式适配器，支持：
- 阿里云 Qwen（DashScope 兼容模式）
- 火山引擎豆包（Doubao）
- 本地 vLLM 服务
- 其他 OpenAI 兼容 API

所有模型使用统一的请求/响应格式，无需为每个模型单独编写适配器。
"""

from app.adapters.base import (
    HttpAdapterConfig,
    ModelConfig,
    StandardHttpAdapter,
    build_openai_compatible_payload,
    parse_openai_response,
)


class OpenAICompatibleAdapter(StandardHttpAdapter):
    """OpenAI 兼容格式通用适配器

    统一使用 OpenAI 兼容格式：
    - 请求：{"model": "...", "messages": [...], "temperature": 0.7, ...}
    - 响应：{"choices": [{"message": {"content": "..."}}], "usage": {...}}
    """

    def __init__(self, name: str, config: ModelConfig):
        # 验证配置
        if not config.base_url:
            raise ValueError(f"[{name}] base_url 不能为空")

        # 判断是否需要 API Key
        # 规则：本地部署（localhost/127.0.0.1/vllm）不需要，其他都需要
        requires_api_key = self._requires_api_key(name, config.base_url)

        # 验证 API Key（如果需要）
        if requires_api_key and not config.api_key:
            raise ValueError(f"[{name}] API Key 不能为空")

        # 构建适配器配置
        adapter_config = HttpAdapterConfig(
            name=name,
            api_url="",  # base_url 已经是完整 URL
            requires_api_key=requires_api_key,
            payload_builder=build_openai_compatible_payload,
            response_parser=parse_openai_response,
        )

        super().__init__(config, adapter_config)

    def _requires_api_key(self, name: str, base_url: str) -> bool:
        """判断是否需要 API Key

        规则：
        - vLLM 通常不需要（除非配置了认证）
        - 云服务（Qwen/Doubao 等）需要

        Args:
            name: 适配器名称
            base_url: API 基础 URL

        Returns:
            是否需要 API Key
        """
        # 本地地址不需要 API Key
        local_indicators = [
            "localhost",
            "127.0.0.1",
            "host.docker.internal",
            "0.0.0.0",
        ]

        # 检查是否是本地部署
        for indicator in local_indicators:
            if indicator in base_url.lower():
                return False

        # 检查是否是 vLLM（通常本地部署不需要 API Key）
        if "vllm" in name.lower():
            return False

        # 其他情况默认需要 API Key（云服务）
        return True
