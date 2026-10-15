"""评测数据集的注册、加载与 Langfuse 同步。"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any, Literal
from uuid import NAMESPACE_URL, uuid5

from pydantic import BaseModel, ConfigDict, Field, ValidationError

DATASET_ROOT = pathlib.Path(__file__).parents[2] / "evals" / "datasets"
DatasetKey = Literal["category", "basic", "form", "flow"]


@dataclass(frozen=True)
class DatasetSpec:
    """一个设计窗口对应的本地数据集及生产调用上下文。"""

    key: DatasetKey
    path: pathlib.Path
    langfuse_name: str
    design_type: Literal["flow_design", "form_design", "category_design"]
    mode: Literal["basic", "design"]


DATASETS: dict[DatasetKey, DatasetSpec] = {
    "category": DatasetSpec(
        "category",
        DATASET_ROOT / "category_design.jsonl",
        "flowmind-category-design-v1",
        "category_design",
        "design",
    ),
    "basic": DatasetSpec(
        "basic",
        DATASET_ROOT / "basic_info_design.jsonl",
        "flowmind-basic-info-design-v1",
        "flow_design",
        "basic",
    ),
    "form": DatasetSpec(
        "form",
        DATASET_ROOT / "form_design.jsonl",
        "flowmind-form-design-v1",
        "form_design",
        "design",
    ),
    "flow": DatasetSpec(
        "flow",
        DATASET_ROOT / "flow_model_design.jsonl",
        "flowmind-flow-model-design-v1",
        "flow_design",
        "design",
    ),
}


class EvaluationTurn(BaseModel):
    """一轮匿名化设计对话；窗口类型由所属数据集决定。"""

    model_config = ConfigDict(extra="forbid")
    user_input: str = Field(min_length=1)
    current_artifact: dict[str, Any] = Field(default_factory=dict)


class EvaluationCase(BaseModel):
    """一条可版本化的设计评测用例。"""

    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    source: Literal["real_anonymized", "curated"]
    turns: list[EvaluationTurn] = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)


def resolve_dataset_specs(target: str) -> list[DatasetSpec]:
    """把 CLI 参数解析为固定数据集，拒绝路径和任意 Langfuse 名称。"""
    if target == "all":
        return list(DATASETS.values())
    if target in DATASETS:
        return [DATASETS[target]]
    choices = ", ".join([*DATASETS, "all"])
    raise ValueError(f"未知数据集 '{target}'，可选值：{choices}")


def resolve_dataset_spec(value: str) -> DatasetSpec:
    """兼容 CLI key 与 Langfuse 回调传入的已登记数据集名称。"""
    if value in DATASETS:
        return DATASETS[value]
    for spec in DATASETS.values():
        if spec.langfuse_name == value:
            return spec
    choices = ", ".join([*DATASETS, "all"])
    raise ValueError(f"未知数据集 '{value}'，可选值：{choices}")


def load_cases(path: str | pathlib.Path) -> list[EvaluationCase]:
    """按行加载 JSONL，并保证用例 ID 在一个数据集中唯一。"""
    dataset_path = pathlib.Path(path)
    cases: list[EvaluationCase] = []
    seen_ids: set[str] = set()
    for line_number, raw_line in enumerate(
        dataset_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        try:
            case = EvaluationCase.model_validate_json(raw_line)
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            raise ValueError(
                f"{dataset_path} 第 {line_number} 行格式错误: {exc}"
            ) from exc
        if case.id in seen_ids:
            raise ValueError(
                f"{dataset_path} 第 {line_number} 行存在重复用例 ID: {case.id}"
            )
        seen_ids.add(case.id)
        cases.append(case)
    if not cases:
        raise ValueError(f"评测数据集为空: {dataset_path}")
    return cases


def inject_window_context(case: EvaluationCase, spec: DatasetSpec) -> dict[str, Any]:
    """仅在执行时补生产链路参数，避免每条 JSONL 重复窗口元数据。"""
    return {
        "turns": [
            {
                "user_input": turn.user_input,
                "current_artifact": turn.current_artifact,
                "design_type": spec.design_type,
                "mode": spec.mode,
            }
            for turn in case.turns
        ]
    }


def sync_dataset(
    client: Any, spec: DatasetSpec, cases: list[EvaluationCase]
) -> list[Any]:
    """幂等同步一个窗口的数据集到 Langfuse。"""
    client.create_dataset(
        name=spec.langfuse_name,
        description=f"FlowMind {spec.key} 设计评测数据集",
        metadata={"schema_version": 3, "dataset_key": spec.key},
    )
    _delete_stale_managed_items(client, spec, cases)
    return [
        client.create_dataset_item(
            id=str(uuid5(NAMESPACE_URL, f"{spec.langfuse_name}:{case.id}")),
            dataset_name=spec.langfuse_name,
            input=inject_window_context(case, spec),
            metadata={
                "case_id": case.id,
                "dataset_key": spec.key,
                "source": case.source,
                "tags": case.tags,
                "turn_count": len(case.turns),
            },
        )
        for case in cases
    ]


def _delete_stale_managed_items(
    client: Any, spec: DatasetSpec, cases: list[EvaluationCase]
) -> None:
    current_ids = {case.id for case in cases}
    for item in client.get_dataset(spec.langfuse_name).items:
        metadata = decode_dataset_value(item.metadata) or {}
        case_id = str(metadata.get("case_id", ""))
        managed_id = str(uuid5(NAMESPACE_URL, f"{spec.langfuse_name}:{case_id}"))
        if case_id and item.id == managed_id and case_id not in current_ids:
            client.api.dataset_items.delete(item.id)


def decode_dataset_value(value: Any) -> Any:
    """兼容 Langfuse SDK 将 JSON 字段反序列化为字符串的情况。"""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return value
    return value


__all__ = [
    "DATASETS",
    "DatasetSpec",
    "EvaluationCase",
    "EvaluationTurn",
    "decode_dataset_value",
    "inject_window_context",
    "load_cases",
    "resolve_dataset_spec",
    "resolve_dataset_specs",
    "sync_dataset",
]
