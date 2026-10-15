"""评测数据集与执行入口的回归测试。"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest

from app.core.auth_context import get_auth_token
from app.evaluation import datasets, runner
from scripts import run_evaluation, upload_dataset

if TYPE_CHECKING:
    from pathlib import Path


def test_resolve_dataset_specs_uses_four_fixed_design_windows() -> None:
    assert [spec.key for spec in datasets.resolve_dataset_specs("all")] == [
        "category",
        "basic",
        "form",
        "flow",
    ]
    basic = datasets.resolve_dataset_specs("basic")[0]
    assert basic.path.name == "basic_info_design.jsonl"
    assert basic.design_type == "flow_design"
    assert basic.mode == "basic"


def test_repository_datasets_cover_every_window_and_multiturn() -> None:
    all_cases = {
        spec.key: datasets.load_cases(spec.path)
        for spec in datasets.resolve_dataset_specs("all")
    }

    assert set(all_cases) == {"category", "basic", "form", "flow"}
    assert all(len(cases) >= 8 for cases in all_cases.values())
    assert all(
        any(len(case.turns) > 1 for case in cases) for cases in all_cases.values()
    )
    assert all(
        any("exception" in case.tags for case in cases) for cases in all_cases.values()
    )


def test_load_cases_rejects_duplicate_ids(tmp_path: Path) -> None:
    row = {
        "id": "form-create",
        "source": "curated",
        "turns": [{"user_input": "创建表单"}],
    }
    path = tmp_path / "form_design.jsonl"
    path.write_text(f"{json.dumps(row)}\n{json.dumps(row)}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="重复"):
        datasets.load_cases(path)


def test_sync_dataset_injects_design_window_context() -> None:
    captured: dict[str, Any] = {}
    client = SimpleNamespace(
        create_dataset=lambda **kwargs: captured.update(dataset=kwargs),
        create_dataset_item=lambda **kwargs: (
            captured.setdefault("items", []).append(kwargs) or kwargs
        ),
        get_dataset=lambda name: SimpleNamespace(items=[]),
        api=SimpleNamespace(dataset_items=SimpleNamespace(delete=lambda item_id: None)),
    )
    spec = datasets.resolve_dataset_specs("form")[0]
    cases = [
        datasets.EvaluationCase.model_validate(
            {
                "id": "form-create",
                "source": "curated",
                "turns": [{"user_input": "创建表单"}],
            }
        )
    ]

    datasets.sync_dataset(client, spec, cases)

    item = captured["items"][0]
    assert captured["dataset"]["name"] == spec.langfuse_name
    assert item["input"]["turns"][0]["design_type"] == "form_design"
    assert item["input"]["turns"][0]["mode"] == "design"
    assert "expected_output" not in item


def test_workflow_task_reuses_latest_artifact_for_next_turn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []
    cleaned: list[str] = []

    def invoke(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return {
            "status": "ready",
            "message": "ok",
            "form_data": {"version": len(calls)},
        }

    monkeypatch.setattr(runner, "invoke_design_workflow", invoke)
    monkeypatch.setattr(runner, "delete_design_thread", cleaned.append)
    spec = datasets.resolve_dataset_specs("basic")[0]
    task = runner.build_workflow_task("token", spec)
    item = SimpleNamespace(
        input={
            "turns": [
                {"user_input": "创建流程基本信息"},
                {"user_input": "修改流程名称"},
            ]
        },
        metadata={"case_id": "basic-multi-turn"},
    )

    result = task(item=item)

    assert result["status"] == "ready"
    assert len(result["turn_outputs"]) == 2
    assert calls[0]["design_type"] == "flow_design"
    assert calls[0]["mode"] == "basic"
    assert calls[1]["current_form_data"] == {"version": 1}
    assert cleaned == [calls[0]["thread_id"]]
    assert get_auth_token() is None


def test_cli_only_accepts_dataset_key_and_case_id() -> None:
    upload_args = upload_dataset.parse_args(["basic"])
    run_args = run_evaluation.parse_args(["flow", "--case-id", "flow-linear-leave"])

    assert upload_args.dataset == "basic"
    assert run_args.dataset == "flow"
    assert run_args.case_id == "flow-linear-leave"
    assert not hasattr(run_args, "dataset_name")
    assert not hasattr(run_args, "run_name")
