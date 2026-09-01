"""
FlowMind 智能流程设计服务 - 聊天节点

本模块实现普通对话节点，处理一般用户输入。
"""

from langchain_core.messages import AIMessage, HumanMessage

from app.adapters.factory import ModelFactory
from app.graph.nodes.base import chat_error_fallback, node_handler
from app.graph.state.app_state import AppState
from app.prompts.loader import load_prompt


@node_handler("chat", fallback=chat_error_fallback)
def chat_node(state: AppState) -> AppState:
    """聊天节点

    处理普通对话，使用 LLM 生成自然的回复。
    使用 messages 数组格式传递完整对话历史给 LLM。
    """
    last_message = (
        state["messages"][-1] if state["messages"] else HumanMessage(content="")
    )
    user_input = last_message.content

    manager = ModelFactory.get_model_manager()

    # 构建 messages 数组：system + 历史对话 + 当前用户输入
    messages = [
        {
            "role": "system",
            "content": load_prompt("agents/chat.md"),
        }
    ]

    # 添加历史对话（排除最后一条用户消息，已在下方单独添加）
    for msg in state["messages"][:-1]:
        if isinstance(msg, HumanMessage):
            messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            messages.append({"role": "assistant", "content": msg.content})

    # 添加当前用户输入
    messages.append({"role": "user", "content": user_input})

    # 不覆盖 LangGraph 注入的 callbacks，messages 流模式依赖它转发 token。
    result = manager.create_llm(task_name="chat").invoke(messages)
    if result is None:
        raise RuntimeError("聊天模型返回空结果")
    ai_response = result.content

    state["chat_response"] = ai_response
    state["messages"] = [*state["messages"], AIMessage(content=ai_response)]
    return state
