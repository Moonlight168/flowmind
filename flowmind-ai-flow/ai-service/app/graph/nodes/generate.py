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
from app.design.operations import apply_design_operations
from app.domain.design_models import PENDING_FORM_KEY
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

    # 阶段1：意图判别（clarification/rollback 提前分流，不调生成）
    intent = (
        discriminate_intent(
            user_input,
            design_type=design_type,
            baseline_summary=_baseline_summary(current_form_data, design_type),
        )
        if not state.get("review_retry_count")
        else None
    )
    if intent and intent.kind == "clarification":
        msg = intent.message or "请更具体地描述您的需求"
        state["intent"] = "clarification"
        state["design_output"] = {
            "intent": "clarification",
            "message": msg,
            "choices": intent.choices,
        }
        state["messages"].append(AIMessage(content=msg))
        return state
    if intent and intent.kind == "rollback":
        state["intent"] = "clarification"  # 走 format 跳过 review
        state["design_output"] = {
            "intent": "clarification",
            "kind": "rollback",
            "target": intent.target or "start",
            "message": "已回到指定版本",
        }
        state["messages"].append(AIMessage(content="已回到指定版本"))
        return state
    # 构建对话历史（从 messages 提取）
    history_messages = state.get("messages", [])
    history_count = state.get("history_count")
    if history_count is not None and 0 <= history_count < len(history_messages):
        # 回退场景：只保留回退点之前的历史 + 本次新输入
        history_messages = [*history_messages[:history_count], history_messages[-1]]
    conversation_history = []
    for msg in history_messages:
        if isinstance(msg, HumanMessage):
            conversation_history.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            conversation_history.append({"role": "assistant", "content": msg.content})

    mode = state.get("mode", "design")

    # 前置压缩：消息过多时裁剪/摘要，再喂给 LLM
    conversation_history = compress_history(conversation_history)

    result = _generate_design_result(
        design_type, current_form_data, conversation_history, mode
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
        operation_count = result.get("operation_count", 0)
        ai_message = f"已生成 {operation_count} 项变更，正在校验…"

    # 将 AI 回复追加到 messages
    state["messages"].append(AIMessage(content=ai_message))

    return state


def _generate_design_result(
    design_type: str,
    current_form_data: dict,
    conversation_history: list[dict],
    mode: str,
) -> dict:
    for attempt in range(2):
        result = run_react_agent(
            design_type=design_type,
            messages=conversation_history,
            current_form_data=current_form_data,
            task_name=design_type,
            mode=mode,
        )
        if "operations" not in result:
            return result
        try:
            return _materialize_result(result, design_type, current_form_data, mode)
        except ValueError as exc:
            logger.warning("[design] operation application failed: %s", exc)
            if attempt == 0:
                conversation_history.append(_operation_retry_feedback(exc))
    operations = result.get("operations") or []
    return _invalid_operation_result(operations)


def _invalid_operation_result(operations: list[dict]) -> dict:
    return {
        "intent": "error",
        "message": "生成的变更无法应用，请明确要修改的节点或字段后重试",
        "error_type": "invalid_operation",
        "retryable": True,
        "operation_count": len(operations),
    }


def _materialize_result(
    result: dict,
    design_type: str,
    current_form_data: dict,
    mode: str,
) -> dict:
    operations = result["operations"]
    materialized = apply_design_operations(
        design_type, current_form_data, operations, mode=mode
    )
    logger.info(
        "[design] operations applied, type=%s, mode=%s, count=%s",
        design_type,
        mode,
        len(operations),
    )
    payload = {
        **materialized,
        "operations": operations,
        "operation_count": len(operations),
    }
    # 依赖实体缺失时模型给出的建议名，透传给前端在应用变更时创建
    for key in ("start_form_name", "category_name"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            payload[key] = value.strip()

    # 新建表单时模型建议的表单名；已有名字的表单不覆盖
    llm_form_name = result.get("form_name")
    if (
        isinstance(llm_form_name, str)
        and llm_form_name.strip()
        and not str(payload.get("form_name") or "").strip()
    ):
        payload["form_name"] = llm_form_name.strip()

    # 需要新建开始表单时先写占位 key，让 review 生成的 bpmn_xml 带上 formKey；
    # 前端创建表单后按占位替换成真实 key（AI 服务对业务后端只读，不在这里建）
    if design_type == "flow_design" and mode == "design" and payload.get("start_form_name"):
        start_node = next(
            (
                node
                for node in payload.get("nodes") or []
                if str(node.get("type") or "").upper() == "START_EVENT"
            ),
            None,
        )
        if start_node is not None and not start_node.get("form_key"):
            start_node["form_key"] = PENDING_FORM_KEY

    return payload


def _operation_retry_feedback(exc: ValueError) -> dict[str, str]:
    return {
        "role": "assistant",
        "content": (
            f"操作无法应用：{exc}。请只修正目标标识或操作参数，"
            "不要扩大用户要求的修改范围。"
        ),
    }


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
