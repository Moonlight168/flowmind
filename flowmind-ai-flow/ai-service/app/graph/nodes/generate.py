"""
FlowMind 智能审批服务 - 设计生成节点

本模块实现设计工作流的 ReAct Agent 节点，负责：
1. 从 state["messages"] 提取对话历史
2. 调用 LLM 生成内容
3. 根据结果设置 intent (clarification/success)
4. 将 AI 回复追加到 messages
"""

from langchain_core.messages import AIMessage, HumanMessage

from app.design.generation import run_react_agent
from app.design.history import compress_history
from app.design.intent import discriminate_intent
from app.graph.nodes.base import node_handler
from app.graph.state import AppState
from app.infra.logger import logger


@node_handler("design")
def generate_node(state: AppState) -> AppState:
    """执行意图识别、历史压缩与 ReAct 结构化生成。"""
    design_type = state.get("design_type", "")
    # 用户原始输入：取最后一条 HumanMessage（重试时最后一条是 feedback AIMessage，不能取 messages[-1]）
    messages = state.get("messages")
    user_input = ""
    for msg in reversed(messages or []):
        if isinstance(msg, HumanMessage):
            user_input = msg.content or ""
            break
    current_form_data = state.get("current_form_data", {})

    if not design_type:
        state["intent"] = "clarification"
        state["design_output"] = {"message": "请告诉我您想设计什么？"}
        return state

    if not user_input:
        state["intent"] = "clarification"
        state["design_output"] = {"message": "请明确您的需求"}
        return state

    # 阶段1：意图判别（clarification/rollback/reset 提前分流，不调生成）
    intent = discriminate_intent(
        user_input,
        baseline_summary=_baseline_summary(current_form_data, design_type),
    )
    if intent.kind == "clarification":
        msg = intent.message or "请更具体地描述您的需求"
        state["intent"] = "clarification"
        state["design_output"] = {"intent": "clarification", "message": msg}
        state["messages"].append(AIMessage(content=msg))
        return state
    if intent.kind == "rollback":
        state["intent"] = "clarification"  # 走 format 跳过 review
        state["design_output"] = {
            "intent": "clarification",
            "kind": "rollback",
            "target": intent.target or "start",
            "message": "已回到指定版本",
        }
        state["messages"].append(AIMessage(content="已回到指定版本"))
        return state
    if intent.kind == "reset":
        state["intent"] = "clarification"
        state["design_output"] = {
            "intent": "clarification",
            "kind": "reset",
            "message": "已清空，重新开始",
        }
        state["messages"].append(AIMessage(content="已清空，重新开始"))
        return state

    # 构建对话历史（从 messages 提取，移除 system 和 最后一条 user）
    conversation_history = []
    for msg in state.get("messages", []):
        if isinstance(msg, HumanMessage):
            conversation_history.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            conversation_history.append({"role": "assistant", "content": msg.content})

    mode = state.get("mode", "design")

    # 前置压缩：消息过多时裁剪/摘要，再喂给 LLM
    conversation_history = compress_history(conversation_history)

    result = run_react_agent(
        design_type=design_type,
        messages=conversation_history,  # 传入对话历史
        current_form_data=current_form_data,
        task_name=design_type,
        mode=mode,
    )

    logger.debug(f"[design] LLM 返回: {str(result)[:200]}")

    # 解析结果，设置 intent
    if result.get("intent") == "clarification":
        state["intent"] = "clarification"
        state["design_output"] = result
        ai_message = result.get("message", "请明确您的需求")
    elif result.get("intent") == "error":
        state["intent"] = "error"
        state["design_output"] = result
        ai_message = result.get("message", "AI 服务暂时异常")
    else:
        state["intent"] = "success"
        state["design_output"] = result
        ai_message = str(result)

    # 将 AI 回复追加到 messages
    state["messages"].append(AIMessage(content=ai_message))

    return state


def _baseline_summary(current_form_data: dict, design_type: str) -> str:
    """生成基线摘要（供意图判别用），无基线返回空串"""
    if not current_form_data:
        return ""
    if design_type == "flow_design":
        nodes = current_form_data.get("nodes") or []
        return f"{len(nodes)} 个节点" if nodes else ""
    if design_type == "form_design":
        widgets = current_form_data.get("widgetList") or []
        return f"{len(widgets)} 个字段" if widgets else ""
    if design_type == "category_design":
        name = current_form_data.get("category_name")
        return f"分类 {name}" if name else ""
    return ""
