"""契约评估器上传脚本：幂等 upsert 行为。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from langfuse.api import CodeEvaluatorSourceCodeLanguage, CreateEvaluatorRequest_Code

from scripts import upload_evaluator as uploader

SOURCE_CODE = "function evaluate(ctx) { return { scores: [] }; }"


def _evaluator(evaluator_id: str, source_code: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=evaluator_id,
        type="code",
        name=uploader.EVALUATOR_NAME,
        source_code=source_code,
        source_code_language=CodeEvaluatorSourceCodeLanguage.TYPESCRIPT,
    )


class _FakeEvaluators:
    def __init__(self, existing: list[Any], captured: dict[str, Any]) -> None:
        self._existing = existing
        self.captured = captured

    def list(self, *, limit: int | None = None) -> SimpleNamespace:
        self.captured["limit"] = limit
        return SimpleNamespace(data=list(self._existing))

    def create(self, *, request: Any) -> SimpleNamespace:
        self.captured["create"] = request
        return SimpleNamespace(id="new-evaluator")

    def update(self, evaluator_id: str, *, request: Any) -> SimpleNamespace:
        self.captured["update"] = {"id": evaluator_id, "request": request}
        return SimpleNamespace(id=evaluator_id)


def _client(existing: list[Any], captured: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(
        api=SimpleNamespace(evaluators=_FakeEvaluators(existing, captured))
    )


def test_creates_when_absent() -> None:
    captured: dict[str, Any] = {}
    action = uploader.sync_evaluator(_client([], captured), SOURCE_CODE)
    request: CreateEvaluatorRequest_Code = captured["create"]
    assert action == "created"
    assert request.name == uploader.EVALUATOR_NAME
    assert request.source_code == SOURCE_CODE
    assert request.source_code_language is CodeEvaluatorSourceCodeLanguage.TYPESCRIPT
    assert "update" not in captured


def test_skips_when_source_unchanged() -> None:
    captured: dict[str, Any] = {}
    existing = [_evaluator("e1", SOURCE_CODE)]
    action = uploader.sync_evaluator(_client(existing, captured), SOURCE_CODE)
    assert action == "unchanged"
    assert "create" not in captured
    assert "update" not in captured


def test_updates_latest_when_source_changed() -> None:
    captured: dict[str, Any] = {}
    existing = [_evaluator("e2", "old"), _evaluator("e1", "older")]
    action = uploader.sync_evaluator(_client(existing, captured), SOURCE_CODE)
    assert action == "updated"
    assert captured["update"]["id"] == "e2"
    assert captured["update"]["request"].source_code == SOURCE_CODE
    assert "create" not in captured
