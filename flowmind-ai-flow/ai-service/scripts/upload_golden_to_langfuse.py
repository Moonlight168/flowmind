"""把本地 evals/golden_dataset.jsonl 上传到 Langfuse dataset（幂等 upsert）。

与 run_golden_eval.py 解耦：只在 golden 数据集变更后手动执行，评估本身不再触发上传。
用法:
    python scripts/upload_golden_to_langfuse.py
    python scripts/upload_golden_to_langfuse.py --dataset-name flowmind-design-golden-v2
"""

from __future__ import annotations

import argparse
from pathlib import Path

from app.config.settings import settings
from app.evaluation.golden_dataset import load_golden_cases, sync_dataset
from app.infra.logger import logger
from app.infra.observability import get_client

DEFAULT_DATASET_PATH = Path(__file__).parents[1] / "evals" / "golden_dataset.jsonl"
DEFAULT_DATASET_NAME = "flowmind-design-golden-v1"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="上传本地 golden 数据集到 Langfuse（幂等 upsert）"
    )
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="本地 JSONL 数据集路径",
    )
    parser.add_argument(
        "--dataset-name", default=DEFAULT_DATASET_NAME, help="Langfuse 数据集名称"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not settings.observability.public_key or not settings.observability.secret_key:
        raise RuntimeError("缺少 Langfuse 密钥, 无法上传数据集")
    client = get_client()
    cases = load_golden_cases(args.dataset_path)
    items = sync_dataset(client, args.dataset_name, cases)
    client.flush()
    logger.info(f"[黄金集上传] {len(items)} 条 -> dataset={args.dataset_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
