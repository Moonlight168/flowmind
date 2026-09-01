"""
FlowMind 智能流程设计服务 - 请求级缓存单元测试
"""

from app.core import request_cache


def test_factory_called_once_on_cache_hit() -> None:
    calls = {"n": 0}

    def factory() -> list[str]:
        calls["n"] += 1
        return ["a", "b"]

    assert request_cache.get("k_once", factory) == ["a", "b"]
    assert request_cache.get("k_once", factory) == ["a", "b"]
    assert calls["n"] == 1


def test_empty_result_is_cached() -> None:
    """空列表也是有效结果，不应重复调用 factory"""
    calls = {"n": 0}

    def factory() -> list:
        calls["n"] += 1
        return []

    assert request_cache.get("k_empty", factory) == []
    assert request_cache.get("k_empty", factory) == []
    assert calls["n"] == 1


def test_distinct_keys_isolated() -> None:
    assert request_cache.get("k_a", lambda: 1) == 1
    assert request_cache.get("k_b", lambda: 2) == 2


def test_scopes_do_not_share_cached_values() -> None:
    with request_cache.scope():
        assert request_cache.get("same", lambda: "first") == "first"
    with request_cache.scope():
        assert request_cache.get("same", lambda: "second") == "second"
