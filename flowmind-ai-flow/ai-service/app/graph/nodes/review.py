"""
FlowMind 智能审批服务 - 审查节点

职责：
1. 按 design_type + mode 选择校验 Pipeline，在 JSON 层校验 LLM 输出
2. 失败时注入错误反馈到 messages，并增加重试计数
3. 死循环检测（连续 2 次同 rule_id 集合 → intent=error）
4. BPMNXMLValidator 生成并缓存 bpmn_xml，供 format_node 复用
"""

import re

from langchain_core.messages import AIMessage, HumanMessage

from app.config.settings import settings
from app.core.auth_context import get_auth_token
from app.design.validators import (
    BaselineValidator,
    BPMNXMLValidator,
    CategoryValidator,
    EdgeValidator,
    FormFieldValidator,
    NodeValidator,
    ValidationError,
    ValidatorContext,
    ValidatorPipeline,
)
from app.graph.nodes.base import node_handler
from app.graph.state import AppState
from app.infra.logger import logger
from app.integrations.backend import (
    CategoryClient,
    FlowModelClient,
    FormClient,
    request_cache,
)
from app.prompts.loader import render_prompt


@node_handler("review")
def review_node(state: AppState) -> AppState:
    """审查节点：JSON 层结构校验"""
    design_type = state.get("design_type", "")
    design_output = state.get("design_output") or {}
    intent = state.get("intent", "")

    # 追问/错误场景跳过校验
    if intent in ("clarification", "error") or not design_type:
        design_output["review"] = {"passed": True, "errors": [], "suggestions": []}
        state["design_output"] = design_output
        return state

    context = _build_context(state)
    pipeline = _build_pipeline(design_type, context.mode)
    result = pipeline.run(design_output, context)

    # 死循环检测：连续 2 次错误 rule_id 集合相同 → error
    history = state.get("review_error_history") or []
    if pipeline.detect_loop(result.errors, [frozenset(h) for h in history]):
        logger.error(
            f"[review] 检测到死循环，rule_ids={sorted({e.rule_id for e in result.errors})}"
        )
        state["intent"] = "error"
        design_output["review"] = {
            "passed": False,
            "errors": [e.message for e in result.errors],
            "suggestions": [],
            "dead_loop": True,
        }
        state["design_output"] = design_output
        return state

    current_rule_set = sorted({e.rule_id for e in result.errors})
    state["review_error_history"] = [*history, current_rule_set][-3:]

    if result.is_valid:
        logger.info("[review] 校验通过")
        design_output["review"] = {"passed": True, "errors": [], "suggestions": []}
    else:
        retry_count = (state.get("review_retry_count") or 0) + 1
        design_output["review"] = {
            "passed": False,
            "errors": [e.message for e in result.errors],
            "warnings": [e.message for e in result.warnings],
        }
        if retry_count <= settings.validation.review_max_retry_count:
            logger.warning(
                f"[review] 校验失败（第 {retry_count}/{settings.validation.review_max_retry_count} 次）："
                f"{[e.rule_id for e in result.errors]}"
            )
            feedback = _build_error_feedback(result.errors, design_output)
            state["messages"].append(AIMessage(content=feedback))
        else:
            logger.error(
                f"[review] 校验失败，已达最大重试次数 ({settings.validation.review_max_retry_count})"
            )
        state["review_retry_count"] = retry_count

    state["design_output"] = design_output
    return state


def _build_context(state: AppState) -> ValidatorContext:
    """构建校验上下文（后端查询失败时 service 内部兜底返回空列表，相关规则自动跳过）"""
    auth_token = get_auth_token()
    # 提取用户最近一次输入（用于基线删除意图判断）
    user_input = ""
    for msg in reversed(state.get("messages", []) or []):
        if isinstance(msg, HumanMessage):
            user_input = msg.content or ""
            break
    return ValidatorContext(
        design_type=state.get("design_type", ""),
        mode=state.get("mode", "design"),
        current_form_data=state.get("current_form_data") or {},
        available_forms=request_cache.get(
            "backend:forms:",
            lambda: FormClient(auth_token=auth_token).search_forms(""),
        ),
        available_categories=request_cache.get(
            "backend:categories:",
            lambda: CategoryClient(auth_token=auth_token).search_categories(),
        ),
        existing_models=request_cache.get(
            "backend:models:",
            lambda: FlowModelClient(auth_token=auth_token).search_flow_models(),
        ),
        auth_token=auth_token,
        user_input=user_input,
    )


def _build_pipeline(design_type: str, mode: str) -> ValidatorPipeline:
    """按 design_type + mode 选择校验组件"""
    if design_type == "flow_design" and mode == "basic":
        return ValidatorPipeline([CategoryValidator()])
    if design_type == "flow_design":
        return ValidatorPipeline(
            [BaselineValidator(), NodeValidator(), EdgeValidator(), BPMNXMLValidator()]
        )
    if design_type == "form_design":
        return ValidatorPipeline([BaselineValidator(), FormFieldValidator()])
    if design_type == "category_design":
        return ValidatorPipeline([BaselineValidator(), CategoryValidator()])
    return ValidatorPipeline([])


def _build_error_feedback(
    errors: list[ValidationError], design_output: dict | None = None
) -> str:
    """构建错误反馈消息，将 BPMN 术语翻译为 JSON nodes/edges 术语"""
    error_lines = []

    if design_output:
        nodes = design_output.get("nodes", [])
        edges = design_output.get("edges", [])
        node_map = {n.get("id"): n for n in nodes}

        for err in errors:
            msg = err.message
            if (
                "出线数量不足" in msg
                or "出边数量不足" in msg
                or "缺少 condition" in msg
            ):
                gw_id = _extract_gateway_id(msg)
                if gw_id:
                    gw_node = node_map.get(gw_id, {})
                    gw_name = gw_node.get("name", gw_id)
                    outgoing = [e for e in edges if e.get("source") == gw_id]
                    error_lines.append(
                        render_prompt(
                            "agents/gateway_feedback.md",
                            {
                                "gateway_name": gw_name,
                                "gateway_id": gw_id,
                                "outgoing_count": len(outgoing),
                            },
                        )
                    )
                else:
                    error_lines.append(f"- {msg}")
            else:
                error_lines.append(f"- {msg}")
    else:
        for err in errors:
            error_lines.append(f"- {err.message}")

    return render_prompt(
        "agents/review_feedback.md",
        {"errors": "\n".join(error_lines)},
    )


def _extract_gateway_id(error_message: str) -> str | None:
    """从验证错误信息中提取网关 ID，如 'Gateway_1' / 'gateway_condition'"""
    match = re.search(r"'(Gateway_\w+|gw_\w+|gateway_\w+)'", error_message)
    return match.group(1) if match else None
