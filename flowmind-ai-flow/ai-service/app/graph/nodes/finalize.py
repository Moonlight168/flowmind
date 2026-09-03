"""Convert validated design state into the public response contract."""

from app.design.bpmn_generator import generate_bpmn_xml
from app.design.validators import build_category
from app.design.vform3_transformer import transform_to_vform3
from app.graph.nodes.base import node_handler
from app.graph.state import AppState
from app.infra.logger import logger


@node_handler("format")
def finalize_node(state: AppState) -> AppState:
    """Return only validated previews; failed candidates never leave the service."""
    intent = state.get("intent", "clarification")
    design_output = state.get("design_output") or {}

    if intent == "clarification":
        final_output = _needs_input(design_output)
    elif intent == "error":
        final_output = _error(design_output)
    elif intent == "success":
        review = design_output.get("review", {})
        if not review.get("passed", True):
            final_output = _error(
                design_output,
                error_type="validation_failed",
                message="生成结果未通过校验，请调整需求后重试",
            )
        else:
            form_data = _format_validated_artifact(state, design_output)
            final_output = {
                "status": "ready",
                "intent": "success",
                "form_data": form_data,
                "message": _success_message(state.get("design_type", ""), form_data),
                "operations": design_output.get("operations", []),
                "operation_count": design_output.get("operation_count", 0),
                "validation": review,
            }
    else:
        final_output = _error(design_output, message="未知状态")

    logger.info(
        "[format] response status=%s, operations=%s, validation_passed=%s",
        final_output["status"],
        final_output.get("operation_count", 0),
        final_output.get("validation", {}).get("passed"),
    )
    state["design_output"] = final_output
    return state


def _needs_input(design_output: dict) -> dict:
    return {
        "status": "needs_input",
        "intent": "clarification",
        "form_data": None,
        "message": design_output.get("message") or "请明确您的需求",
        "kind": design_output.get("kind"),
        "target": design_output.get("target"),
        "choices": design_output.get("choices", []),
    }


def _error(
    design_output: dict,
    *,
    error_type: str | None = None,
    message: str | None = None,
) -> dict:
    return {
        "status": "error",
        "intent": "error",
        "form_data": None,
        "message": message or design_output.get("message") or "系统错误，请重试",
        "error_type": error_type or design_output.get("error_type", "unknown"),
        "retryable": design_output.get("retryable", True),
        "validation": design_output.get("review", {}),
        "operation_count": design_output.get("operation_count", 0),
    }


def _format_validated_artifact(state: AppState, result: dict) -> dict:
    design_type = state.get("design_type", "")
    mode = state.get("mode", "design")
    current = dict(state.get("current_form_data") or {})

    if design_type == "category_design":
        return {
            "category_name": result.get("category_name", ""),
            "code": result.get("code", ""),
            "remark": result.get("remark", ""),
        }
    if design_type == "form_design":
        return result.get("vform3") or transform_to_vform3(result, current)
    if design_type != "flow_design":
        raise ValueError(f"不支持的设计类型: {design_type}")
    if mode == "basic":
        return {
            **current,
            "flow_name": result.get("flow_name", ""),
            "code": result.get("code", ""),
            "description": result.get("description", ""),
            "flow_key": result.get("flow_key") or current.get("flow_key"),
        }

    nodes, edges = result.get("nodes", []), result.get("edges", [])
    category = build_category(result, current)
    bpmn_xml = result.get("bpmn_xml")
    if not bpmn_xml:
        bpmn_xml = generate_bpmn_xml({"nodes": nodes, "edges": edges}, category)
    return {**current, "nodes": nodes, "edges": edges, "bpmn_xml": bpmn_xml}


def _success_message(design_type: str, form_data: dict) -> str:
    if design_type == "category_design":
        return f"已生成分类【{form_data.get('category_name', '')}】的变更预览"
    if design_type == "form_design":
        return f"已生成表单【{form_data.get('form_name', '表单')}】的变更预览"
    return "已生成流程变更预览"
