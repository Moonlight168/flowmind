"""Synchronize local Markdown prompts to Langfuse idempotently.

The logical path without `.md` is used as the prompt name. Stable versions use
the `production` label, while other versions use `canary`.

Usage:
    poetry run python -m scripts.upload_prompts
    poetry run python -m scripts.upload_prompts --dry-run
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from app.config.settings import settings
from app.infra.logger import logger
from app.infra.observability import get_client
from app.prompts.loader import PROMPT_ROOT, PROMPT_VERSIONS_FILE

if TYPE_CHECKING:
    from pathlib import Path

PRODUCTION_LABEL = "production"
CANARY_LABEL = "canary"
DEFAULT_STABLE_VERSION = "v1"
PROMPT_NAME_SUFFIX = ".md"
PROMPT_LIST_LIMIT = 100


@dataclass(frozen=True)
class PromptVersionUpload:
    """单个提示词版本的待上传内容。"""

    name: str
    version: str
    label: str
    content: str


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="上传本地 Markdown 提示词到 Langfuse (幂等)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="只打印计划, 不写 Langfuse"
    )
    return parser.parse_args(argv)


def build_uploads(registry_path: Path) -> list[PromptVersionUpload]:
    """按 versions.json 展开出所有待上传的提示词版本。"""
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    prompts: dict[str, Any] = registry.get("prompts", {})
    uploads: list[PromptVersionUpload] = []
    for logical_path, config in prompts.items():
        name = logical_path.removesuffix(PROMPT_NAME_SUFFIX)
        stable = str(config.get("stable") or DEFAULT_STABLE_VERSION)
        for version, entry in config.get("versions", {}).items():
            content = (PROMPT_ROOT / entry["file"]).read_text(encoding="utf-8").strip()
            label = PRODUCTION_LABEL if version == stable else CANARY_LABEL
            uploads.append(PromptVersionUpload(name, str(version), label, content))
    return uploads


def _group_by_name(
    uploads: list[PromptVersionUpload],
) -> dict[str, list[PromptVersionUpload]]:
    groups: dict[str, list[PromptVersionUpload]] = {}
    for upload in uploads:
        groups.setdefault(upload.name, []).append(upload)
    return groups


def _existing_content_versions(client: Any, name: str) -> dict[str, int]:
    """Return a content-to-version index for idempotent prompt uploads.

    Prompt names containing `/` must be URL encoded before the single-prompt
    API call; otherwise Langfuse interprets them as nested URL paths.
    """
    meta = client.api.prompts.list(name=name, limit=PROMPT_LIST_LIMIT)
    if not meta.data:
        return {}
    encoded_name = quote(name, safe="")
    index: dict[str, int] = {}
    for version in meta.data[0].versions:
        prompt = client.api.prompts.get(encoded_name, version=version)
        if isinstance(prompt.prompt, str):
            index[prompt.prompt] = version
    return index


def _sync_version(
    client: Any, upload: PromptVersionUpload, existing: dict[str, int]
) -> str:
    version_number = existing.get(upload.content)
    if version_number is None:
        client.create_prompt(
            name=upload.name,
            prompt=upload.content,
            type="text",
            labels=[upload.label],
            commit_message=f"upload {upload.version} from repo",
        )
        return "created"
    client.update_prompt(
        name=upload.name, version=version_number, new_labels=[upload.label]
    )
    return "relabeled"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    uploads = build_uploads(PROMPT_VERSIONS_FILE)
    if args.dry_run:
        for upload in uploads:
            logger.info(
                f"[提示词上传] 计划 {upload.name} ({upload.version}) -> {upload.label}"
            )
        return 0

    if not settings.observability.public_key or not settings.observability.secret_key:
        raise RuntimeError("缺少 Langfuse 密钥, 无法上传提示词")
    client = get_client()
    created = relabeled = 0
    for name, versions in _group_by_name(uploads).items():
        existing = _existing_content_versions(client, name)
        for upload in versions:
            action = _sync_version(client, upload, existing)
            if action == "created":
                created += 1
            else:
                relabeled += 1
    client.flush()
    logger.info(
        f"[提示词上传] 共 {len(uploads)} 个版本, 新建 {created}, 修正标签 {relabeled}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
