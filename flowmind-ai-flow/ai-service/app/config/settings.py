"""
FlowMind 智能流程设计服务 - 配置管理

本模块负责管理应用的全局配置，使用分层配置结构。
职责：
1. 从环境变量和 .env 文件加载配置
2. 提供配置验证和默认值
3. 管理数据库、LLM 和服务器配置

作者: wish168
版本: 3.0.0
"""

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 加载 .env 文件（确保在 Settings 初始化前读取环境变量）
_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path, override=False)

# ============ 默认值常量 ============
SECONDS_PER_HOUR = 3600
DEFAULT_MAX_TOKENS = 4096  # 增加到 4096 以支持复杂流程设计
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9

# 默认模型配置
DEFAULT_MODELS = [
    {
        "name": "vllm",
        "model": "qwen2.5_1.5b_instruct",
        "base_url": "http://localhost:8001/v1",
        "timeout": 60,
        "supports_structured_output": False,
    },
    {
        "name": "qwen",
        "model": "qwen-turbo",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": None,
        "supports_structured_output": True,
    },
]


class DatabaseSettings(BaseSettings):
    """数据库配置"""

    url: str | None = Field(
        default=None,
        alias="DATABASE_URL",
    )

    model_config = SettingsConfigDict(
        env_prefix="DB_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class RedisSettings(BaseSettings):
    """Redis 配置"""

    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    db: int = Field(default=0)
    password: str | None = Field(default=None)
    checkpoint_ttl_hours: int = Field(default=720)  # 30天

    model_config = SettingsConfigDict(
        env_prefix="REDIS_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class FallbackSettings(BaseSettings):
    """容错配置"""

    enabled: bool = Field(default=True)
    max_retries: int = Field(
        default=3, ge=0, description="首选模型之外允许尝试的备用 Provider 数量"
    )
    retry_interval: float = Field(
        default=1.0, ge=0, description="切换 Provider 前的等待秒数"
    )

    model_config = SettingsConfigDict(
        env_prefix="FALLBACK_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class AppSettings(BaseSettings):
    """应用配置"""

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    debug: bool = Field(default=True)
    allowed_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:80"],
        description="允许的跨域来源，prod环境需修改为实际域名",
    )
    execution_mode: str = Field(
        default="invoke",
        description="工作流执行模式: stream(分步执行,调试用) / invoke(同步执行,生产用)",
    )
    workers: int = Field(
        default=4,
        description="uvicorn worker 进程数（debug 模式强制为 1）",
    )

    model_config = SettingsConfigDict(
        env_prefix="APP_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @field_validator("execution_mode")
    @classmethod
    def validate_execution_mode(cls, v: str) -> str:
        allowed = ["stream", "invoke"]
        if v not in allowed:
            raise ValueError(f"execution_mode 仅支持: {', '.join(allowed)}")
        return v


class LogSettings(BaseSettings):
    """日志配置"""

    level: str = Field(default="INFO")  # DEBUG/INFO/ERROR
    format: str = Field(default="chain")  # simple/detailed/chain
    llm_detail: str = Field(default="summary")  # none/summary/full

    model_config = SettingsConfigDict(
        env_prefix="LOG_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        allowed_formats = ["simple", "detailed", "chain"]
        value = v.lower()
        if value not in allowed_formats:
            raise ValueError("日志格式仅支持: " + ", ".join(allowed_formats))
        return value

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        allowed_levels = ["DEBUG", "INFO", "ERROR"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"日志级别仅支持: {', '.join(allowed_levels)}")
        return v.upper()


class BackendSettings(BaseSettings):
    """后端服务配置"""

    base_url: str = Field(
        default="http://localhost:9001",
        alias="BACKEND_BASE_URL",
    )
    category_api_path: str = Field(default="/flowable/category")
    form_api_path: str = Field(default="/flowable/form")
    flow_model_api_path: str = Field(default="/flowable/model")
    role_api_path: str = Field(default="/system/role")
    timeout: int = Field(default=30)

    model_config = SettingsConfigDict(
        env_prefix="BACKEND_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class NacosSettings(BaseSettings):
    """Nacos 配置"""

    enabled: bool = Field(default=True)
    server_addr: str = Field(default="localhost:8848")
    register_ip: str | None = Field(default=None)
    register_port: int = Field(default=0, ge=0, le=65535)
    max_retries: int = Field(default=5, ge=1)
    retry_interval: float = Field(default=5.0, ge=0)

    model_config = SettingsConfigDict(
        env_prefix="NACOS_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class ObservabilitySettings(BaseSettings):
    """Langfuse 链路监控配置。"""

    public_key: str = Field(default="")
    secret_key: str = Field(default="")
    base_url: str = Field(default="https://cloud.langfuse.com")
    tracing_enabled: bool = Field(default=True)
    tracing_environment: str = Field(default="development")

    model_config = SettingsConfigDict(
        env_prefix="LANGFUSE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class PromptSettings(BaseSettings):
    """提示词版本与灰度发布配置。"""

    rollout_enabled: bool = Field(default=False)
    version_overrides: dict[str, str] = Field(default_factory=dict)

    model_config = SettingsConfigDict(
        env_prefix="PROMPT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class EvaluationSettings(BaseSettings):
    """黄金数据集运行配置。"""

    auth_token: str = Field(default="")

    model_config = SettingsConfigDict(
        env_prefix="FLOWMIND_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class CompressConfig(BaseSettings):
    """对话历史压缩配置"""

    max_messages: int = Field(default=12, description="消息数超过该值才触发压缩")
    keep_recent: int = Field(default=4, description="保留最近 N 条完整消息")
    enable_llm_summary: bool = Field(
        default=True, description="True=中间段 LLM 摘要；False=纯裁剪"
    )
    summary_max_tokens: int = Field(default=300, description="LLM 摘要 token 上限")

    model_config = SettingsConfigDict(
        env_prefix="COMPRESS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ValidationConfig(BaseSettings):
    """校验配置"""

    review_max_retry_count: int = Field(default=3, description="review 节点重试预算")
    structured_max_retry_count: int = Field(
        default=3, ge=1, description="结构化内容语义重试预算"
    )

    model_config = SettingsConfigDict(
        env_prefix="VALIDATION_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Settings(BaseSettings):
    """应用主配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),  # 禁用 model_ 命名空间保护
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    fallback: FallbackSettings = Field(default_factory=FallbackSettings)
    app: AppSettings = Field(default_factory=AppSettings)
    backend: BackendSettings = Field(default_factory=BackendSettings)
    nacos: NacosSettings = Field(default_factory=NacosSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    prompt: PromptSettings = Field(default_factory=PromptSettings)
    evaluation: EvaluationSettings = Field(default_factory=EvaluationSettings)
    log: LogSettings = Field(default_factory=LogSettings)
    compress: CompressConfig = Field(default_factory=CompressConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)

    jwt_secret: str = Field(default="")
    models: list[dict[str, Any]] = Field(
        default_factory=lambda: [dict(model) for model in DEFAULT_MODELS]
    )

    model_priority: str = Field(default="vllm,qwen")

    @field_validator("model_priority", mode="before")
    @classmethod
    def validate_model_priority(cls, v: str) -> str:
        return v.strip() if v else "vllm,qwen"

    def get_model_priority(self) -> list[str]:
        return [p.strip() for p in self.model_priority.split(",")]

    def get_model_providers(self) -> dict[str, dict]:
        """获取模型列表配置"""
        return {
            model["name"]: _normalize_model_config(model)
            for model in self.models
            if model.get("name")
        }

    def get_fallback_config(self) -> dict:
        return {
            "enabled": self.fallback.enabled,
            "max_retries": self.fallback.max_retries,
            "retry_interval": self.fallback.retry_interval,
        }


def _normalize_model_config(model: dict) -> dict:
    """标准化模型配置，补充默认值并统一字段名"""
    return {
        "model_name": model.get("model", ""),
        "base_url": model.get("base_url", ""),
        "api_key": model.get("api_key"),
        "temperature": model.get("temperature", DEFAULT_TEMPERATURE),
        "max_tokens": model.get("max_tokens", DEFAULT_MAX_TOKENS),
        "top_p": model.get("top_p", DEFAULT_TOP_P),
        "timeout": model.get("timeout", 60),
        "thinking": model.get("thinking", False),
        "supports_structured_output": model.get("supports_structured_output", True),
    }


settings = Settings()
