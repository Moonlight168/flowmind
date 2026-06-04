"""
FlowMind 智能审批服务 - 审查节点

职责：
1. 从 design_output 提取数据进行审查
2. 失败时注入错误反馈到 messages，并增加重试计数
3. 通过 checkpoint 自动持久化更新的 messages
"""

from langchain_core.messages import AIMessage

from app.agents.reviewer import reviewer_agent
from app.graph.nodes.base import node_handler
from app.graph.state.app_state import AppState
from app.infra.logger import logger
from app.utils.bpmn_generator import generate_bpmn_xml
from app.utils.bpmn_validator import validate_bpmn_xml

MAX_RETRIES = 3


@node_handler("review")
def review_node(state: AppState) -> AppState:
    """审查节点"""
    design_type = state.get("design_type", "")
    design_output = state.get("design_output") or {}

    logger.info(f"[review] 进入, design_type={design_type}")

    # 追问时跳过审查
    intent = state.get("intent", "")
    if intent == "clarification":
        logger.info("[review] 追问场景，跳过审查")
        design_output["review"] = {"passed": True, "errors": [], "suggestions": []}
        state["design_output"] = design_output
        return state

    if not design_type:
        logger.warning("[review] 未指定 design_type，跳过审查")
        design_output["review"] = {"passed": True, "errors": [], "suggestions": []}
        state["design_output"] = design_output
        return state

    # 提取待审查数据
    review_data = _extract_output(design_output)
    if not review_data:
        logger.warning("[review] 未能提取输出数据，跳过审查")
        design_output["review"] = {"passed": True, "errors": [], "suggestions": []}
        state["design_output"] = design_output
        return state

    # BPMN 结构验证（flow_design 专属，在 LLM 审查之前）
    if design_type == "flow_design":
        bpmn_errors = _validate_bpmn_structure(design_output, state)
        if bpmn_errors:
            retry_count = (state.get("review_retry_count") or 0) + 1
            design_output["review"] = {
                "passed": False,
                "errors": bpmn_errors,
                "suggestions": [],
            }

            if retry_count <= MAX_RETRIES:
                logger.warning(f"[review] BPMN 验证失败（第 {retry_count}/{MAX_RETRIES} 次）：{bpmn_errors}")
                error_feedback = _build_error_feedback(bpmn_errors, design_output)
                state["messages"].append(AIMessage(content=error_feedback))
            else:
                logger.error(f"[review] BPMN 验证失败，已达最大重试次数 ({MAX_RETRIES})")

            state["design_output"] = design_output
            state["review_retry_count"] = retry_count
            return state

    # 根据 mode 选择 schema
    mode = state.get("mode", "design")
    if design_type == "flow_design":
        schema_name = "flow_design_basic" if mode == "basic" else "flow_design_nodes"
    else:
        schema_name = design_type

    # 执行审查
    review_result = reviewer_agent.review(review_data, schema_name, state)

    if review_result.passed:
        logger.info("[review] 审查通过")
        design_output["review"] = {"passed": True, "errors": [], "suggestions": []}
    else:
        retry_count = (state.get("review_retry_count") or 0) + 1
        design_output["review"] = {
            "passed": False,
            "errors": review_result.errors,
            "suggestions": review_result.suggestions,
        }

        if retry_count <= MAX_RETRIES:
            logger.warning(f"[review] 审查未通过（第 {retry_count}/{MAX_RETRIES} 次）：{review_result.errors}")
            error_feedback = _build_error_feedback(review_result.errors, design_output)
            state["messages"].append(AIMessage(content=error_feedback))
            logger.debug(f"[review] 已注入错误反馈，messages数量={len(state['messages'])}")
        else:
            logger.error(f"[review] 审查失败，已达最大重试次数 ({MAX_RETRIES})")

        state["review_retry_count"] = retry_count

    state["design_output"] = design_output
    return state


def _build_error_feedback(errors: list[str], design_output: dict | None = None) -> str:
    """构建错误反馈消息，将 BPMN 术语翻译为 JSON nodes/edges 术语"""
    feedback_lines = ["请修正以下问题后重新生成："]

    if design_output:
        nodes = design_output.get("nodes", [])
        edges = design_output.get("edges", [])
        node_map = {n.get("id"): n for n in nodes}

        for error in errors:
            if "出线数量不足" in error or "缺少 conditionExpression" in error:
                # 从错误信息中提取网关 ID
                gw_id = _extract_gateway_id(error)
                if gw_id:
                    gw_node = node_map.get(gw_id, {})
                    gw_name = gw_node.get("name", gw_id)
                    outgoing = [e for e in edges if e.get("source") == gw_id]
                    outgoing_count = len(outgoing)

                    feedback_lines.append(
                        f"- 排他网关 \"{gw_name}\"(id={gw_id}) 当前只有 {outgoing_count} 条出边，"
                        f"但排他网关必须有 ≥2 条出边且每条都要有 condition 字段。"
                        f"如果此流程不需要条件分支，请移除该网关节点并直接将前一个节点连向下一个节点。"
                    )
                else:
                    feedback_lines.append(f"- {error}")
            else:
                feedback_lines.append(f"- {error}")
    else:
        for error in errors:
            feedback_lines.append(f"- {error}")

    return "\n".join(feedback_lines)


def _extract_gateway_id(error_message: str) -> str | None:
    """从验证错误信息中提取网关 ID，如 'Gateway_1'"""
    import re
    match = re.search(r"'(Gateway_\d+|gw_\w+)'", error_message)
    return match.group(1) if match else None


def _extract_output(design_output: dict) -> dict | None:
    """从 design_output 中提取输出数据"""
    return design_output.get("form_data") or design_output


def _validate_bpmn_structure(design_output: dict, state: AppState) -> list[str]:
    """验证 BPMN XML 结构，返回错误列表（空表示通过）"""
    nodes = design_output.get("nodes", [])
    if not nodes:
        return []

    mode = state.get("mode", "design")
    if mode == "basic":
        return []

    current_form_data = state.get("current_form_data") or {}
    code = design_output.get("code") or current_form_data.get("code") or current_form_data.get("category", "")
    category = {"category_name": design_output.get("flow_name", ""), "code": code}

    # 获取 AI 生成的 edges，用于正确验证排他网关等需要多条出边的节点
    edges = design_output.get("edges", [])

    try:
        bpmn_xml = generate_bpmn_xml({"nodes": nodes, "edges": edges}, category)
    except Exception as e:
        logger.error(f"[review] generate_bpmn_xml 失败: {e}")
        return [f"BPMN XML 生成失败: {e}"]

    validation = validate_bpmn_xml(bpmn_xml)
    if not validation.is_valid:
        return [err.message for err in validation.errors]

    if validation.warnings:
        for w in validation.warnings:
            logger.warning(f"[review] BPMN 警告 [{w.rule_id}]: {w.message}")

    return []
