"""黄金数据集实验执行核心：CLI 脚本与实验 webhook 共用同一实现。

从 Langfuse dataset 拉取用例、执行生产设计链路、把确定性契约评分写回为一个
新的 Dataset Run。调用方只负责提供运行参数，不再各自复制这段编排逻辑。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.config.settings import settings
from app.evaluation.golden_dataset import (
    build_workflow_task,
    decode_dataset_value,
    evaluate_contract,
)
from app.infra.logger import logger
from app.infra.observability import get_client, observability_enabled

DEFAULT_DATASET_NAME = "flowmind-design-golden-v1"
EXPERIMENT_NAME = "flowmind-design-contract"
EXPERIMENT_DESCRIPTION = "FlowMind 设计链路黄金数据集契约评估"
UPLOAD_HINT = "scripts/upload_golden_to_langfuse.py"


def resolve_run_name(case_id: str | None, run_name: str | None = None) -> str:
    """未显式指定 run 名称时，按用例范围与时间戳生成可追溯名称。"""
    if run_name:
        return run_name
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"golden-{case_id or 'all'}-{timestamp}"


def case_id_of(item: Any) -> str:
    """从数据集项 metadata 读取稳定用例 ID。"""
    metadata = decode_dataset_value(item.metadata) or {}
    return str(metadata.get("case_id", ""))


def load_dataset_items(
    client: Any, dataset_name: str, case_id: str | None = None
) -> list[Any]:
    """从 Langfuse 拉取数据集项，可选按用例 ID 精确过滤。"""
    items = list(client.get_dataset(dataset_name).items)
    if case_id:
        items = [item for item in items if case_id_of(item) == case_id]
        if not items:
            raise RuntimeError(
                f"Langfuse dataset={dataset_name} 中不存在用例: {case_id}"
            )
    if not items:
        raise RuntimeError(
            f"Langfuse dataset={dataset_name} 为空, 请先运行 {UPLOAD_HINT} "
            "上传本地 golden 数据集"
        )
    return items


def run_dataset_experiment(
    dataset_name: str = DEFAULT_DATASET_NAME,
    *,
    case_id: str | None = None,
    run_name: str | None = None,
    max_concurrency: int = 1,
    extra_metadata: dict[str, Any] | None = None,
) -> Any:
    """执行一次完整实验并上报 Langfuse，返回 run 结果对象。"""
    auth_token = settings.evaluation.auth_token
    if not auth_token:
        raise RuntimeError("缺少 FLOWMIND_AUTH_TOKEN, 无法验证完整后端调用链")
    if not observability_enabled():
        raise RuntimeError("请先配置 Langfuse 密钥并启用链路监控")

    client = get_client()
    items = load_dataset_items(client, dataset_name, case_id)
    resolved_run_name = resolve_run_name(case_id, run_name)
    logger.info(f"[黄金集评估] 开始执行 run={resolved_run_name}, cases={len(items)}")
    try:
        result = client.run_experiment(
            name=EXPERIMENT_NAME,
            run_name=resolved_run_name,
            description=EXPERIMENT_DESCRIPTION,
            data=items,
            task=build_workflow_task(auth_token),
            evaluators=[evaluate_contract],
            max_concurrency=max(max_concurrency, 1),
            metadata={
                "dataset_name": dataset_name,
                "selected_case_id": case_id,
                "case_count": len(items),
                **(extra_metadata or {}),
            },
        )
    finally:
        client.flush()
    logger.info(f"\n{result.format(include_item_results=True)}")
    if result.dataset_run_url:
        logger.info(f"[黄金集评估] Langfuse: {result.dataset_run_url}")
    return result


__all__ = [
    "DEFAULT_DATASET_NAME",
    "EXPERIMENT_NAME",
    "case_id_of",
    "load_dataset_items",
    "resolve_run_name",
    "run_dataset_experiment",
]
