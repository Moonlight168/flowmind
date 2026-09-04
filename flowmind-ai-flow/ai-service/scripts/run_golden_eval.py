"""执行 FlowMind 黄金数据集评估并上报 Langfuse（从 dataset 拉取，不触发上传）。

前置：先用 scripts/upload_golden_to_langfuse.py 把本地 evals/golden_dataset.jsonl
上传到 Langfuse dataset；本脚本从 dataset 拉取用例执行，避免 golden 未更新时重复上传。
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from typing import Any

from app.config.settings import settings
from app.evaluation.golden_dataset import build_workflow_task, evaluate_contract
from app.infra.logger import logger
from app.infra.observability import get_client, observability_enabled

DEFAULT_DATASET_NAME = "flowmind-design-golden-v1"


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


def _case_id(item: Any) -> str:
    metadata = item.metadata or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except (json.JSONDecodeError, ValueError):
            metadata = {}
    return str(metadata.get("case_id", ""))


def run(args: argparse.Namespace) -> Any:
    """Pull dataset items, execute the production workflow, and return the run."""
    auth_token = settings.evaluation.auth_token
    if not auth_token:
        raise RuntimeError("缺少 FLOWMIND_AUTH_TOKEN, 无法验证完整后端调用链")
    if not observability_enabled():
        raise RuntimeError("请先配置 Langfuse 密钥并启用链路监控")

    client = get_client()
    items = list(client.get_dataset(args.dataset_name).items)
    if args.case_id:
        items = [item for item in items if _case_id(item) == args.case_id]
        if not items:
            raise RuntimeError(
                f"Langfuse dataset={args.dataset_name} 中不存在用例: {args.case_id}"
            )
    if not items:
        raise RuntimeError(
            f"Langfuse dataset={args.dataset_name} 为空，请先运行 "
            "scripts/upload_golden_to_langfuse.py 上传本地 golden 数据集"
        )

    run_name = args.run_name or _default_run_name(args.case_id)
    logger.info(f"[黄金集评估] 开始执行 run={run_name}, cases={len(items)}")
    try:
        result = _execute_experiment(client, args, items, auth_token, run_name)
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
