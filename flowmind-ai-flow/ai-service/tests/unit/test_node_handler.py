"""
FlowMind 智能流程设计服务 - 节点装饰器单元测试
"""

from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage
from langgraph.errors import GraphInterrupt

from app.graph.nodes import base
from app.graph.nodes.base import (
    chat_error_fallback,
    design_error_fallback,
    node_handler,
)
from app.graph.state import AppState


def test_node_handler_returns_design_fallback_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """设计节点异常统一转换为可被路由和格式化的错误状态。"""
    error_logs = []
    monkeypatch.setattr(
        base,
        "logger",
        SimpleNamespace(
            debug=lambda message: None,
            info=lambda message: None,
            error=error_logs.append,
        ),
    )

    @node_handler("design", fallback=design_error_fallback)
    def failing_node(state: AppState) -> AppState:
        raise RuntimeError("模型不可用")

    result = failing_node({"messages": []})

    assert result["intent"] == "error"
    assert result["design_output"] == {
        "intent": "error",
        "message": "AI 服务暂时异常，请稍后重试",
        "error_type": "internal",
    }
    assert len(error_logs) == 1
    assert "[design] 执行失败: 模型不可用" in error_logs[0]


def test_node_handler_returns_chat_fallback_on_failure() -> None:
    """聊天节点异常统一追加稳定回复并保留历史消息。"""
    original = AIMessage(content="历史回复")

    @node_handler("chat", fallback=chat_error_fallback)
    def failing_node(state: AppState) -> AppState:
        raise TimeoutError("请求超时")

    result = failing_node({"messages": [original]})

    assert result["chat_response"] == "抱歉，AI 服务当前不可用，请稍后重试。"
    assert result["messages"][0] is original
    assert result["messages"][-1].content == result["chat_response"]


def test_node_handler_preserves_success_result() -> None:
    """成功路径原样返回节点结果。"""

    @node_handler("test", fallback=design_error_fallback)
    def successful_node(state: AppState) -> AppState:
        state["intent"] = "success"
        return state

    assert successful_node({})["intent"] == "success"


def test_node_handler_does_not_swallow_graph_interrupt() -> None:
    """LangGraph 暂停信号必须继续向框架传播。"""

    @node_handler("interrupt", fallback=design_error_fallback)
    def interrupting_node(state: AppState) -> AppState:
        raise GraphInterrupt()

    with pytest.raises(GraphInterrupt):
        interrupting_node({})
