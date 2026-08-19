"""
FlowMind 智能审批服务 - 设计 Workflow

简化版工作流设计：
- design_node: 调用 LLM 生成内容，追加 AI 回复到 messages
- review_node: 审查输出，失败时注入错误反馈到 messages 并重试
- format_node: 统一格式化输出

状态管理：
- messages: 唯一的历史记录，所有节点都追加到它
- design_type/mode: 仅在首次设置，后续从 checkpoint 恢复
- intent: 标识最终结果类型 (clarification/success/error)
"""

import redis
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.config.settings import settings
from app.core.checkpoint.redis_checkpoint import RedisCheckpoint
from app.graph.nodes.format_node import format_node
from app.graph.nodes.react_agent_node import react_agent_node
from app.graph.nodes.review_node import review_node
from app.graph.state.app_state import AppState
from app.infra.logger import generate_trace_id, log_context, logger

LOCK_TTL_SECONDS = 120


def _get_redis_client() -> redis.Redis:
    return redis.Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        password=settings.redis.password,
        decode_responses=True,
    )


# 创建全局检查点存储
try:
    checkpointer = RedisCheckpoint()
except Exception as exc:
    if not settings.app.debug:
        raise RuntimeError("Redis checkpoint 初始化失败，生产环境禁止降级") from exc
    logger.warning(f"Redis checkpoint 初始化失败，降级到 MemorySaver: {exc!s}")
    checkpointer = MemorySaver()


def _result_router(state: AppState) -> str:
    """根据 intent 路由到对应节点

    - intent == "success" + review_passed: 成功，格式化
    - intent == "success" + !review_passed: 审查失败，重试 design
    - intent == "error" 或超重试: 结束
    """
    intent = state.get("intent", "clarification")
    design_output = state.get("design_output") or {}
    review_info = design_output.get("review", {})
    review_passed = review_info.get("passed", True)
    review_retry_count = state.get("review_retry_count") or 0

    logger.info(
        f"[router] intent={intent}, review_passed={review_passed}, retry={review_retry_count}"
    )

    # 成功 + 审查通过 = 结束
    if intent == "success" and review_passed:
        return "format"

    # 成功 + 审查失败 + 未超重试次数 = 重试
    if intent == "success" and not review_passed and review_retry_count < 3:
        return "design"

    # 其他情况（错误 或 超重试）= 结束
    return "format"


def create_design_workflow() -> StateGraph:
    workflow = StateGraph(AppState)

    workflow.add_node("design", react_agent_node)
    workflow.add_node("review", review_node)
    workflow.add_node("format", format_node)

    workflow.set_entry_point("design")

    # design → review/format 的条件路由
    # clarification 和 error 直接进入 format，success 进入 review
    workflow.add_conditional_edges(
        "design",
        lambda state: (
            "format" if state.get("intent") in ("clarification", "error") else "review"
        ),
        {"review": "review", "format": "format"},
    )

    workflow.add_conditional_edges(
        "review",
        _result_router,
        {
            "design": "design",
            "format": "format",
        },
    )

    workflow.add_edge("format", END)

    return workflow.compile(checkpointer=checkpointer)


design_workflow = create_design_workflow()


def _prepare_design_call(
    design_type: str,
    user_input: str,
    thread_id: str,
    trace_id: str | None,
    current_form_data: dict | None,
    mode: str,
    kwargs: dict,
) -> tuple[dict, str, AppState]:
    """准备 config 与 initial_state（invoke 与 stream 共用）"""
    config = {"configurable": {"thread_id": thread_id}}
    auth_token = kwargs.get("auth_token")
    if auth_token:
        config["configurable"]["auth_token"] = auth_token
    if not trace_id:
        trace_id = generate_trace_id()

    is_first_call = not checkpointer.thread_exists(thread_id)
    # messages 用 add_messages reducer，自动追加到 checkpoint 现有消息
    initial_state: AppState = {
        "messages": [HumanMessage(content=user_input)],
        "current_form_data": current_form_data or {},
    }
    # design_type/mode 只在首次设置，后续从 checkpoint 恢复
    if is_first_call:
        initial_state["design_type"] = design_type
        initial_state["mode"] = mode
        initial_state["intent"] = "clarification"
    else:
        logger.debug(f"[design] 从 checkpoint 恢复 thread_id={thread_id}")
    return config, trace_id, initial_state


