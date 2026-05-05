"""
FlowMind 智能流程设计服务 - 格式化节点

本模块为 Agent 输出包装统一的元数据信封。
"""


from app.graph.nodes.base import node_handler
from app.graph.state.app_state import AppState
from app.infra.logger import logger


@node_handler("format")
def format_node(state: AppState) -> AppState:
    """格式化节点

    将 Agent 输出统一为前端所需的结构:
    { form_data: { ...设计数据, bpmnXml?, formName? }, message, trace_id, design_type, review_passed }
    """
    try:
        raw_result = state.get("raw_result", {})

        if not raw_result:
            raw_result = {
                "form_data": state.get("design_output", {}),
                "message": "未能生成有效结果",
            }

        form_data = dict(raw_result.get("form_data", {}))
        if "bpmn_xml" in raw_result:
            form_data["bpmn_xml"] = raw_result["bpmn_xml"]

        # 包装元数据信封
        formatted = {
            "form_data": form_data,
            "message": raw_result.get("message", ""),
            "trace_id": state.get("trace_id", ""),
            "design_type": state.get("design_type", ""),
            "review_passed": state.get("review_passed", True),
        }

        # 审查未通过时附加错误信息
        if not state.get("review_passed", True):
            formatted["review_errors"] = state.get("review_errors", [])

        state["formatted_result"] = formatted
        state["format_success"] = True
        return state

    except Exception as e:
        logger.error(f"格式化节点执行失败：{e}")
        state["format_success"] = False
        state["format_error"] = str(e)
        state["formatted_result"] = state.get("raw_result", {})
        return state
