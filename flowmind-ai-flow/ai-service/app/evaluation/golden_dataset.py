"""FlowMind 黄金数据集加载、执行与确定性契约评分。"""

from __future__ import annotations

import json
import pathlib
import typing
from typing import Any, Literal
from uuid import NAMESPACE_URL, uuid4, uuid5

import httpx
import requests
from langfuse import Evaluation
from langgraph.errors import (
    EmptyInputError,
    GraphRecursionError,
    InvalidUpdateError,
    TaskNotFound,
)
from openai import OpenAIError
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from redis.exceptions import RedisError

from app.core.auth_context import set_auth_token
from app.core.exceptions import FlowDesignException
from app.graph.workflows.design_workflow import (
    delete_design_thread,
    invoke_design_workflow,
)
from app.infra.logger import logger

EVALUATION_RUNTIME_ERRORS = (
    OpenAIError,
    httpx.HTTPError,
    requests.RequestException,
    RedisError,
    ValidationError,
    EmptyInputError,
    GraphRecursionError,
    InvalidUpdateError,
    TaskNotFound,
    FlowDesignException,
)


class GoldenInput(BaseModel):
    """真实设计工作流所需的输入。"""

    model_config = ConfigDict(extra="forbid")

    design_type: Literal["flow_design", "form_design", "category_design"]
    user_input: str = Field(min_length=1)
    current_form_data: dict[str, Any] = Field(default_factory=dict)
    mode: Literal["basic", "design"] = "design"


class GoldenFallbackOutput(BaseModel):
    """主目标失败时仍必须满足的用户可见契约。"""

    model_config = ConfigDict(extra="forbid")

    error_types: list[str] = Field(min_length=1)
    message_required: bool = True
    message_contains: list[str] = Field(default_factory=list)


class GoldenExpectedOutput(BaseModel):
    """跨模型稳定的输出契约，不约束自然语言细节。"""

    model_config = ConfigDict(extra="forbid")

    intent: Literal["success", "clarification", "error"]
    required_paths: list[str] = Field(default_factory=list)
    min_counts: dict[str, int] = Field(default_factory=dict)
    required_node_types: list[str] = Field(default_factory=list)
    required_widget_types: list[str] = Field(default_factory=list)
    message_contains: list[str] = Field(default_factory=list)
    error_type: str | None = None
    fallback_output: GoldenFallbackOutput | None = None


