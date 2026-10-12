"""Convert validated design state into the public response contract."""

from app.design.bpmn_generator import generate_bpmn_xml
from app.design.change_report import build_change_report
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
            operations = design_output.get("operations", [])
            design_type = state.get("design_type", "")
            mode = state.get("mode", "design")
            summary = ""
            details: list[dict[str, str]] = []
            # 分类与流程基本信息只改几个文本字段，前端沿用原有的字段 diff 呈现；
            # 表单与流程模型用后端的变更摘要 + 明细分组
            if (design_type, mode) in _SUMMARY_ENTITIES:
                summary, details = build_change_report(
                    design_type,
                    operations,
                    state.get("current_form_data") or {},
                    form_data,
                )
            final_output = {
                "status": "ready",
                "intent": "success",
                "form_data": form_data,
                "message": _success_message(design_type, mode, form_data, summary),
                "operations": operations,
                "operation_count": design_output.get("operation_count", 0),
                "validation": review,
            }
            if summary:
                final_output["change_details"] = details
            # 需要前端在「应用变更」时一并创建的依赖实体（表单占位 / 分类）
            pending = {
                key: design_output[key]
                for key in ("start_form_name", "category_name")
                if design_output.get(key)
            }
            if pending:
                final_output["pending_entities"] = pending
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
            # 基线兜底：模型未给 flow_key 时保留模型标识（前端字段为驼峰 modelKey）
            "flow_key": result.get("flow_key")
            or current.get("flow_key")
            or current.get("modelKey"),
        }

    nodes, edges = result.get("nodes", []), result.get("edges", [])
    category = build_category(result, current)
    bpmn_xml = result.get("bpmn_xml")
    if not bpmn_xml:
        process_key = current.get("modelKey") or current.get("flow_key") or ""
        bpmn_xml = generate_bpmn_xml(
            {"nodes": nodes, "edges": edges}, category, process_key
        )
    return {**current, "nodes": nodes, "edges": edges, "bpmn_xml": bpmn_xml}


def _display_name(value: object) -> str:
    """名称缺失时给占位文案：dict.get 的默认值对空串不生效，会渲染成【】。"""
    text = str(value or "").strip()
    return text or "未命名"


#: 需要"变更摘要"的设计场景 → (实体名, 名称字段候选)
#: 分类与流程基本信息只改几个文本字段，沿用原有的简单文案
_SUMMARY_ENTITIES: dict[tuple[str, str], tuple[str, tuple[str, ...]]] = {
    ("form_design", "design"): ("表单", ("form_name", "formName")),
    ("flow_design", "design"): ("流程", ("flow_name", "modelName")),
}


def _success_message(design_type: str, mode: str, form_data: dict, summary: str) -> str:
    if design_type == "category_design":
        return f"已生成分类【{_display_name(form_data.get('category_name'))}】的变更预览"
    if design_type == "flow_design" and mode == "basic":
        return "已生成流程变更预览"
    entity, name_keys = _SUMMARY_ENTITIES.get(
        (design_type, mode), ("表单", ("form_name", "formName"))
    )
    name = next(
        (str(form_data.get(key)).strip() for key in name_keys if form_data.get(key)),
        "",
    )
    prefix = f"{entity}「{name}」" if name else entity
    return f"{prefix}：{summary}" if summary else f"{prefix}已更新"
