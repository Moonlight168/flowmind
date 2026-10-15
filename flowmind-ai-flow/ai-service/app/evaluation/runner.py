"""设计评测执行器：CLI 与 Langfuse webhook 共用同一运行链路。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import NAMESPACE_URL, uuid5

import requests
from langgraph.errors import EmptyInputError, GraphRecursionError, InvalidUpdateError

from app.config.settings import settings
from app.core.auth_context import set_auth_token
from app.core.exceptions import EXPECTED_RUNTIME_ERRORS, ErrorCode, FlowDesignException
from app.evaluation.datasets import (
    DatasetSpec,
    decode_dataset_value,
    resolve_dataset_spec,
)
from app.graph.design_graph import delete_design_thread, invoke_design_workflow
from app.infra.logger import logger
from app.infra.observability import get_client, observability_enabled

EXPERIMENT_NAME = "flowmind-design-evaluation"
EXPERIMENT_DESCRIPTION = "FlowMind AI 设计数据集评测"
UPLOAD_HINT = "scripts.upload_dataset.py"
EVALUATION_RUNTIME_ERRORS = (
    *EXPECTED_RUNTIME_ERRORS,
    requests.RequestException,
    EmptyInputError,
    GraphRecursionError,
    InvalidUpdateError,
    FlowDesignException,
)


def resolve_run_name(spec: DatasetSpec, case_id: str | None) -> str:
    """按数据集、范围和时间生成可追溯运行名称。"""
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"{spec.key}-{case_id or 'all'}-{timestamp}"


def case_id_of(item: Any) -> str:
    metadata = decode_dataset_value(item.metadata) or {}
    return str(metadata.get("case_id", ""))


def load_dataset_items(
    client: Any, spec: DatasetSpec, case_id: str | None = None
) -> list[Any]:
    """从固定 Langfuse 数据集取用例，可选精确筛选。"""
    items = list(client.get_dataset(spec.langfuse_name).items)
    if case_id:
        items = [item for item in items if case_id_of(item) == case_id]
        if not items:
            raise RuntimeError(f"数据集 {spec.key} 中不存在用例: {case_id}")
    if not items:
        raise RuntimeError(f"数据集 {spec.key} 为空，请先运行 {UPLOAD_HINT} {spec.key}")
    return items


def build_workflow_task(auth_token: str, spec: DatasetSpec) -> Any:
    """构建一次数据集运行任务，始终隔离会话和认证上下文。"""

    def run(item: Any, **_: Any) -> dict[str, Any]:
        metadata = decode_dataset_value(item.metadata) or {}
        case_id = str(metadata.get("case_id", "unknown"))
        thread_id = (
            f"eval-{spec.key}-{case_id}-{uuid5(NAMESPACE_URL, case_id).hex[:12]}"
        )
        set_auth_token(auth_token)
        try:
            payload = decode_dataset_value(item.input)
            turns = payload.get("turns") if isinstance(payload, dict) else None
            if not isinstance(turns, list) or not turns:
                raise ValueError("评测用例缺少 turns")
            latest_artifact: dict[str, Any] = {}
            turn_outputs: list[dict[str, Any]] = []
            for turn in turns:
                if not isinstance(turn, dict):
                    raise ValueError("评测用例 turn 必须是对象")
                current_artifact = turn.get("current_artifact") or latest_artifact
                output = invoke_design_workflow(
                    design_type=spec.design_type,
                    user_input=str(turn.get("user_input") or ""),
                    thread_id=thread_id,
                    current_form_data=current_artifact,
                    mode=spec.mode,
                )
                turn_outputs.append(output)
                if output.get("status") == "ready" and output.get("form_data"):
                    latest_artifact = output["form_data"]
            return {
                "case_id": case_id,
                "thread_id": thread_id,
                "turn_outputs": turn_outputs,
                **turn_outputs[-1],
            }
        except (*EVALUATION_RUNTIME_ERRORS, ValueError, TypeError) as exc:
            logger.error(
                f"[设计评测] 用例执行失败 case_id={case_id}, "
                f"exception={type(exc).__name__}"
            )
            return {
                "case_id": case_id,
                "thread_id": thread_id,
                "status": "error",
                "intent": "error",
                "form_data": None,
                "error_type": ErrorCode.EVALUATION_RUNTIME.value,
                "message": "评测执行失败，已隔离该用例",
                "failed_exception": type(exc).__name__,
            }
        finally:
            delete_design_thread(thread_id)
            set_auth_token(None)

    return run


def run_dataset_experiment(
    dataset: str,
    *,
    case_id: str | None = None,
    max_concurrency: int = 1,
    extra_metadata: dict[str, Any] | None = None,
) -> Any:
    """执行一个固定窗口的数据集，评分由 Langfuse TS Evaluator 负责。"""
    spec = resolve_dataset_spec(dataset)
    auth_token = settings.evaluation.auth_token
    if not auth_token:
        raise RuntimeError("缺少 FLOWMIND_AUTH_TOKEN，无法验证完整后端调用链")
    if not observability_enabled():
        raise RuntimeError("请先配置 Langfuse 密钥并启用链路监控")

    client = get_client()
    items = load_dataset_items(client, spec, case_id)
    run_name = resolve_run_name(spec, case_id)
    logger.info(f"[设计评测] 开始执行 run={run_name}, cases={len(items)}")
    try:
        result = client.run_experiment(
            name=EXPERIMENT_NAME,
            run_name=run_name,
            description=EXPERIMENT_DESCRIPTION,
            data=items,
            task=build_workflow_task(auth_token, spec),
            max_concurrency=max(max_concurrency, 1),
            metadata={
                "dataset_key": spec.key,
                "dataset_name": spec.langfuse_name,
                "selected_case_id": case_id,
                "case_count": len(items),
                **(extra_metadata or {}),
            },
        )
    finally:
        client.flush()
    logger.info(f"\n{result.format(include_item_results=True)}")
    if result.dataset_run_url:
        logger.info(f"[设计评测] Langfuse: {result.dataset_run_url}")
    return result


__all__ = [
    "EXPERIMENT_NAME",
    "build_workflow_task",
    "case_id_of",
    "load_dataset_items",
    "resolve_run_name",
    "run_dataset_experiment",
]
