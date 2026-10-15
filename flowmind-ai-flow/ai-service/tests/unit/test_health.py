"""
FlowMind 智能流程设计服务 - 健康检查单元测试

验证模型健康接口只输出脱敏后的运行时配置。
"""

import pytest

from app.api import health
from app.llm.runtime import ModelRuntime, ModelRuntimeConfig


def _runtime(*names: str, enabled: bool = True, max_retries: int = 3) -> ModelRuntime:
    providers = {
        name: {
            "model_name": f"model-{name}",
            "base_url": f"https://{name}.test/v1",
            "supports_structured_output": True,
        }
        for name in names
    }
    return ModelRuntime(
        providers,
        list(names),
        ModelRuntimeConfig(enabled=enabled, max_retries=max_retries),
    )


async def test_model_health_uses_safe_runtime_description(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = _runtime("primary")
    providers = [
        {
            "name": "primary",
            "model": "model-primary",
            "priority": 1,
            "configured": True,
            "supports_structured_output": True,
        }
    ]
    monkeypatch.setattr(health, "get_model_runtime", lambda: runtime)

    result = await health.model_health_check.__wrapped__(None)

    data = dict(result.data)
    assert data.pop("timestamp")
    assert data == {
        "status": "configured",
        "primary_provider": "primary",
        "total_count": 1,
        "structured_provider_count": 1,
        "fallback_enabled": True,
        "fallback_max_retries": 3,
        "eligible_structured_provider_count": 1,
        "structured_fallback_ready": True,
        "not_ready_reasons": [],
        "providers": providers,
    }
    assert "api_key" not in str(result.data)
    assert "base_url" not in str(result.data)


async def test_readiness_returns_503_without_any_configured_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(health, "get_model_runtime", lambda: _runtime())

    response = await health.readiness_check.__wrapped__(None)

    assert response.status_code == 503


async def test_readiness_accepts_single_structured_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = _runtime("primary")
    monkeypatch.setattr(health, "get_model_runtime", lambda: runtime)

    response = await health.readiness_check.__wrapped__(None)

    assert response.code == 200
    assert response.data["structured_fallback_ready"] is True


async def test_readiness_accepts_disabled_fallback_with_configured_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 降级开关关闭不影响就绪判定：只要有一个可用模型即可接流量
    runtime = _runtime("primary", enabled=False)
    monkeypatch.setattr(health, "get_model_runtime", lambda: runtime)

    response = await health.readiness_check.__wrapped__(None)

    assert response.code == 200
    assert runtime.describe_readiness()["fallback_enabled"] is False


async def test_readiness_accepts_zero_retry_budget_with_configured_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = _runtime("primary", max_retries=0)
    monkeypatch.setattr(health, "get_model_runtime", lambda: runtime)

    response = await health.readiness_check.__wrapped__(None)

    assert response.code == 200


@pytest.mark.parametrize(
    "backup_config",
    [
        {
            "model_name": "your_structured_model",
            "base_url": "https://backup.test/v1",
        },
        {"model_name": "model-backup", "base_url": "not-a-url"},
        {
            "model_name": "model-backup",
            "base_url": "https://backup.test/v1",
            "api_key": "your_secondary_api_key_here",
        },
    ],
)
async def test_readiness_excludes_invalid_provider_from_candidates(
    monkeypatch: pytest.MonkeyPatch, backup_config: dict[str, str]
) -> None:
    # 未配置的占位 Provider 不进降级候选：不影响就绪判定，也不吃重试预算
    runtime = ModelRuntime(
        providers={
            "primary": {
                "model_name": "model-primary",
                "base_url": "https://primary.test/v1",
                "supports_structured_output": True,
            },
            "backup": {
                **backup_config,
                "supports_structured_output": True,
            },
        },
        priority=["primary", "backup"],
    )
    monkeypatch.setattr(health, "get_model_runtime", lambda: runtime)

    response = await health.readiness_check.__wrapped__(None)

    assert response.code == 200
    assert runtime.describe_readiness()["eligible_structured_provider_count"] == 1
