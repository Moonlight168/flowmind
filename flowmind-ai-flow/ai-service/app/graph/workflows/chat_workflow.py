"""
FlowMind 智能流程设计服务 - 聊天 Workflow

简化后的通用聊天 Workflow，只包含 chat_node。
"""

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from app.core.checkpoint import checkpointer, save_preview, thread_exists
from app.graph.nodes.chat_node import chat_node
from app.graph.state.app_state import AppState
from app.infra.logger import generate_trace_id, log_context


def create_chat_workflow() -> StateGraph:
    """创建简化的聊天 Workflow"""
    workflow = StateGraph(AppState)

    workflow.add_node("chat", chat_node)
    workflow.set_entry_point("chat")
    workflow.add_edge("chat", END)

    return workflow.compile(checkpointer=checkpointer)


chat_workflow = create_chat_workflow()


def invoke_chat_workflow(
    user_input: str,
    thread_id: str,
    trace_id: str | None = None,
    **kwargs,
) -> dict:
    """聊天 Workflow 调用入口"""
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
    }

    with log_context(
        trace_id=trace_id, request_id=thread_id[:8] if thread_id else None
    ):
        return chat_workflow.invoke(initial_state, config)


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
]
