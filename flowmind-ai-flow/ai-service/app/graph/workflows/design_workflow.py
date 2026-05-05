"""
FlowMind 智能流程设计服务 - 设计 Workflow

统一的流程/表单/分类设计 Workflow，包含：
- design_node: 调用 DesignAgent 生成内容
- review_node: 审查输出质量（失败时自动重试）
- format_node: 包装元数据信封
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.config.settings import settings
from app.core.checkpoint.redis_checkpoint import RedisCheckpoint
from app.graph.nodes.design_node import design_node
from app.graph.nodes.format_node import format_node
from app.graph.nodes.review_node import review_node
from app.graph.state.app_state import AppState
from app.infra.logger import generate_trace_id, log_context, logger

# 创建全局检查点存储
try:
    checkpointer = RedisCheckpoint()
except Exception as exc:
    if not settings.app.debug:
        raise RuntimeError("Redis checkpoint 初始化失败，生产环境禁止降级") from exc

    logger.warning(f"Redis checkpoint 初始化失败，降级到 MemorySaver: {exc!s}")
    checkpointer = MemorySaver()


def _review_router(state: AppState) -> str:
    """审查路由：通过则进入 format，未通过且未超重试次数则回到 design"""
    if state.get("review_passed", True):
        return "format"
    if (state.get("review_retry_count") or 0) < 2:
        return "design"
    return "format"


def create_design_workflow() -> StateGraph:
    """创建设计 Workflow"""
    workflow = StateGraph(AppState)

    # 添加节点
    workflow.add_node("design", design_node)
    workflow.add_node("review", review_node)
    workflow.add_node("format", format_node)

    # 设置入口和结束
    workflow.set_entry_point("design")
    workflow.add_edge("design", "review")
    workflow.add_conditional_edges("review", _review_router, {
        "design": "design",
        "format": "format",
    })
    workflow.add_edge("format", END)

    return workflow.compile(checkpointer=checkpointer)


design_workflow = create_design_workflow()


def invoke_design_workflow(
    design_type: str,
    user_input: str,
    thread_id: str,
    trace_id: str | None = None,
    conversation_history: list[dict] | None = None,
    current_form_data: dict | None = None,
    mode: str = "create",
    **kwargs,
) -> dict:
    """设计 Workflow 调用入口

    Args:
        design_type: 设计类型 (category/flow/form)
        user_input: 用户输入
        thread_id: 线程 ID
        trace_id: 追踪 ID
        conversation_history: 对话历史
        current_form_data: 当前表单数据
        mode: 设计模式 (create/update)
    """
    config = {"configurable": {"thread_id": thread_id}}

    auth_token = kwargs.get("auth_token")
    if auth_token:
        config["configurable"]["auth_token"] = auth_token

    if not trace_id:
        trace_id = generate_trace_id()

    initial_state: AppState = {
        "design_type": design_type,
        "user_input": user_input,
        "trace_id": trace_id,
        "thread_id": thread_id,
        "conversation_history": conversation_history or [],
        "current_form_data": current_form_data or {},
        "mode": mode,
        "schema_name": _get_schema_name(design_type),
    }

    with log_context(trace_id=trace_id, request_id=thread_id[:8] if thread_id else None):
        if settings.app.debug:
            result = None
            for step in design_workflow.stream(initial_state, config):
                result = step
            if result and "__interrupt__" in result:
                pass
            else:
                final_state = design_workflow.get_state(config)
                result = final_state.values if final_state else {}
        else:
            result = design_workflow.invoke(initial_state, config)

        # 提取格式化结果（含元数据信封）
        if isinstance(result, dict) and "formatted_result" in result:
            return result["formatted_result"]
        return result


def _get_schema_name(design_type: str) -> str:
    """获取设计类型对应的 Schema 名称"""
    schema_map = {
        "category": "category_classification",
        "flow": "flow_design",
        "form": "form_generation",
    }
    return schema_map.get(design_type, "")


__all__ = [
    "create_design_workflow",
    "design_workflow",
    "invoke_design_workflow",
]
