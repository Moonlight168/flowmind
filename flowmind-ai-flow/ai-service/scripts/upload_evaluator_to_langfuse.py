"""把本地 TypeScript 契约评估器上传到 Langfuse（幂等）。

命名规则：固定评估器名，源码内容决定是否变更。
- 不存在同名 code evaluator → 新建（version 1）
- 存在且源码一致 → 跳过，不产生新版本
- 存在但源码不同 → 更新，生成新版本

注意：自托管 Langfuse 的 code evaluator 需要有可用的 code evaluator
dispatcher 才会真正执行；未配置时评估器仍可创建，但不会运行。

用法：
    poetry run python -m scripts.upload_evaluator_to_langfuse
    poetry run python -m scripts.upload_evaluator_to_langfuse --dry-run
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from langfuse.api import (
    CodeEvaluatorSourceCodeLanguage,
    CreateEvaluatorRequest_Code,
    UpdateCodeEvaluatorRequest,
)

from app.config.settings import settings
from app.infra.logger import logger
from app.infra.observability import get_client

DEFAULT_EVALUATOR_PATH = (
    Path(__file__).parents[1] / "evals" / "evaluators" / "design_contract.ts"
)
DEFAULT_EVALUATOR_NAME = "flowmind-design-contract"
EVALUATOR_LIST_LIMIT = 100


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="上传本地 TypeScript 契约评估器到 Langfuse（幂等）"
    )
    parser.add_argument(
        "--evaluator-path",
        type=Path,
        default=DEFAULT_EVALUATOR_PATH,
        help="本地评估器源码路径",
    )
    parser.add_argument(
        "--name", default=DEFAULT_EVALUATOR_NAME, help="Langfuse 评估器名称"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="只打印计划，不写 Langfuse"
    )
    return parser.parse_args(argv)


def _find_existing(client: Any, name: str) -> list[Any]:
    """返回同名 code evaluator，按创建时间倒序（Langfuse 默认 newest-first）。"""
    page = client.api.evaluators.list(limit=EVALUATOR_LIST_LIMIT)
    return [
        evaluator
        for evaluator in page.data
        if getattr(evaluator, "type", None) == "code" and evaluator.name == name
    ]


def sync_evaluator(client: Any, name: str, source_code: str) -> str:
    existing = _find_existing(client, name)
    if not existing:
        client.api.evaluators.create(
            request=CreateEvaluatorRequest_Code(
                name=name,
                source_code=source_code,
                source_code_language=CodeEvaluatorSourceCodeLanguage.TYPESCRIPT,
            )
        )
        return "created"
    latest = existing[0]
    if latest.source_code == source_code:
        return "unchanged"
    client.api.evaluators.update(
        latest.id,
        request=UpdateCodeEvaluatorRequest(
            name=name,
            source_code=source_code,
            source_code_language=CodeEvaluatorSourceCodeLanguage.TYPESCRIPT,
        ),
    )
    return "updated"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_code = args.evaluator_path.read_text(encoding="utf-8")
    if args.dry_run:
        logger.info(
            f"[评估器上传] 计划 {args.name} ({len(source_code)} 字符) 语言=TYPESCRIPT"
        )
        return 0
    if not settings.observability.public_key or not settings.observability.secret_key:
        raise RuntimeError("缺少 Langfuse 密钥, 无法上传评估器")
    client = get_client()
    action = sync_evaluator(client, args.name, source_code)
    client.flush()
    logger.info(f"[评估器上传] {args.name} -> {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
