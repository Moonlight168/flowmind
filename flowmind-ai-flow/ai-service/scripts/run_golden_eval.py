"""Run FlowMind golden dataset evaluations and report scores to Langfuse."""

from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from langfuse import get_client

from app.evaluation.golden_dataset import (
    build_workflow_task,
    evaluate_contract,
    load_golden_cases,
    select_cases,
    sync_dataset,
)
from app.infra.logger import logger
from app.infra.observability import observability_enabled

DEFAULT_DATASET_PATH = Path(__file__).parents[1] / "evals" / "golden_dataset.jsonl"
DEFAULT_DATASET_NAME = "flowmind-design-golden-v1"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line options for all-case or exact single-case execution."""
    parser = argparse.ArgumentParser(
        description="执行 FlowMind 黄金数据集并将评估结果上报 Langfuse"
    )
    parser.add_argument("--case-id", help="只执行指定的稳定用例 ID")
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="JSONL 数据集路径",
    )
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


def run(args: argparse.Namespace) -> Any:
    """Sync selected cases, execute the production workflow, and return the run."""
    auth_token = os.getenv("FLOWMIND_AUTH_TOKEN")
    if not auth_token:
        raise RuntimeError("缺少 FLOWMIND_AUTH_TOKEN, 无法验证完整后端调用链")
    if not observability_enabled():
        raise RuntimeError("请先配置 Langfuse 密钥并启用链路监控")

    cases = select_cases(load_golden_cases(args.dataset_path), args.case_id)
    client = get_client()
    dataset_items = sync_dataset(client, args.dataset_name, cases)
    run_name = args.run_name or _default_run_name(args.case_id)
    logger.info(f"[黄金集评估] 开始执行 run={run_name}, cases={len(dataset_items)}")
    try:
        result = _execute_experiment(client, args, dataset_items, auth_token, run_name)
    finally:
        client.flush()
    logger.info(f"\n{result.format(include_item_results=True)}")
    if result.dataset_run_url:
        logger.info(f"[黄金集评估] Langfuse: {result.dataset_run_url}")
    return result


def _execute_experiment(
    client: Any,
    args: argparse.Namespace,
    dataset_items: list[Any],
    auth_token: str,
    run_name: str,
) -> Any:
    return client.run_experiment(
        name="flowmind-design-contract",
        run_name=run_name,
        description="FlowMind 设计链路黄金数据集契约评估",
        data=dataset_items,
        task=build_workflow_task(auth_token),
        evaluators=[evaluate_contract],
        max_concurrency=args.max_concurrency,
        metadata={
            "dataset_name": args.dataset_name,
            "selected_case_id": args.case_id,
            "case_count": len(dataset_items),
        },
    )


def _default_run_name(case_id: str | None) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    scope = case_id or "all"
    return f"golden-{scope}-{timestamp}"


def main() -> int:
    """CLI entrypoint."""
    run(parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
