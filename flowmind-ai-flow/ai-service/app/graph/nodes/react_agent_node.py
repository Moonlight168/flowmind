"""
FlowMind 智能审批服务 - ReAct Agent 节点

本模块实现设计工作流的 ReAct Agent 节点，负责：
1. 从 state["messages"] 提取对话历史
2. 调用 LLM 生成内容
3. 根据结果设置 intent (clarification/success)
4. 将 AI 回复追加到 messages
"""

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.react_agent import run_react_agent
from app.core.auth_context import get_auth_token
from app.graph.nodes.base import node_handler
from app.graph.state.app_state import AppState
from app.infra.logger import logger


@node_handler("design")
def react_agent_node(state: AppState) -> AppState:
    """ReAct Agent 节点"""
    design_type = state.get("design_type", "")
    # 直接从 messages 获取最后一条用户消息
    messages = state.get("messages")
    user_input = messages[-1].content if messages else ""
    current_form_data = state.get("current_form_data", {})

    logger.info(f"[design] 进入, design_type={design_type}, user_input={user_input[:30]}...")

    if not design_type:
        state["intent"] = "clarification"
        state["design_output"] = {"message": "请告诉我您想设计什么？"}
        return state

    if not user_input:
        state["intent"] = "clarification"
        state["design_output"] = {"message": "请明确您的需求"}
        return state

    auth_token = get_auth_token()

    # 构建对话历史（从 messages 提取，移除 system 和 最后一条 user）
    conversation_history = []
    for msg in state.get("messages", []):
        if isinstance(msg, HumanMessage):
            conversation_history.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            conversation_history.append({"role": "assistant", "content": msg.content})

    mode = state.get("mode", "design")

    result = run_react_agent(
        design_type=design_type,
        messages=conversation_history,  # 传入对话历史
        current_form_data=current_form_data,
        auth_token=auth_token or "",
        task_name=design_type,
        mode=mode,
    )

    logger.debug(f"[design] LLM 返回: {str(result)[:200]}")

    # 解析结果，设置 intent
    if result.get("intent") == "clarification":
        state["intent"] = "clarification"
        state["design_output"] = result
        ai_message = result.get("message", "请明确您的需求")
    else:
        state["intent"] = "success"
        state["design_output"] = result
        ai_message = str(result)

    # 将 AI 回复追加到 messages
    state["messages"].append(AIMessage(content=ai_message))

    logger.info(f"[design] 完成, intent={state['intent']}")
    return state
