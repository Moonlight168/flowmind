"""
FlowMind 智能流程设计服务 - 统一环境配置测试

验证功能开关和运行参数统一由 Pydantic Settings 从 .env/环境变量加载。
"""

import pytest

from app.config.settings import (
    NacosSettings,
    ObservabilitySettings,
    PromptSettings,
    Settings,
)


def test_feature_settings_load_environment_values(monkeypatch) -> None:
    monkeypatch.setenv("PROMPT_ROLLOUT_ENABLED", "true")
    monkeypatch.setenv("PROMPT_VERSION_OVERRIDES", '{"agents/chat.md":"v2"}')
    monkeypatch.setenv("LANGFUSE_TRACING_ENABLED", "false")
    monkeypatch.setenv("NACOS_ENABLED", "false")

    assert PromptSettings().rollout_enabled is True
    assert PromptSettings().version_overrides == {"agents/chat.md": "v2"}
    assert ObservabilitySettings().tracing_enabled is False
    assert NacosSettings().enabled is False


def test_root_settings_parse_models_and_credentials(monkeypatch) -> None:
    monkeypatch.setenv(
        "MODELS",
        '[{"name":"primary","model":"model-a","base_url":"http://model/v1"}]',
    )
    monkeypatch.setenv("JWT_SECRET", "jwt-from-env")
    monkeypatch.setenv("FLOWMIND_AUTH_TOKEN", "eval-token")

    configured = Settings()

    assert configured.jwt_secret == "jwt-from-env"
    assert configured.evaluation.auth_token == "eval-token"
    assert configured.get_model_providers()["primary"]["model_name"] == "model-a"


def test_model_provider_keeps_compatibility_options(monkeypatch) -> None:
    monkeypatch.setenv(
        "MODELS",
        """[{"name":"deepseek","model":"deepseek-v4-flash","base_url":"https://api.deepseek.com","extra_body":{"thinking":{"type":"disabled"}},"structured_output_method":"function_calling"}]""",
    )

    provider = Settings().get_model_providers()["deepseek"]

    assert provider["extra_body"] == {"thinking": {"type": "disabled"}}
    assert provider["structured_output_method"] == "function_calling"


def test_model_provider_rejects_unknown_structured_output_method(monkeypatch) -> None:
    monkeypatch.setenv(
        "MODELS",
        '[{"name":"broken","model":"model-a","structured_output_method":"typo"}]',
    )

    with pytest.raises(ValueError, match="不支持的 structured_output_method"):
        Settings().get_model_providers()
