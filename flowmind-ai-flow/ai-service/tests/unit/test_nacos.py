"""
FlowMind 智能流程设计服务 - Nacos 配置开关测试
"""

from app.infra import nacos


def test_disabled_nacos_skips_registry_initialization(monkeypatch) -> None:
    monkeypatch.setattr(nacos.settings.nacos, "enabled", False)
    monkeypatch.setattr(
        nacos,
        "get_registry",
        lambda: (_ for _ in ()).throw(AssertionError("不应初始化 Nacos")),
    )

    assert nacos.register_to_nacos() is True
    assert nacos.deregister_from_nacos() is True
