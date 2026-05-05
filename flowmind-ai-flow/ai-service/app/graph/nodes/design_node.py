"""
FlowMind 智能流程设计服务 - 设计节点

本模块封装 DesignAgents，提供统一的设计工作流节点。
"""

from typing import Any

from app.agents.design_category_agent import DesignCategoryAgent
from app.agents.design_flow_agent import DesignFlowAgent
from app.agents.design_form_agent import DesignFormAgent
from app.graph.nodes.base import node_handler
from app.graph.state.app_state import AppState
from app.infra.logger import logger


@node_handler("design")
def design_node(state: AppState) -> AppState:
    """设计节点

    根据 design_type 调用对应的 DesignAgent。
    """
    try:
        design_type = state.get("design_type", "")
        user_input = state.get("user_input", "")
        history = state.get("conversation_history", [])
        current_form_data = state.get("current_form_data", {})

        if not design_type:
            state["design_error"] = "未指定 design_type"
            return state

        if not user_input:
            state["design_error"] = "用户输入为空"
            return state

        # 调用对应的 DesignAgent
        if design_type == "category":
            result = _design_category(user_input, history, current_form_data)
        elif design_type == "flow":
            result = _design_flow(user_input, history, current_form_data, state)
        elif design_type == "form":
            result = _design_form(user_input, history, current_form_data)
        else:
            state["design_error"] = f"不支持的 design_type: {design_type}"
            return state

        # 将结果存入状态
        if result.get("error"):
            state["design_error"] = result["error"]
            state["design_success"] = False
        else:
            _store_result(state, design_type, result)
            state["design_success"] = True
            state["raw_result"] = result

        return state

    except Exception as e:
        logger.error(f"设计节点执行失败：{e}")
        state["design_error"] = str(e)
        state["design_success"] = False
        return state


def _design_category(
    user_input: str,
    history: list[dict],
    current_form_data: dict,
) -> dict[str, Any]:
    """调用分类设计 Agent"""
    agent = DesignCategoryAgent()
    result = agent.generate(
        user_input=user_input,
        history=history,
        current_form_data=current_form_data
    )
    return result


def _design_flow(
    user_input: str,
    history: list[dict],
    current_form_data: dict,
    state: AppState,
) -> dict[str, Any]:
    """调用流程设计 Agent"""
    agent = DesignFlowAgent()
    mode = state.get("mode", "create")
    result = agent.generate(
        user_input=user_input,
        history=history,
        current_form_data=current_form_data,
        mode=mode
    )
    return result


def _design_form(
    user_input: str,
    history: list[dict],
    current_form_data: dict,
) -> dict[str, Any]:
    """调用表单设计 Agent"""
    agent = DesignFormAgent()
    result = agent.generate(
        user_input=user_input,
        history=history,
        current_form_data=current_form_data
    )
    return result


def _store_result(state: AppState, design_type: str, result: dict[str, Any]) -> None:
    """将 Agent 结果存储到状态
    统一存储到 state["design_output"]，供 review_node 和 format_node 使用。
    存储完整 result，保留 flow_name/category_id/nodes 等字段供审查使用。
    """
    state["design_output"] = result