def invoke_design_workflow(
    design_type: str,
    user_input: str,
    thread_id: str,
    trace_id: str | None = None,
    current_form_data: dict | None = None,
    mode: str = "design",
    **kwargs,
) -> dict:
    """设计 Workflow 调用入口（同步，返回最终 design_output）"""
    config, trace_id, initial_state = _prepare_design_call(
        design_type,
        user_input,
        thread_id,
        trace_id,
        current_form_data,
        mode,
        kwargs,
    )

    lock_key = f"lock:design:{thread_id}"
    redis_client = _get_redis_client()
    acquired = redis_client.set(lock_key, "1", nx=True, ex=LOCK_TTL_SECONDS)

    if not acquired:
        raise RuntimeError("请等待上一个请求完成后再发起新请求")

    logger.info(f"[invoke] 开始执行 design_type={design_type}, thread_id={thread_id}")

    try:
        with log_context(
            trace_id=trace_id, request_id=thread_id[:8] if thread_id else None
        ):
            result = design_workflow.invoke(initial_state, config)

            # 从最终状态提取 design_output
            if isinstance(result, dict):
                design_output = result.get("design_output", {})
                if design_output:
                    logger.info(f"[invoke] 完成, intent={result.get('intent')}")
                    return design_output

            logger.warning(
                f"[invoke] 无 design_output, result_keys={list(result.keys()) if isinstance(result, dict) else type(result)}"
            )
            return result
    finally:
        redis_client.delete(lock_key)


def stream_design_workflow(
    design_type: str,
    user_input: str,
    thread_id: str,
    trace_id: str | None = None,
    current_form_data: dict | None = None,
    mode: str = "design",
    **kwargs,
):
    """流式设计 Workflow：逐个 yield 进度事件，最后 yield done 事件（含完整 design_output）"""
    config, trace_id, initial_state = _prepare_design_call(
        design_type,
        user_input,
        thread_id,
        trace_id,
        current_form_data,
        mode,
        kwargs,
    )

    lock_key = f"lock:design:{thread_id}"
    redis_client = _get_redis_client()
    acquired = redis_client.set(lock_key, "1", nx=True, ex=LOCK_TTL_SECONDS)
    if not acquired:
        raise RuntimeError("请等待上一个请求完成后再发起新请求")

    max_retry = settings.validation.review_max_retry_count
    logger.info(f"[stream] 开始执行 design_type={design_type}, thread_id={thread_id}")

    try:
        with log_context(
            trace_id=trace_id, request_id=thread_id[:8] if thread_id else None
        ):
            design_count = 0
            last_error_count = 0
            for step in design_workflow.stream(
                initial_state, config, stream_mode="updates"
            ):
                for node_name, node_state in step.items():
                    if node_name == "design":
                        design_count += 1
                        if design_count == 1:
                            yield {
                                "type": "progress",
                                "phase": "design",
                                "message": "正在理解需求并生成流程结构",
                            }
                        else:
                            yield {
                                "type": "progress",
                                "phase": "design",
                                "message": f"发现 {last_error_count} 处问题，正在修正（第 {design_count - 1}/{max_retry} 次）",
                            }
                    elif node_name == "review":
                        yield {
                            "type": "progress",
                            "phase": "review",
                            "message": "正在校验流程结构",
                        }
                        review_info = (
                            (node_state or {})
                            .get("design_output", {})
                            .get("review", {})
                            if isinstance(node_state, dict)
                            else {}
                        )
                        last_error_count = len(review_info.get("errors", []))
                    elif node_name == "format":
                        yield {
                            "type": "progress",
                            "phase": "format",
                            "message": "正在组装结果",
                        }

            final_state = design_workflow.get_state(config)
            design_output = (
                (final_state.values or {}).get("design_output", {})
                if final_state
                else {}
            )
            yield {
                "type": "done",
                **(design_output if isinstance(design_output, dict) else {}),
            }
    finally:
        redis_client.delete(lock_key)


def delete_design_thread(thread_id: str) -> None:
    """删除设计对话历史"""
    try:
        checkpointer.delete_thread(thread_id)
        logger.info(f"删除设计对话: thread_id={thread_id}")
    except Exception as e:
        logger.warning(f"删除设计对话失败: {e}")


__all__ = [
    "checkpointer",
    "create_design_workflow",
    "delete_design_thread",
    "design_workflow",
    "invoke_design_workflow",
    "stream_design_workflow",
]
