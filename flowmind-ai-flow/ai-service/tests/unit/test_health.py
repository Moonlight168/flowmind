"""
FlowMind 智能流程设计服务 - 健康检查单元测试

验证模型健康接口只输出脱敏后的运行时配置。
"""

from app.api import health


async def test_model_health_uses_safe_runtime_description(monkeypatch) -> None:
    providers = [
        {
            "name": "primary",
            "model": "model-a",
            "priority": 1,
            "supports_structured_output": True,
        }
    ]

    class _Runtime:
        def describe_providers(self):
            return providers

    monkeypatch.setattr(health, "get_model_runtime", _Runtime)

    result = await health.model_health_check.__wrapped__(None)

    data = dict(result.data)
    assert data.pop("timestamp")
    assert data == {
        "status": "configured",
        "primary_provider": "primary",
        "total_count": 1,
        "providers": providers,
    }
    assert "api_key" not in str(result.data)
    assert "base_url" not in str(result.data)
