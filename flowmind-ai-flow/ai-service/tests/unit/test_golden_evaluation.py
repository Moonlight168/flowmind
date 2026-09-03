"""FlowMind 黄金数据集与 Langfuse 评估单元测试。"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from app.core.auth_context import get_auth_token
from app.core.exceptions import FlowDesignException
from app.evaluation import golden_dataset
from app.evaluation.golden_dataset import (
    GoldenCase,
    build_workflow_task,
    evaluate_contract,
    load_golden_cases,
    select_cases,
    sync_dataset,
)
from scripts import run_golden_eval
from scripts.run_golden_eval import parse_args


def _case(case_id: str = "flow-linear") -> GoldenCase:
    return GoldenCase.model_validate(
        {
            "id": case_id,
            "category": "flow_design",
            "source": "curated",
            "input": {
                "turns": [
                    {
                        "design_type": "flow_design",
                        "user_input": "设计请假审批流程",
                        "current_form_data": {},
                        "mode": "design",
                    }
                ]
            },
            "expected_output": {
                "status": "ready",
                "required_paths": ["form_data.nodes", "form_data.bpmn_xml"],
                "min_counts": {"form_data.nodes": 3},
                "required_node_types": ["START_EVENT", "USER_TASK", "END_EVENT"],
            },
        }
    )


class _FakeLangfuseClient:
    def __init__(self, captured: dict[str, object], result: SimpleNamespace) -> None:
        self.captured = captured
        self.result = result

    def create_dataset(self, **kwargs: object) -> None:
        self.captured["dataset"] = kwargs

    def create_dataset_item(self, **kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(**kwargs)

    def run_experiment(self, **kwargs: object) -> SimpleNamespace:
        self.captured["experiment"] = kwargs
        return self.result

    def flush(self) -> None:
        self.captured["flushed"] = True


def test_load_dataset_reports_invalid_line(tmp_path: Path) -> None:
    dataset = tmp_path / "golden.jsonl"
    dataset.write_text(
        json.dumps(_case().model_dump(), ensure_ascii=False) + "\n{bad-json}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="第 2 行"):
        load_golden_cases(dataset)


def test_load_dataset_rejects_duplicate_ids(tmp_path: Path) -> None:
    dataset = tmp_path / "golden.jsonl"
    row = json.dumps(_case().model_dump(), ensure_ascii=False)
    dataset.write_text(f"{row}\n{row}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="重复"):
        load_golden_cases(dataset)


def test_select_exact_case() -> None:
    cases = [_case("first"), _case("second")]

    assert [case.id for case in select_cases(cases, "second")] == ["second"]
    with pytest.raises(ValueError, match="missing"):
        select_cases(cases, "missing")


def test_evaluate_contract_scores_stable_structure() -> None:
    expected = _case().expected_output.model_dump()
    output = {
        "status": "ready",
        "form_data": {
            "nodes": [
                {"type": "START_EVENT"},
                {"type": "USER_TASK"},
                {"type": "END_EVENT"},
            ],
            "bpmn_xml": "<definitions />",
        },
    }

    scores = evaluate_contract(output=output, expected_output=expected)
    score_values = {score.name: score.value for score in scores}

    assert score_values["status_match"] == 1
    assert score_values["required_fields"] == 1
    assert score_values["minimum_counts"] == 1
    assert score_values["node_type_coverage"] == 1
    assert score_values["contract_score"] == 1


def test_evaluate_contract_scores_fallback_contract() -> None:
    scores = evaluate_contract(
        output={
            "status": "error",
            "error_type": "internal",
            "message": "AI 服务暂时异常，请稍后重试",
        },
        expected_output={
            "status": "error",
            "error_type": "internal",
            "message_contains": ["AI 服务暂时异常"],
        },
    )

    assert {score.name: score.value for score in scores}["fallback_contract"] == 1


def test_sync_dataset_uses_stable_ids() -> None:
    client = SimpleNamespace(
        create_dataset=lambda **kwargs: kwargs,
        create_dataset_item=lambda **kwargs: kwargs,
    )

    first = sync_dataset(client, "flowmind-design-golden-v1", [_case()])
    second = sync_dataset(client, "flowmind-design-golden-v1", [_case()])

    assert first[0]["id"] == second[0]["id"]
    assert first[0]["metadata"]["case_id"] == "flow-linear"
    assert first[0]["input"]["turns"][0]["design_type"] == "flow_design"


@pytest.mark.parametrize(
    ("failure", "exception_name"),
    [
        (httpx.ConnectError("model unavailable"), "ConnectError"),
        (FlowDesignException("会话锁不可用", stage="lock"), "FlowDesignException"),
    ],
)
def test_workflow_task_isolates_expected_runtime_failure(
    monkeypatch: pytest.MonkeyPatch,
    failure: Exception,
    exception_name: str,
) -> None:
    cleaned: list[str] = []

    def fail_workflow(**kwargs: object) -> dict:
        raise failure

    monkeypatch.setattr(golden_dataset, "invoke_design_workflow", fail_workflow)
    monkeypatch.setattr(
        golden_dataset,
        "delete_design_thread",
        lambda thread_id: cleaned.append(thread_id),
    )
    task = build_workflow_task("token-for-test")
    item = SimpleNamespace(
        input=_case().input.model_dump(), metadata={"case_id": "flow-linear"}
    )

    result = task(item=item)

    assert result["intent"] == "error"
    assert result["error_type"] == "evaluation_runtime"
    assert result["failed_exception"] == exception_name
    assert cleaned == [result["thread_id"]]
    assert get_auth_token() is None


def test_workflow_task_calls_production_contract_and_cleans_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    cleaned: list[str] = []

    def invoke_workflow(**kwargs: object) -> dict:
        captured.update(kwargs)
        captured["auth_token"] = get_auth_token()
        return {"status": "ready", "intent": "success", "form_data": {}}

    monkeypatch.setattr(golden_dataset, "invoke_design_workflow", invoke_workflow)
    monkeypatch.setattr(
        golden_dataset,
        "delete_design_thread",
        lambda thread_id: cleaned.append(thread_id),
    )

    result = build_workflow_task("token-for-test")(
        item=SimpleNamespace(
            input=_case().input.model_dump(), metadata={"case_id": "flow-linear"}
        )
    )

    assert captured["design_type"] == "flow_design"
    assert captured["auth_token"] == "token-for-test"
    assert cleaned == [captured["thread_id"]]
    assert result["status"] == "ready"
    assert get_auth_token() is None


def test_workflow_task_isolates_invalid_dataset_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cleaned: list[str] = []
    monkeypatch.setattr(
        golden_dataset,
        "delete_design_thread",
        lambda thread_id: cleaned.append(thread_id),
    )

    result = build_workflow_task("token-for-test")(
        item=SimpleNamespace(input={"user_input": "missing type"}, metadata={})
    )

    assert result["error_type"] == "evaluation_runtime"
    assert result["failed_exception"] == "ValidationError"
    assert cleaned == [result["thread_id"]]


def test_repository_dataset_has_unique_coverage() -> None:
    dataset = Path(__file__).parents[2] / "evals" / "golden_dataset.jsonl"
    cases = load_golden_cases(dataset)

    assert len(cases) >= 8
    assert {turn.design_type for case in cases for turn in case.input.turns} == {
        "flow_design",
        "form_design",
        "category_design",
    }
    assert {turn.mode for case in cases for turn in case.input.turns} == {
        "basic",
        "design",
    }
    assert any(case.expected_output.status == "needs_input" for case in cases)
    assert any(case.expected_output.fallback_output for case in cases)
    assert any(len(case.input.turns) > 1 for case in cases)
    assert {case.source for case in cases} == {"real_anonymized", "curated"}


def test_cli_selects_one_case() -> None:
    args = parse_args(["--case-id", "flow-linear-leave"])

    assert args.case_id == "flow-linear-leave"
    assert args.max_concurrency == 1


def test_cli_run_syncs_only_selected_case_and_flushes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    result = SimpleNamespace(
        dataset_run_url="https://langfuse.example/run/1",
        format=lambda **kwargs: "evaluation summary",
    )

    monkeypatch.setattr(
        run_golden_eval.settings.evaluation, "auth_token", "token-for-test"
    )
    monkeypatch.setattr(run_golden_eval, "observability_enabled", lambda: True)
    monkeypatch.setattr(
        run_golden_eval, "get_client", lambda: _FakeLangfuseClient(captured, result)
    )
    args = parse_args(["--case-id", "flow-linear-leave", "--run-name", "test-run"])

    assert run_golden_eval.run(args) is result
    experiment = captured["experiment"]
    assert len(experiment["data"]) == 1
    assert experiment["data"][0].metadata["case_id"] == "flow-linear-leave"
    assert experiment["run_name"] == "test-run"
    assert experiment["evaluators"] == [evaluate_contract]
    assert captured["flushed"] is True
