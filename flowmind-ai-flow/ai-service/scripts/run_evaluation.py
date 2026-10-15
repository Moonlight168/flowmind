"""从 Langfuse 执行指定设计窗口的评测数据集。"""

from __future__ import annotations

import argparse

from app.evaluation.datasets import resolve_dataset_specs
from app.evaluation.runner import run_dataset_experiment


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 FlowMind AI 设计评测")
    parser.add_argument(
        "dataset",
        nargs="?",
        default="all",
        choices=["category", "basic", "form", "flow", "all"],
        help="设计窗口, 默认 all",
    )
    parser.add_argument("--case-id", help="只运行指定稳定用例 ID")
    parser.add_argument(
        "--max-concurrency", type=int, default=1, help="并发用例数, 默认串行"
    )
    args = parser.parse_args(argv)
    if args.max_concurrency < 1:
        parser.error("--max-concurrency 必须大于 0")
    if args.dataset == "all" and args.case_id:
        parser.error("--case-id 需要指定单个数据集")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    for spec in resolve_dataset_specs(args.dataset):
        run_dataset_experiment(
            spec.key,
            case_id=args.case_id,
            max_concurrency=args.max_concurrency,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
