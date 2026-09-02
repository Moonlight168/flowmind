"""
FlowMind 智能流程设计服务 - 提示词版本与灰度发布测试

通过提示词加载公开入口验证同会话稳定分流、强制版本和监控元数据。
"""

import json

from app.infra.observability import langchain_config
from app.prompts import loader


def _write_registry(tmp_path, versions: dict, monkeypatch) -> None:
    registry = tmp_path / "versions.json"
    registry.write_text(
        json.dumps({"prompts": {"agents/chat.md": versions}}), encoding="utf-8"
    )
    monkeypatch.setattr(loader, "PROMPT_VERSIONS_FILE", registry)
    monkeypatch.setattr(loader.settings.prompt, "rollout_enabled", True)
    monkeypatch.setattr(loader.settings.prompt, "version_overrides", {})
    loader.clear_prompt_cache()


def test_prompt_release_routes_same_thread_to_same_version(
    tmp_path, monkeypatch
) -> None:
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "chat.md").write_text("stable", encoding="utf-8")
    (tmp_path / "agents" / "chat.v2.md").write_text("canary", encoding="utf-8")
    monkeypatch.setattr(loader, "PROMPT_ROOT", tmp_path)
    _write_registry(
        tmp_path,
        {
            "stable": "v1",
            "versions": {
                "v1": {"file": "agents/chat.md", "weight": 50},
                "v2": {"file": "agents/chat.v2.md", "weight": 50},
            },
        },
        monkeypatch,
    )

    with loader.prompt_release("thread-42"):
        first = loader.load_prompt("agents/chat.md")
        second = loader.load_prompt("agents/chat.md")
        metadata = loader.get_prompt_metadata()

    assert first == second
    expected = {
        "stable": {"version": "v1", "cohort": "stable"},
        "canary": {"version": "v2", "cohort": "canary"},
    }
    assert metadata["agents/chat.md"] == expected[first]


def test_prompt_version_override_supports_immediate_rollback(
    tmp_path, monkeypatch
) -> None:
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "chat.md").write_text("stable", encoding="utf-8")
    (tmp_path / "agents" / "chat.v2.md").write_text("canary", encoding="utf-8")
    monkeypatch.setattr(loader, "PROMPT_ROOT", tmp_path)
    _write_registry(
        tmp_path,
        {
            "stable": "v1",
            "versions": {
                "v1": {"file": "agents/chat.md", "weight": 0},
                "v2": {"file": "agents/chat.v2.md", "weight": 100},
            },
        },
        monkeypatch,
    )
    monkeypatch.setattr(
        loader.settings.prompt, "version_overrides", {"agents/chat.md": "v1"}
    )

    with loader.prompt_release("thread-42"):
        content = loader.load_prompt("agents/chat.md")
        metadata = loader.get_prompt_metadata()

    assert content == "stable"
    assert metadata["agents/chat.md"] == {
        "version": "v1",
        "cohort": "stable",
    }


def test_langchain_config_contains_selected_prompt_versions(
    tmp_path, monkeypatch
) -> None:
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "chat.md").write_text("stable", encoding="utf-8")
    monkeypatch.setattr(loader, "PROMPT_ROOT", tmp_path)
    _write_registry(
        tmp_path,
        {
            "stable": "v1",
            "versions": {"v1": {"file": "agents/chat.md", "weight": 100}},
        },
        monkeypatch,
    )

    with loader.prompt_release("thread-42"):
        loader.load_prompt("agents/chat.md")
        config = langchain_config()

    assert config["metadata"]["prompt_versions"] == {
        "agents/chat.md": {"version": "v1", "cohort": "stable"}
    }


def test_missing_canary_file_falls_back_to_stable(tmp_path, monkeypatch) -> None:
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "chat.md").write_text("stable", encoding="utf-8")
    monkeypatch.setattr(loader, "PROMPT_ROOT", tmp_path)
    _write_registry(
        tmp_path,
        {
            "stable": "v1",
            "versions": {
                "v1": {"file": "agents/chat.md", "weight": 0},
                "v2": {"file": "agents/missing.md", "weight": 100},
            },
        },
        monkeypatch,
    )

    with loader.prompt_release("thread-42"):
        content = loader.load_prompt("agents/chat.md")
        metadata = loader.get_prompt_metadata()

    assert content == "stable"
    assert metadata["agents/chat.md"] == {
        "version": "v1",
        "cohort": "stable",
    }


def test_disabled_rollout_always_uses_stable_version(tmp_path, monkeypatch) -> None:
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "chat.md").write_text("stable", encoding="utf-8")
    (tmp_path / "agents" / "chat.v2.md").write_text("canary", encoding="utf-8")
    monkeypatch.setattr(loader, "PROMPT_ROOT", tmp_path)
    _write_registry(
        tmp_path,
        {
            "stable": "v1",
            "versions": {
                "v1": {"file": "agents/chat.md", "weight": 0},
                "v2": {"file": "agents/chat.v2.md", "weight": 100},
            },
        },
        monkeypatch,
    )
    monkeypatch.setattr(loader.settings.prompt, "rollout_enabled", False)

    with loader.prompt_release("thread-42"):
        content = loader.load_prompt("agents/chat.md")

    assert content == "stable"