class GoldenCase(BaseModel):
    """一条可版本化的黄金用例。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    category: str = Field(min_length=1)
    input: GoldenInput
    expected_output: GoldenExpectedOutput
    metadata: dict[str, Any] = Field(default_factory=dict)


def load_golden_cases(path: str | pathlib.Path) -> list[GoldenCase]:
    """按行加载 JSONL，错误信息保留行号便于修正。"""
    path = pathlib.Path(path)
    cases: list[GoldenCase] = []
    seen_ids: set[str] = set()
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        case = _parse_case(raw_line, path, line_number)
        if case.id in seen_ids:
            raise ValueError(f"{path} 第 {line_number} 行存在重复用例 ID: {case.id}")
        seen_ids.add(case.id)
        cases.append(case)
    if not cases:
        raise ValueError(f"黄金数据集为空: {path}")
    return cases


def _parse_case(raw_line: str, path: pathlib.Path, line_number: int) -> GoldenCase:
    try:
        return GoldenCase.model_validate_json(raw_line)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise ValueError(f"{path} 第 {line_number} 行格式错误: {exc}") from exc


def select_cases(cases: list[GoldenCase], case_id: str | None) -> list[GoldenCase]:
    """精确选择单条用例；未指定时返回全部。"""
    if case_id is None:
        return cases
    selected = [case for case in cases if case.id == case_id]
    if not selected:
        raise ValueError(f"黄金数据集中不存在用例: {case_id}")
    return selected


def sync_dataset(client: Any, dataset_name: str, cases: list[GoldenCase]) -> list[Any]:
    """幂等同步用例到 Langfuse，并返回可直接执行的数据集项。"""
    client.create_dataset(
        name=dataset_name,
        description="FlowMind 设计链路黄金数据集",
        metadata={"schema_version": 1, "service": "flowmind-ai-flow"},
        input_schema=GoldenInput.model_json_schema(),
        expected_output_schema=GoldenExpectedOutput.model_json_schema(),
    )
    return [
        client.create_dataset_item(
            id=str(uuid5(NAMESPACE_URL, f"{dataset_name}:{case.id}")),
            dataset_name=dataset_name,
            input=case.input.model_dump(mode="json"),
            expected_output=case.expected_output.model_dump(mode="json"),
            metadata={
                **case.metadata,
                "case_id": case.id,
                "category": case.category,
            },
        )
        for case in cases
    ]


def build_workflow_task(auth_token: str) -> typing.Callable[..., dict[str, Any]]:
    """构建 Langfuse 实验 task，逐条隔离运行时失败。"""

    def run(item: Any, **_: Any) -> dict[str, Any]:
        case_id = str((item.metadata or {}).get("case_id", "unknown"))
        thread_id = f"eval-{case_id}-{uuid4().hex[:12]}"
        set_auth_token(auth_token)
        try:
            case_input = GoldenInput.model_validate(item.input)
            output = invoke_design_workflow(
                **case_input.model_dump(), thread_id=thread_id
            )
            return {"case_id": case_id, "thread_id": thread_id, **output}
        except EVALUATION_RUNTIME_ERRORS as exc:
            return _runtime_failure_output(case_id, thread_id, exc)
        finally:
            delete_design_thread(thread_id)
            set_auth_token(None)

    return run


def _runtime_failure_output(
    case_id: str, thread_id: str, exc: BaseException
) -> dict[str, Any]:
    exception_name = type(exc).__name__
    logger.error(
        f"[黄金集评估] 用例执行失败 case_id={case_id}, exception={exception_name}"
    )
    return {
        "case_id": case_id,
        "thread_id": thread_id,
        "intent": "error",
        "error_type": "evaluation_runtime",
        "message": "评估执行失败，已隔离该用例",
        "failed_exception": exception_name,
    }


def evaluate_contract(
    *, output: dict[str, Any], expected_output: dict[str, Any], **_: Any
) -> list[Evaluation]:
    """评估稳定输出契约，所有分数均可直接上报 Langfuse。"""
    expected = GoldenExpectedOutput.model_validate(expected_output)
    scores = [
        _evaluation(
            "intent_match",
            output.get("intent") == expected.intent,
            f"期望 intent={expected.intent}",
        )
    ]
    _append_path_scores(scores, output, expected)
    _append_coverage_scores(scores, output, expected)
    _append_fallback_score(scores, output, expected)
    scores.append(
        Evaluation(
            name="contract_score",
            value=sum(float(score.value) for score in scores) / len(scores),
            comment="所有稳定契约指标的平均分",
        )
    )
    return scores


def _append_path_scores(
    scores: list[Evaluation], output: dict[str, Any], expected: GoldenExpectedOutput
) -> None:
    if expected.required_paths:
        matched = sum(
            _resolve_path(output, path) is not None for path in expected.required_paths
        )
        scores.append(
            Evaluation(
                name="required_fields",
                value=matched / len(expected.required_paths),
                comment=f"必需字段 {matched}/{len(expected.required_paths)}",
            )
        )
    if expected.min_counts:
        passed = sum(
            _collection_size(_resolve_path(output, path)) >= minimum
            for path, minimum in expected.min_counts.items()
        )
        scores.append(
            Evaluation(
                name="minimum_counts",
                value=passed / len(expected.min_counts),
                comment=f"最小数量约束 {passed}/{len(expected.min_counts)}",
            )
        )


def _append_coverage_scores(
    scores: list[Evaluation], output: dict[str, Any], expected: GoldenExpectedOutput
) -> None:
    if expected.required_node_types:
        actual = _item_values(output, "form_data.nodes", "type")
        scores.append(
            _coverage_evaluation(
                "node_type_coverage", actual, expected.required_node_types
            )
        )
    if expected.required_widget_types:
        actual = _item_values(output, "form_data.widgetList", "type")
        scores.append(
            _coverage_evaluation(
                "widget_type_coverage", actual, expected.required_widget_types
            )
        )


def _append_fallback_score(
    scores: list[Evaluation], output: dict[str, Any], expected: GoldenExpectedOutput
) -> None:
    matches = _fallback_contract_matches(output, expected)
    if matches is None:
        return
    scores.append(
        _evaluation("fallback_contract", matches, "错误类型与用户可见兜底文案契约")
    )


def _fallback_contract_matches(
    output: dict[str, Any], expected: GoldenExpectedOutput
) -> bool | None:
    explicit_contract = expected.error_type is not None or expected.message_contains
    observed_fallback = output.get("intent") == "error" and expected.fallback_output
    if not explicit_contract and not observed_fallback:
        return None
    error_types = (
        observed_fallback.error_types
        if observed_fallback
        else [expected.error_type]
        if expected.error_type
        else []
    )
    error_matches = not error_types or output.get("error_type") in error_types
    message = str(output.get("message", ""))
    required_text = (
        observed_fallback.message_contains
        if observed_fallback
        else expected.message_contains
    )
    message_matches = all(text in message for text in required_text)
    if observed_fallback and observed_fallback.message_required:
        message_matches = bool(message.strip()) and message_matches
    return error_matches and message_matches


def _resolve_path(value: Any, path: str) -> Any | None:
    current = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _collection_size(value: Any) -> int:
    return len(value) if isinstance(value, (list, dict, str)) else 0


def _item_values(output: dict[str, Any], path: str, key: str) -> set[str]:
    items = _resolve_path(output, path)
    if not isinstance(items, list):
        return set()
    return {
        str(item[key])
        for item in items
        if isinstance(item, dict) and item.get(key) is not None
    }


def _coverage_evaluation(
    name: str, actual: set[str], required: list[str]
) -> Evaluation:
    matched = len(actual.intersection(required))
    return Evaluation(
        name=name,
        value=matched / len(required),
        comment=f"覆盖 {matched}/{len(required)}: {', '.join(required)}",
    )


def _evaluation(name: str, passed: bool, comment: str) -> Evaluation:
    return Evaluation(name=name, value=1 if passed else 0, comment=comment)


__all__ = [
    "GoldenCase",
    "GoldenExpectedOutput",
    "GoldenFallbackOutput",
    "GoldenInput",
    "build_workflow_task",
    "evaluate_contract",
    "load_golden_cases",
    "select_cases",
    "sync_dataset",
]
