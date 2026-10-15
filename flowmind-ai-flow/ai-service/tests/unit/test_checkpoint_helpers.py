"""
FlowMind 智能流程设计服务 - checkpoint 兼容 helper 单元测试
"""

from langgraph.checkpoint.memory import MemorySaver

from app.infra import checkpoint


def test_memory_saver_helpers(monkeypatch) -> None:
    """debug 降级到 MemorySaver 时查询和预览均不得报错。"""
    monkeypatch.setattr(checkpoint, "checkpointer", MemorySaver())

    assert checkpoint.thread_exists("missing") is False
    checkpoint.save_preview("missing", "hello")
