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
from app.core.exceptions import ErrorCode
from app.design.validators import (
    BaselineValidator,
    BPMNXMLValidator,
    CategoryValidator,
    EdgeValidator,
    FormFieldValidator,
    NodeValidator,
    ValidationError,
    ValidationResult,
    ValidatorContext,
    ValidatorPipeline,
    VForm3Validator,
)
from app.graph.nodes.base import node_handler
from app.graph.state import AppState
from app.infra.logger import logger
from app.integrations.backend import (
    CategoryClient,
    FormClient,
    RoleClient,
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
    state["available_forms"] = context.available_forms
    pipeline = _build_pipeline(design_type, context.mode)
    result = pipeline.run(design_output, context)

    # 依赖实体（表单/分类）不存在、但模型给了建议名 → 由前端在「应用变更」时创建，
    # 本轮不再判失败（AI 服务对业务后端只读，不能自己建）
    _clear_pending_entity_errors(result, design_output, context)

    # 兜底：模型没给建议名时仍按追问处理，避免校验失败重试到死循环。
    ask = _design_clarification(result.errors, context)
    if ask:
        state["intent"] = "clarification"
        design_output["message"] = ask
        design_output["kind"] = "clarification"
        design_output["review"] = {"passed": True, "errors": [], "suggestions": []}
        state["design_output"] = design_output
        logger.info("[review] 依赖数据不可用，转为向用户追问")
        return state

    # 死循环检测：连续 2 次错误 rule_id 集合相同 → error
    history = state.get("review_error_history") or []
    if pipeline.detect_loop(result.errors, [frozenset(h) for h in history]):
        logger.error(
            f"[review] 检测到死循环，rule_ids={sorted({e.rule_id for e in result.errors})}"
        )
        state["intent"] = "error"
        # 确定性校验失败：优先透出具体校验原因（如"还没有流程分类"），
        # 它比通用文案更能指导用户下一步动作；无具体原因时才退回通用提示
        first_error = result.errors[0].message if result.errors else None
        design_output["error_type"] = ErrorCode.VALIDATION_FAILED.value
        design_output["message"] = (
            first_error or "生成结果反复未通过校验，请调整需求后重试"
        )
        design_output["retryable"] = False
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
        # 仅在还会触发下一次 design 重试时追加反馈；已达上限时不再留无人消费的 AIMessage
        if retry_count < settings.validation.review_max_retry_count:
            logger.warning(
                f"[review] 校验失败（第 {retry_count}/{settings.validation.review_max_retry_count} 次）："
                f"{[e.rule_id for e in result.errors]}"
            )
            feedback = _build_error_feedback(result.errors, design_output)
            state["messages"].append(AIMessage(content=feedback))
        else:
            logger.warning(
                f"[review] 校验失败，已达最大重试次数 ({settings.validation.review_max_retry_count})"
            )
        state["review_retry_count"] = retry_count

    state["design_output"] = design_output
    return state


def _build_context(state: AppState) -> ValidatorContext:
    """Fetch only the authoritative data required by this validation pipeline."""
    auth_token = get_auth_token()
    # 提取用户最近一次输入（用于基线删除意图判断）
    user_input = ""
    for msg in reversed(state.get("messages", []) or []):
        if isinstance(msg, HumanMessage):
            user_input = msg.content or ""
            break
    design_type = state.get("design_type", "")
    mode = state.get("mode", "design")
    available_forms = []
    available_categories = []
    available_roles = []
    if design_type == "flow_design" and mode == "design":
        available_forms = request_cache.get(
            "backend:forms:",
            lambda: FormClient(auth_token=auth_token).search_forms(""),
        )
        available_roles = request_cache.get(
            "backend:roles:",
            lambda: RoleClient(auth_token=auth_token).search_roles(""),
        )
    if design_type == "category_design" or (
        design_type == "flow_design" and mode == "basic"
    ):
        available_categories = request_cache.get(
            "backend:categories:",
            lambda: CategoryClient(auth_token=auth_token).search_categories(),
        )
    return ValidatorContext(
        design_type=design_type,
        mode=mode,
        current_form_data=state.get("current_form_data") or {},
        available_forms=available_forms,
        available_categories=available_categories,
        available_roles=available_roles,
        forms_lookup_complete=design_type == "flow_design" and mode == "design",
        categories_lookup_complete=design_type == "category_design"
        or (design_type == "flow_design" and mode == "basic"),
        roles_lookup_complete=design_type == "flow_design" and mode == "design",
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
        return ValidatorPipeline(
            [BaselineValidator(), FormFieldValidator(), VForm3Validator()]
        )
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


#: "分类不可用"的校验规则（flow basic 选用分类）
_CATEGORY_ASK_RULES = {"CAT_C003", "CAT_C005"}
#: "开始表单不可用"的校验规则（flow design）
_FORM_ASK_RULES = {"NODE_N005", "NODE_N010"}


def _clear_pending_entity_errors(
    result: ValidationResult, design_output: dict, context: ValidatorContext
) -> None:
    """模型给出了缺失实体的建议名时，把对应校验错误降级。

    表单/分类的实际创建由前端在「应用变更」时经网关完成（AI 服务对后端只读）。
    """
    if context.design_type != "flow_design":
        return
    pending_form_nodes = {
        str(node_id)
        for draft in (design_output.get("new_forms") or [])
        for node_id in (draft.get("node_ids") or [])
    }
    start_ids = {
        str(node.get("id"))
        for node in (design_output.get("nodes") or [])
        if node.get("type", "").upper() == "START_EVENT" and node.get("id")
    }
    has_pending_start_form = bool(start_ids & pending_form_nodes)
    if context.mode == "design" and has_pending_start_form:
        rules = _FORM_ASK_RULES
    elif context.mode == "basic" and str(design_output.get("category_name") or "").strip():
        rules = _CATEGORY_ASK_RULES
    else:
        return
    result.errors = [e for e in result.errors if e.rule_id not in rules]
    result.is_valid = not result.errors


def _design_clarification(
    errors: list[ValidationError], context: ValidatorContext
) -> str | None:
    """权威数据缺失/不匹配导致的问题，重试无法修复，转为面向用户的追问。

    无相关内容返回 None（交给正常的重试或死循环处理）。
    """
    rule_ids = {e.rule_id for e in errors}

    # 流程设计没有表单：开始节点强制要 form_key，重试不可能通过
    if "NODE_N010" in rule_ids:
        return "当前系统还没有表单。\n\n请先创建表单，再回来生成流程。"

    # 流程基本信息选用分类：没有分类 / 模型给的分类不存在
    if context.design_type == "flow_design" and context.mode == "basic":
        if rule_ids & _CATEGORY_ASK_RULES:
            available = context.available_categories
            if not available:
                return "当前系统还没有流程分类。\n\n请先在「流程分类」中创建分类，再回来生成流程。"
            names = "\n".join(
                f"- {category.get('categoryName') or category.get('code')}"
                for category in available[:10]
                if category.get("categoryName") or category.get("code")
            )
            return (
                "没有找到匹配的流程分类。\n\n"
                f"现有分类：\n{names}\n\n"
                "请确认要归到哪个分类，或先在「流程分类」中创建。"
            )

    return None
