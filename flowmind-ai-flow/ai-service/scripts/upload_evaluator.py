"""上传唯一的 Langfuse TypeScript 状态评估器。"""

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

EVALUATOR_PATH = (
    Path(__file__).parents[1] / "evals" / "evaluators" / "status_success.ts"
)
EVALUATOR_NAME = "flowmind-status-success"
EVALUATOR_LIST_LIMIT = 100


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="上传 FlowMind 状态评估器")
    parser.add_argument(
        "--dry-run", action="store_true", help="只打印计划, 不写 Langfuse"
    )
    return parser.parse_args(argv)


def _find_existing(client: Any) -> list[Any]:
    page = client.api.evaluators.list(limit=EVALUATOR_LIST_LIMIT)
    return [
        evaluator
        for evaluator in page.data
        if getattr(evaluator, "type", None) == "code"
        and evaluator.name == EVALUATOR_NAME
    ]


def sync_evaluator(client: Any, source_code: str) -> str:
    existing = _find_existing(client)
    if not existing:
        client.api.evaluators.create(
            request=CreateEvaluatorRequest_Code(
                name=EVALUATOR_NAME,
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
            name=EVALUATOR_NAME,
            source_code=source_code,
            source_code_language=CodeEvaluatorSourceCodeLanguage.TYPESCRIPT,
        ),
    )
    return "updated"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_code = EVALUATOR_PATH.read_text(encoding="utf-8")
    if args.dry_run:
        logger.info(f"[评估器上传] 计划 {EVALUATOR_NAME} ({len(source_code)} 字符)")
        return 0
    if not settings.observability.public_key or not settings.observability.secret_key:
        raise RuntimeError("缺少 Langfuse 密钥, 无法上传评估器")
    client = get_client()
    action = sync_evaluator(client, source_code)
    client.flush()
    logger.info(f"[评估器上传] {EVALUATOR_NAME} -> {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
