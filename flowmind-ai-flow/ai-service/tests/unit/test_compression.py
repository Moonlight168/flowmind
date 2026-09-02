"""
FlowMind 智能流程设计服务 - 前置压缩单元测试
"""

import app.design.history as compression_module
from app.config.settings import settings
from app.design.history import compress_history


def _msgs(n: int, with_system: bool = True) -> list[dict]:
    """构造 n 条非 system 消息（可选带 system）"""
    msgs = [{"role": "system", "content": "system"}] if with_system else []
    for i in range(n):
        msgs.append(
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg{i}"}
        )
    return msgs


def test_below_threshold_unchanged(monkeypatch):
    """未超阈值：原样返回"""
    monkeypatch.setattr(settings.compress, "max_messages", 10)
    msgs = _msgs(5)
    assert compress_history(msgs) == msgs


def test_pure_trim(monkeypatch):
    """纯裁剪：system + 最近 keep_recent 条，中间段丢弃"""
    monkeypatch.setattr(settings.compress, "max_messages", 4)
    monkeypatch.setattr(settings.compress, "keep_recent", 2)
    monkeypatch.setattr(settings.compress, "enable_llm_summary", False)

    msgs = _msgs(6)
    out = compress_history(msgs)
    assert len(out) == 3  # system + 2 条 recent
    assert out[0]["role"] == "system"
    assert out[-1]["content"] == "msg5"
    assert out[-2]["content"] == "msg4"


def test_llm_summary_replaced(monkeypatch):
    """LLM 摘要：中间段替换为 1 条 [历史摘要]"""

    class _FakeLLM:
        class _Resp:
            content = "这是摘要"

        def invoke(self, messages, config=None):
            return self._Resp()

    class _FakeRuntime:
        def execute(self, task_name, operation, structured=False):
            return operation(_FakeLLM())

    monkeypatch.setattr(settings.compress, "max_messages", 4)
    monkeypatch.setattr(settings.compress, "keep_recent", 2)
    monkeypatch.setattr(settings.compress, "enable_llm_summary", True)

    monkeypatch.setattr(compression_module, "get_model_runtime", _FakeRuntime)

    msgs = _msgs(6)
    out = compress_history(msgs)
    assert out[0]["role"] == "system"
    assert out[1]["role"] == "assistant"
    assert "[历史摘要]" in out[1]["content"]
    assert out[-1]["content"] == "msg5"


def test_llm_summary_fallback_to_trim(monkeypatch):
    """LLM 摘要失败 → 回退纯裁剪，不抛异常"""

    class _FakeRuntime:
        def execute(self, task_name, operation, structured=False):
            raise RuntimeError("模型不可用")

    monkeypatch.setattr(settings.compress, "max_messages", 4)
    monkeypatch.setattr(settings.compress, "keep_recent", 2)
    monkeypatch.setattr(settings.compress, "enable_llm_summary", True)

    monkeypatch.setattr(compression_module, "get_model_runtime", _FakeRuntime)

    msgs = _msgs(6)
    out = compress_history(msgs)
    assert len(out) == 3  # 回退纯裁剪
    assert out[0]["role"] == "system"
