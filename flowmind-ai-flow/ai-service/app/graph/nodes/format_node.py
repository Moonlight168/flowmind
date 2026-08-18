"""
FlowMind 智能审批服务 - 格式化节点

职责：
1. 根据 intent 和 review 结果生成最终响应
2. 统一返回格式：{ form_data, message, intent }
"""

from app.agents.validators import build_category
from app.graph.nodes.base import node_handler
from app.graph.state.app_state import AppState
from app.infra.logger import logger
from app.utils.bpmn_generator import generate_bpmn_xml
from app.utils.vform3_transformer import transform_to_vform3


@node_handler("format")
def format_node(state: AppState) -> AppState:
    """格式化节点 - 生成最终响应"""
    design_type = state.get("design_type", "")
    intent = state.get("intent", "clarification")
    design_output = state.get("design_output") or {}
    raw_result = dict(design_output)

    logger.info(f"[format] 进入, design_type={design_type}, intent={intent}")

    # 根据 intent 生成响应
    if intent == "clarification":
        final_output = {
            "form_data": None,
            "message": design_output.get("message") or "请明确您的需求",
            "intent": "clarification",
        }

    elif intent == "error":
        # 处理系统错误（如输出截断）
        final_output = {
            "form_data": None,
            "message": design_output.get("message") or "系统错误，请重试",
            "intent": "error",
            "error_type": design_output.get("error_type", "unknown"),
        }

    elif intent == "success":
        review_info = design_output.get("review", {})
        review_passed = review_info.get("passed", True)
        review_retry_count = state.get("review_retry_count") or 0

        if not review_passed and review_retry_count >= 3:
            # 超重试次数
            final_output = {
                "form_data": None,
                "message": f"审查失败：{', '.join(review_info.get('errors', []))}",
                "intent": "error",
            }
        elif not review_passed:
            # 审查未通过但还有重试机会（不应该到达这里，但做防御）
            errors = review_info.get("errors", [])
            final_output = {
                "form_data": None,
                "message": f"请补充：{', '.join(errors)}",
                "intent": "clarification",
            }
        else:
            # 成功，格式化业务数据
            mode = state.get("mode", "design")
            current_form_data = state.get("current_form_data") or {}
            final_output = _format_success_output(design_type, raw_result, mode, current_form_data)

    else:
        final_output = {
            "form_data": None,
            "message": "未知状态",
            "intent": "error",
        }

    state["design_output"] = final_output
    logger.info(f"[format] 完成, intent={final_output['intent']}")
    return state


def _format_success_output(design_type: str, raw_result: dict, mode: str = "design", current_form_data: dict | None = None) -> dict:
    """格式化成功输出"""
    if design_type == "category_design":
        category_name = raw_result.get("category_name", "")
        return {
            "form_data": {
                "category_name": category_name or (current_form_data or {}).get("category_name", ""),
                "code": raw_result.get("code", "") or (current_form_data or {}).get("code", ""),
                "remark": raw_result.get("remark", "") or (current_form_data or {}).get("remark", ""),
            },
            "message": f"已为您生成【{category_name}】分类",
            "intent": "success",
        }

    elif design_type == "flow_design":
        nodes = raw_result.get("nodes", [])
        edges = raw_result.get("edges", [])
        category = build_category(raw_result, current_form_data or {})
        logger.info(f"[format] flow_design raw_result keys: {list(raw_result.keys())}")
        logger.info(f"[format] nodes type: {type(nodes)}, category: {category}, mode: {mode}")

        # design 模式：完全保留前端传递的基本信息，AI 只生成流程编排
        current_form = dict(current_form_data or {})
        form_data = {
            **current_form,  # 保留前端所有字段（modelId, modelName, modelKey, category, description 等）
            # AI 生成的流程编排数据
            "nodes": nodes,
            "edges": edges,
        }

        # basic 模式仅返回基本信息，不生成 BPMN XML
        if mode != "basic":
            # 优先复用 review 阶段 BPMNXMLValidator 缓存的 bpmn_xml，避免二次生成
            bpmn_xml = raw_result.get("bpmn_xml") or ""
            if not bpmn_xml and nodes:
                try:
                    bpmn_xml = generate_bpmn_xml({"nodes": nodes, "edges": edges}, category)
                except (ValueError, TypeError, KeyError, AttributeError) as e:
                    logger.error(f"[format] generate_bpmn_xml 失败: {e}, nodes={nodes}, category={category}")
                    bpmn_xml = ""

            form_data["bpmn_xml"] = bpmn_xml

        return {
            "form_data": form_data,
            "message": f"已为您生成流程编排",
            "intent": "success",
        }

    elif design_type == "form_design":
        # 转换 AI 生成的简化格式为完整 VForm3 格式，合并当前表单已有数据
        form_data = transform_to_vform3(raw_result, current_form_data)
        return {
            "form_data": form_data,
            "message": f"已为您生成【{form_data.get('form_name', '表单')}】",
            "intent": "success",
        }

    else:
        return {
            "form_data": raw_result,
            "message": "生成完成",
            "intent": "success",
        }
