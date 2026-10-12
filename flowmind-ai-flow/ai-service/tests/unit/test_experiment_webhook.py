"""Langfuse 自定义实验 webhook 接收端单元测试。"""

from __future__ import annotations

import json
from typing import Any

import pytest
from starlette.background import BackgroundTasks

from app.api import webhook
from app.evaluation import runner


class _FakeRequest:
    """仅实现 body()，足以驱动 webhook 的 payload 解析。"""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    async def body(self) -> bytes:
        return self._payload


def _capture_runner(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    def fake_run(dataset_name: str, **kwargs: Any) -> None:
        captured["dataset_name"] = dataset_name
        captured.update(kwargs)

    monkeypatch.setattr(runner, "run_dataset_experiment", fake_run)
    return captured


def test_parse_experiment_request_reads_nested_dataset_and_config() -> None:
    request = webhook.parse_experiment_request(
        {
            "dataset": {"id": "d-1", "name": "flowmind-design-golden-v1"},
            "config": {"run_name": "r-1", "case_id": "c-1", "max_concurrency": 3},
        }
    )

    assert request.dataset_name == "flowmind-design-golden-v1"
    assert request.dataset_id == "d-1"
    assert request.run_name == "r-1"
    assert request.case_id == "c-1"
    assert request.max_concurrency == 3


def test_parse_experiment_request_reads_flat_payload() -> None:
    request = webhook.parse_experiment_request(
        {"datasetName": "ds", "datasetId": "id-1", "runName": "r"}
    )

    assert request.dataset_name == "ds"
    assert request.dataset_id == "id-1"
    assert request.run_name == "r"
    assert request.max_concurrency == 1


def test_parse_experiment_request_tolerates_unknown_shape() -> None:
    request = webhook.parse_experiment_request({"unexpected": ["shape"]})

    assert request.dataset_name is None
    assert request.max_concurrency == 1


async def test_trigger_experiment_returns_202_and_runs_in_background(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_runner(monkeypatch)
    request = _FakeRequest(json.dumps({"dataset": {"name": "ds-1"}}).encode())
    tasks = BackgroundTasks()

    response = await webhook.trigger_experiment.__wrapped__(request, tasks)

    assert response.status_code == 202
    await tasks()
    assert captured["dataset_name"] == "ds-1"
    assert captured["extra_metadata"] == {
        "trigger": "langfuse_webhook",
        "dataset_id": None,
    }


async def test_trigger_experiment_falls_back_to_default_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_runner(monkeypatch)
    request = _FakeRequest(b"not-json")
    tasks = BackgroundTasks()

    response = await webhook.trigger_experiment.__wrapped__(request, tasks)

    assert response.status_code == 202
    await tasks()
    assert captured["dataset_name"] == runner.DEFAULT_DATASET_NAME
