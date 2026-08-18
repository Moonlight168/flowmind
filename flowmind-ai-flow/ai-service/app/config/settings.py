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

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 加载 .env 文件（确保在 Settings 初始化前读取环境变量）
_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path, override=True)

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
    },
    {
        "name": "qwen",
        "model": "qwen-turbo",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": None,
    },
]


class DatabaseSettings(BaseSettings):
    """数据库配置"""

    url: str | None = Field(
        default=None,
        alias="DATABASE_URL",
    )

    model_config = SettingsConfigDict(env_prefix="DB_", env_file=".env", env_file_encoding="utf-8", extra="ignore")


class RedisSettings(BaseSettings):
    """Redis 配置"""

    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    db: int = Field(default=0)
    password: str | None = Field(default=None)
    checkpoint_ttl_hours: int = Field(default=720)  # 30天

    model_config = SettingsConfigDict(env_prefix="REDIS_", env_file=".env", env_file_encoding="utf-8", extra="ignore")


class FallbackSettings(BaseSettings):
    """容错配置"""

    enabled: bool = Field(default=True)
    max_retries: int = Field(default=3)
    retry_interval: float = Field(default=1.0)

    model_config = SettingsConfigDict(env_prefix="FALLBACK_", env_file=".env", env_file_encoding="utf-8", extra="ignore")


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

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", env_file_encoding="utf-8", extra="ignore")

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

    model_config = SettingsConfigDict(env_prefix="LOG_", env_file=".env", env_file_encoding="utf-8", extra="ignore")


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

    model_config = SettingsConfigDict(env_prefix="BACKEND_", env_file=".env", env_file_encoding="utf-8", extra="ignore")


class NacosSettings(BaseSettings):
    """Nacos 配置"""

    server_addr: str = Field(default="localhost:8848")

    model_config = SettingsConfigDict(env_prefix="NACOS_", env_file=".env", env_file_encoding="utf-8", extra="ignore")


class CompressConfig(BaseSettings):
    """对话历史压缩配置"""

    max_messages: int = Field(default=12, description="消息数超过该值才触发压缩")
    keep_recent: int = Field(default=4, description="保留最近 N 条完整消息")
    enable_llm_summary: bool = Field(default=True, description="True=中间段 LLM 摘要；False=纯裁剪")
    summary_max_tokens: int = Field(default=300, description="LLM 摘要 token 上限")

    model_config = SettingsConfigDict(env_prefix="COMPRESS_", env_file=".env", env_file_encoding="utf-8", extra="ignore")


class ValidationConfig(BaseSettings):
    """校验配置"""

    review_max_retry_count: int = Field(default=3, description="review 节点重试预算")

    model_config = SettingsConfigDict(env_prefix="VALIDATION_", env_file=".env", env_file_encoding="utf-8", extra="ignore")


class Settings(BaseSettings):
    """应用主配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=('settings_',),  # 禁用 model_ 命名空间保护
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    fallback: FallbackSettings = Field(default_factory=FallbackSettings)
    app: AppSettings = Field(default_factory=AppSettings)
    backend: BackendSettings = Field(default_factory=BackendSettings)
    nacos: NacosSettings = Field(default_factory=NacosSettings)
    log: LogSettings = Field(default_factory=LogSettings)
    compress: CompressConfig = Field(default_factory=CompressConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)

    jwt_secret: str = Field(default_factory=lambda: os.getenv("JWT_SECRET", ""))

    model_priority: str = Field(default="vllm,qwen")
    triple_protection_enabled: bool = Field(default=True)  # 三级保障体系开关
    rules_table: str = Field(default="approval_rules")
    langgraph_checkpoint_dir: str | None = Field(default=None)

    @field_validator("model_priority", mode="before")
    @classmethod
    def validate_model_priority(cls, v: str) -> str:
        return v.strip() if v else "vllm,qwen"

    def get_model_priority(self) -> list[str]:
        return [p.strip() for p in self.model_priority.split(",")]

    def get_model_providers(self) -> dict[str, dict]:
        """获取模型列表配置"""
        # 优先从环境变量 MODELS 读取 JSON 配置
        models_env = os.getenv("MODELS", "")
        if models_env:
            try:
                models_list = json.loads(models_env)
                return {m["name"]: _normalize_model_config(m) for m in models_list if m.get("name")}
            except json.JSONDecodeError:
                pass  # 解析失败，使用默认配置

        # 默认配置
        return {m["name"]: _normalize_model_config(m) for m in DEFAULT_MODELS}

    def get_fallback_config(self) -> dict:
        return {
            "enabled": self.fallback.enabled,
            "max_retries": self.fallback.max_retries,
            "retry_interval": self.fallback.retry_interval,
        }

    def reload_model_priority(self, new_priority: str | None = None) -> list[str]:
        """重新加载模型优先级配置

        Args:
            new_priority: 新的优先级字符串，为 None 时从环境变量加载

        Returns:
            更新后的模型优先级列表
        """
        if new_priority is None:
            new_priority = os.getenv("MODEL_PRIORITY", self.model_priority)
        self.model_priority = new_priority
        return self.get_model_priority()

    def update_fallback_config(
        self,
        enabled: bool | None = None,
        max_retries: int | None = None,
        retry_interval: float | None = None,
    ) -> dict:
        """更新降级配置

        Args:
            enabled: 是否启用降级
            max_retries: 最大重试次数
            retry_interval: 重试间隔

        Returns:
            更新后的降级配置
        """
        if enabled is not None:
            self.fallback.enabled = enabled
        if max_retries is not None:
            self.fallback.max_retries = max_retries
        if retry_interval is not None:
            self.fallback.retry_interval = retry_interval

        return self.get_fallback_config()


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
    }


settings = Settings()
