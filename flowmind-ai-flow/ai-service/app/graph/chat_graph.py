"""
FlowMind 智能流程设计服务 - 聊天 Workflow

简化后的通用聊天 Workflow，只包含 chat_node，并支持同步与 token 流式调用。
"""

from collections.abc import Iterator
from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from app.graph.nodes.chat import chat_node
from app.graph.state import AppState
from app.infra.checkpoint import checkpointer, save_preview, thread_exists
from app.infra.logger import generate_trace_id, log_context
from app.infra.observability import (
    langchain_config,
    observe_workflow,
    record_observation_output,
)
from app.prompts import prompt_release


def create_chat_workflow() -> StateGraph:
    """创建简化的聊天 Workflow"""
    workflow = StateGraph(AppState)

    workflow.add_node("chat", chat_node)
    workflow.set_entry_point("chat")
    workflow.add_edge("chat", END)

    return workflow.compile(checkpointer=checkpointer)


chat_workflow = create_chat_workflow()


def _prepare_chat_call(
    user_input: str,
    thread_id: str,
    trace_id: str | None,
    kwargs: dict[str, Any],
    *,
    stream_response: bool,
) -> tuple[dict[str, Any], str, AppState]:
    """准备聊天调用配置与初始状态。"""
    config = {"configurable": {"thread_id": thread_id}}
    auth_token = kwargs.get("auth_token")
    if auth_token:
        config["configurable"]["auth_token"] = auth_token

    # 新线程且用户有输入时保存预览
    if not thread_exists(thread_id) and user_input.strip():
        save_preview(thread_id, user_input)

    if not trace_id:
        trace_id = generate_trace_id()

    initial_state: AppState = {
        "messages": [HumanMessage(content=user_input)],
        "stream_response": stream_response,
    }
    return config, trace_id, initial_state


def invoke_chat_workflow(
    user_input: str,
    thread_id: str,
    trace_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """聊天 Workflow 同步调用入口。"""
    config, trace_id, initial_state = _prepare_chat_call(
        user_input, thread_id, trace_id, kwargs, stream_response=False
    )

    with (
        prompt_release(thread_id),
        log_context(trace_id=trace_id, request_id=thread_id[:8] if thread_id else None),
        observe_workflow(
            "flowmind.chat",
            input={"user_input": user_input},
            session_id=thread_id,
            trace_id=trace_id,
            metadata={"stream": False},
            tags=["chat"],
        ) as observation,
    ):
        result = chat_workflow.invoke(initial_state, langchain_config(config))
        record_observation_output(
            observation,
            {
                "chat_response": result.get("chat_response")
                if isinstance(result, dict)
                else result
            },
        )
        return result


def stream_chat_workflow(
    user_input: str,
    thread_id: str,
    trace_id: str | None = None,
    **kwargs: Any,
) -> Iterator[dict[str, Any]]:
    """聊天 Workflow 流式入口，逐 token 返回 delta，最后返回 done。"""
    config, trace_id, initial_state = _prepare_chat_call(
        user_input, thread_id, trace_id, kwargs, stream_response=True
    )
    final_response = ""

    with (
        prompt_release(thread_id),
        log_context(trace_id=trace_id, request_id=thread_id[:8] if thread_id else None),
        observe_workflow(
            "flowmind.chat",
            input={"user_input": user_input},
            session_id=thread_id,
            trace_id=trace_id,
            metadata={"stream": True},
            tags=["chat", "stream"],
        ) as observation,
    ):
        for stream_mode, data in chat_workflow.stream(
            initial_state,
            langchain_config(config),
            stream_mode=["custom", "updates"],
        ):
            if stream_mode == "custom":
                if isinstance(data, dict) and data.get("type") == "delta":
                    yield data
            elif stream_mode == "updates":
                node_state = data.get("chat", {}) if isinstance(data, dict) else {}
                if isinstance(node_state, dict):
                    final_response = str(node_state.get("chat_response") or "")

        if not final_response:
            state = chat_workflow.get_state(config)
            if state and isinstance(state.values, dict):
                final_response = str(state.values.get("chat_response") or "")

        record_observation_output(observation, {"chat_response": final_response})
        yield {"type": "done", "response": final_response}


def get_chat_workflow_state(thread_id: str) -> dict | None:
    """获取聊天 Workflow 状态"""
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = chat_workflow.get_state(config)
        return state.values if state else None
    except Exception:
        return None


__all__ = [
    "chat_workflow",
    "create_chat_workflow",
    "get_chat_workflow_state",
    "invoke_chat_workflow",
    "stream_chat_workflow",
]
