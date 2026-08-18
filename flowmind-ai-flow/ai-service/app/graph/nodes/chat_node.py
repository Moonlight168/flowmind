"""
FlowMind 智能流程设计服务 - 聊天节点

本模块实现普通对话节点，处理一般用户输入。
"""

from langchain_core.messages import AIMessage, HumanMessage

from app.adapters.factory import ModelFactory
from app.graph.state.app_state import AppState
from app.infra.logger import logger


def chat_node(state: AppState) -> AppState:
    """聊天节点

    处理普通对话，使用 LLM 生成自然的回复。
    使用 messages 数组格式传递完整对话历史给 LLM。
    """
    try:
        last_message = (
            state["messages"][-1] if state["messages"] else HumanMessage(content="")
        )
        user_input = last_message.content

        manager = ModelFactory.get_model_manager()

        # 构建 messages 数组：system + 历史对话 + 当前用户输入
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个友好、智能的 AI 助手，名为 FlowMind助手。"
                    "请用友好、简洁的语言回复用户，帮助用户解决各种问题。"
                    "如果用户表现出想设计流程的意图，可以引导用户使用 AI 设计功能。"
                ),
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

        result = manager.create_llm(task_name="chat").invoke(messages)

        # LLM 服务不可用时，返回错误信息
        if result is None:
            ai_response = "抱歉，AI 服务当前不可用，请稍后重试。"
        else:
            ai_response = result.content
        logger.debug(f"[AI输出] chat_response: {ai_response}")

        state["chat_response"] = ai_response

        # 将 AI 回复追加到 messages
        state["messages"] = list(state["messages"]) + [AIMessage(content=ai_response)]

        return state

    except (RuntimeError, ValueError, KeyError, ConnectionError, TimeoutError, OSError) as e:
        logger.error(f"聊天节点执行失败：{e}")
        ai_response = "抱歉，AI 服务当前不可用，请稍后重试。"
        state["chat_response"] = ai_response
        state["messages"] = list(state.get("messages", [])) + [
            AIMessage(content=ai_response)
        ]
        return state
