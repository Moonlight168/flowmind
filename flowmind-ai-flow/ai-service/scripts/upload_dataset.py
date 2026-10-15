"""同步指定设计窗口的数据集到 Langfuse。"""

from __future__ import annotations

import argparse

from app.config.settings import settings
from app.evaluation.datasets import load_cases, resolve_dataset_specs, sync_dataset
from app.infra.logger import logger
from app.infra.observability import get_client


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="上传 FlowMind 设计评测数据集")
    parser.add_argument(
        "dataset",
        nargs="?",
        default="all",
        choices=["category", "basic", "form", "flow", "all"],
        help="设计窗口, 默认 all",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not settings.observability.public_key or not settings.observability.secret_key:
        raise RuntimeError("缺少 Langfuse 密钥, 无法上传数据集")
    client = get_client()
    for spec in resolve_dataset_specs(args.dataset):
        cases = load_cases(spec.path)
        items = sync_dataset(client, spec, cases)
        logger.info(f"[数据集上传] {spec.key}: {len(items)} 条 -> {spec.langfuse_name}")
    client.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
