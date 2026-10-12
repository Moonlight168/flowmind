"""执行 FlowMind 黄金数据集评估并上报 Langfuse (从 dataset 拉取, 不触发上传).

前置: 先用 scripts/upload_golden_to_langfuse.py 把本地 evals/golden_dataset.jsonl
上传到 Langfuse dataset; 本脚本从 dataset 拉取用例执行, 避免 golden 未更新时重复上传.
"""

from __future__ import annotations

import argparse

from app.evaluation.runner import DEFAULT_DATASET_NAME, run_dataset_experiment


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line options for all-case or exact single-case execution."""
    parser = argparse.ArgumentParser(
        description="从 Langfuse dataset 拉取黄金用例并执行评估上报"
    )
    parser.add_argument("--case-id", help="只执行指定的稳定用例 ID")
    parser.add_argument(
        "--dataset-name", default=DEFAULT_DATASET_NAME, help="Langfuse 数据集名称"
    )
    parser.add_argument("--run-name", help="Langfuse Dataset Run 名称")
    parser.add_argument(
        "--max-concurrency", type=int, default=1, help="并发用例数, 默认串行"
    )
    args = parser.parse_args(argv)
    if args.max_concurrency < 1:
        parser.error("--max-concurrency 必须大于 0")
    return args


def main() -> int:
    """CLI entrypoint."""
    args = parse_args()
    run_dataset_experiment(
        args.dataset_name,
        case_id=args.case_id,
        run_name=args.run_name,
        max_concurrency=args.max_concurrency,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
