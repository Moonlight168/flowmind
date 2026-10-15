"""Langfuse「自定义实验」webhook 接收端（Remote Dataset Run）。

Langfuse 在 UI 触发自定义实验时，会把数据集元信息（ID、名称）与自定义配置
POST 到本端点；本端点立即返回 202，并在后台拉取数据集、执行设计链路、把评分
写回为一个新的 Dataset Run。

安全前提：本端点不经过网关身份注入，故不挂载 require_auth；AI 服务端口不对
宿主机发布，仅同容器网络（flowmind-network）内的 Langfuse 可达，网络边界即
信任边界。若直接暴露端口，任何调用者都可触发实验执行。
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.domain.dto import ResponseVO
from app.infra.logger import log_api_endpoint, logger

router = APIRouter(prefix="/webhooks", tags=["webhook"])

DATASET_SECTION_KEY = "dataset"
DATASET_NAME_KEYS = ("datasetName", "dataset_name")
DATASET_ID_KEYS = ("datasetId", "dataset_id")
CASE_ID_KEYS = ("caseId", "case_id")
MAX_CONCURRENCY_KEYS = ("maxConcurrency", "max_concurrency")
CONFIG_SECTION_KEYS = (
    "config",
    "customConfig",
    "custom_config",
    "defaultConfig",
    "default_config",
)
RAW_PAYLOAD_LOG_LIMIT = 2000


class ExperimentRequest(BaseModel):
    """规范化后的实验触发参数（字段缺失时保持 None，由执行侧兜底）。"""

    dataset_name: str | None = None
    dataset_id: str | None = None
    case_id: str | None = None
    max_concurrency: int = 1


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _json_dict(value: Any) -> dict[str, Any]:
    """UI 中手填的配置可能是 JSON 字符串，尽量解析为字典。"""
    if isinstance(value, str):
        try:
            return _as_dict(json.loads(value))
        except (json.JSONDecodeError, ValueError):
            return {}
    return _as_dict(value)


def _first_str(source: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = source.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _first_int(source: dict[str, Any], keys: tuple[str, ...]) -> int | None:
    for key in keys:
        value = source.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())
    return None


def _config_section(body: dict[str, Any]) -> dict[str, Any]:
    for key in CONFIG_SECTION_KEYS:
        config = _json_dict(body.get(key))
        if config:
            return config
    return {}


def parse_experiment_request(payload: Any) -> ExperimentRequest:
    """兼容 Langfuse 未公开的 payload 结构，尽量提取数据集与运行参数。"""
    body = _as_dict(payload)
    dataset = _as_dict(body.get(DATASET_SECTION_KEY))
    config = _config_section(body)
    return ExperimentRequest(
        dataset_name=(
            _first_str(dataset, ("name",))
            or _first_str(body, DATASET_NAME_KEYS)
            or _first_str(config, DATASET_NAME_KEYS)
        ),
        dataset_id=_first_str(dataset, ("id",)) or _first_str(body, DATASET_ID_KEYS),
        case_id=_first_str(config, CASE_ID_KEYS) or _first_str(body, CASE_ID_KEYS),
        max_concurrency=(
            _first_int(config, MAX_CONCURRENCY_KEYS)
            or _first_int(body, MAX_CONCURRENCY_KEYS)
            or 1
        ),
    )


async def _read_payload(request: Request) -> Any:
    """读取原始 payload；为空或非 JSON 时记录并降级为空对象，保证触发不中断。"""
    raw = await request.body()
    if not raw:
        logger.warning("[实验 webhook] payload 为空")
        return {}
    text = raw.decode("utf-8", errors="replace")
    logger.info(f"[实验 webhook] 原始 payload={text[:RAW_PAYLOAD_LOG_LIMIT]}")
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        logger.error("[实验 webhook] payload 非合法 JSON, 已降级为空对象")
        return {}


def _run_experiment_task(experiment: ExperimentRequest) -> None:
    """后台执行实验；失败仅记录日志，不再回传（202 已发出）。"""
    from app.evaluation import runner

    dataset_name = experiment.dataset_name or "flow"
    try:
        runner.run_dataset_experiment(
            dataset_name,
            case_id=experiment.case_id,
            max_concurrency=experiment.max_concurrency,
            extra_metadata={
                "trigger": "langfuse_webhook",
                "dataset_id": experiment.dataset_id,
            },
        )
    except (RuntimeError, ValueError, OSError) as exc:
        logger.error(
            f"[实验 webhook] 后台执行失败 dataset={dataset_name}, "
            f"exception={type(exc).__name__}, detail={exc}"
        )


@router.post("/experiment", status_code=202)
@log_api_endpoint()
async def trigger_experiment(
    request: Request, background_tasks: BackgroundTasks
) -> JSONResponse:
    """接收 Langfuse 自定义实验触发，异步执行并立即返回 202。"""
    experiment = parse_experiment_request(await _read_payload(request))
    logger.info(
        f"[实验 webhook] 收到触发请求 dataset={experiment.dataset_name}, "
        f"dataset_id={experiment.dataset_id}, case={experiment.case_id}, "
        f"max_concurrency={experiment.max_concurrency}"
    )
    background_tasks.add_task(_run_experiment_task, experiment)
    body = ResponseVO[dict[str, Any]](
        code=202,
        message="accepted",
        data={
            "dataset_name": experiment.dataset_name,
            "case_id": experiment.case_id,
        },
    )
    return JSONResponse(status_code=202, content=body.model_dump())


__all__ = ["parse_experiment_request", "router"]
