"""
FlowMind 智能流程设计服务 - Markdown 提示词加载器
"""

import hashlib
import json
import re
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.infra.logger import logger

PROMPT_ROOT = Path(__file__).parent
PROMPT_VERSIONS_FILE = PROMPT_ROOT / "versions.json"
VARIABLE_PATTERN = re.compile(r"(?<!\$)\{([A-Za-z_][A-Za-z0-9_]*)\}")
_release_key: ContextVar[str | None] = ContextVar("prompt_release_key", default=None)
_prompt_metadata: ContextVar[dict[str, dict[str, str]] | None] = ContextVar(
    "prompt_metadata", default=None
)


@dataclass(frozen=True)
class PromptSelection:
    """一次提示词版本选择结果。"""

    path: str
    version: str
    cohort: str


@contextmanager
def prompt_release(release_key: str) -> Iterator[None]:
    """在请求范围内按稳定 key 选择提示词版本并收集监控元数据。"""
    key_token = _release_key.set(release_key)
    metadata_token = _prompt_metadata.set({})
    try:
        yield
    finally:
        _prompt_metadata.reset(metadata_token)
        _release_key.reset(key_token)


def get_prompt_metadata() -> dict[str, dict[str, str]]:
    """返回当前请求实际使用的提示词版本。"""
    return dict(_prompt_metadata.get() or {})


def load_prompt(relative_path: str) -> str:
    """按当前请求的灰度版本读取 Markdown 提示词。"""
    selection = resolve_prompt_version(relative_path, _release_key.get())
    try:
        content = _read_prompt(PROMPT_ROOT, selection.path)
    except FileNotFoundError:
        stable = _stable_selection(relative_path)
        if selection == stable:
            raise
        logger.warning(
            f"[prompt] 灰度版本文件不存在，回退稳定版: "
            f"path={relative_path}, version={selection.version}"
        )
        selection = stable
        content = _read_prompt(PROMPT_ROOT, selection.path)
    metadata = _prompt_metadata.get()
    if metadata is not None:
        metadata[relative_path] = {
            "version": selection.version,
            "cohort": selection.cohort,
        }
    return content


def resolve_prompt_version(
    relative_path: str, release_key: str | None
) -> PromptSelection:
    """解析强制版本或按 release_key 稳定分配灰度版本。"""
    config = _prompt_config(relative_path)
    stable_version = str(config.get("stable") or "v1")
    versions = config.get("versions")
    if not isinstance(versions, dict) or not versions:
        return PromptSelection(relative_path, stable_version, "stable")

    forced = _forced_selection(relative_path, versions, stable_version)
    if forced is not None:
        return forced
    if not settings.prompt.rollout_enabled or not release_key:
        return _selection(relative_path, versions, stable_version, stable_version)

    weighted = _weighted_versions(versions)
    if not weighted:
        return _selection(relative_path, versions, stable_version, stable_version)
    bucket = _release_bucket(f"{release_key}:{relative_path}")
    cumulative = 0.0
    for version, weight in weighted:
        cumulative += weight
        if bucket < cumulative:
            return _selection(relative_path, versions, version, stable_version)
    return _selection(relative_path, versions, weighted[-1][0], stable_version)


def clear_prompt_cache() -> None:
    """清空版本配置和提示词文件缓存，供测试或配置重载使用。"""
    _read_prompt.cache_clear()
    _load_registry.cache_clear()


@cache
def _read_prompt(root: Path, relative_path: str) -> str:
    path = (root / relative_path).resolve()
    if path.suffix.lower() != ".md" or not path.is_relative_to(root.resolve()):
        raise ValueError(f"非法提示词路径: {relative_path}")
    return path.read_text(encoding="utf-8").strip()


@cache
def _load_registry(registry_path: Path) -> dict[str, Any]:
    if not registry_path.exists():
        return {}
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning(f"[prompt] 版本配置读取失败，使用稳定版: {exc}")
        return {}
    prompts = data.get("prompts") if isinstance(data, dict) else None
    return prompts if isinstance(prompts, dict) else {}


def _prompt_config(relative_path: str) -> dict[str, Any]:
    config = _load_registry(PROMPT_VERSIONS_FILE).get(relative_path)
    return config if isinstance(config, dict) else {}


def _forced_selection(
    relative_path: str, versions: dict[str, Any], stable_version: str
) -> PromptSelection | None:
    override = settings.prompt.version_overrides.get(relative_path)
    if override is None:
        return None
    if override in versions:
        return _selection(relative_path, versions, override, stable_version)
    logger.warning(
        f"[prompt] 强制版本不存在，回退稳定版: path={relative_path}, version={override}"
    )
    return _selection(relative_path, versions, stable_version, stable_version)


def _stable_selection(relative_path: str) -> PromptSelection:
    config = _prompt_config(relative_path)
    stable_version = str(config.get("stable") or "v1")
    versions = config.get("versions")
    if isinstance(versions, dict) and versions:
        return _selection(relative_path, versions, stable_version, stable_version)
    return PromptSelection(relative_path, stable_version, "stable")


def _selection(
    relative_path: str,
    versions: dict[str, Any],
    version: str,
    stable_version: str,
) -> PromptSelection:
    entry = versions.get(version)
    path = entry.get("file") if isinstance(entry, dict) else None
    return PromptSelection(
        str(path or relative_path),
        version,
        "stable" if version == stable_version else "canary",
    )


def _weighted_versions(versions: dict[str, Any]) -> list[tuple[str, float]]:
    weights: list[tuple[str, float]] = []
    for version, entry in versions.items():
        if not isinstance(entry, dict):
            continue
        try:
            weight = max(0.0, float(entry.get("weight", 0)))
        except (TypeError, ValueError):
            continue
        if weight > 0:
            weights.append((str(version), weight))
    total = sum(weight for _, weight in weights)
    return [(version, weight / total) for version, weight in weights] if total else []


def _release_bucket(seed: str) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def render_prompt(relative_path: str, variables: dict[str, Any]) -> str:
    """替换显式变量，保留提示词中的 JSON 与表达式花括号。"""
    content = load_prompt(relative_path)
    return VARIABLE_PATTERN.sub(
        lambda match: str(variables.get(match.group(1), match.group(0))),
        content,
    )
