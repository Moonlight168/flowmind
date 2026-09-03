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

from collections.abc import Iterator
from contextlib import contextmanager
from secrets import token_hex
from typing import Any

import redis
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from app.config.settings import settings
from app.core.exceptions import FlowDesignException
from app.design.bpmn_parser import enrich_flow_baseline
from app.design.operations import normalize_design_baseline
from app.graph.nodes.finalize import finalize_node
from app.graph.nodes.generate import generate_node
from app.graph.nodes.review import review_node
from app.graph.state import AppState
from app.infra.checkpoint import checkpointer
from app.infra.logger import generate_trace_id, log_context, logger
from app.infra.observability import (
    langchain_config,
    observe_workflow,
    record_observation_output,
)
from app.integrations.backend import request_cache
from app.prompts import prompt_release

LOCK_TTL_SECONDS = 600
_RELEASE_LOCK_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
end
return 0
"""

_redis_client: redis.Redis | None = None


def _get_redis_client() -> redis.Redis:
    """锁专用 Redis 客户端（懒加载单例，避免每请求新建连接池）"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            password=settings.redis.password,
            decode_responses=True,
        )
    return _redis_client


@contextmanager
def _thread_lock(thread_id: str) -> Iterator[None]:
    """按 thread_id 加分布式锁，防止并发重复执行"""
    lock_key = f"lock:design:{thread_id}"
    lock_token = token_hex(16)
    redis_client = _get_redis_client()
    try:
        acquired = redis_client.set(lock_key, lock_token, nx=True, ex=LOCK_TTL_SECONDS)
    except redis.RedisError as exc:
        raise FlowDesignException(
            "会话锁服务暂时不可用，请稍后重试", stage="lock"
        ) from exc
    if not acquired:
        raise FlowDesignException("请等待上一个请求完成后再发起新请求", stage="lock")
    try:
        yield
    finally:
        try:
            redis_client.eval(_RELEASE_LOCK_SCRIPT, 1, lock_key, lock_token)
        except redis.RedisError as exc:
            logger.warning(f"[lock] 释放失败，等待 TTL 自动清理: {exc}")


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
    if (
        intent == "success"
        and not review_passed
        and review_retry_count < settings.validation.review_max_retry_count
    ):
        return "design"

    # 其他情况（错误 或 超重试）= 结束
    return "format"


def create_design_workflow() -> StateGraph:
    workflow = StateGraph(AppState)

    workflow.add_node("design", generate_node)
    workflow.add_node("review", review_node)
    workflow.add_node("format", finalize_node)

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
    allow_full_replace: bool,
    kwargs: dict,
) -> tuple[dict, str, AppState]:
    """准备 config 与 initial_state（invoke 与 stream 共用）"""
    config = {"configurable": {"thread_id": thread_id}}
    auth_token = kwargs.get("auth_token")
    if auth_token:
        config["configurable"]["auth_token"] = auth_token
    if not trace_id:
        trace_id = generate_trace_id()

    # flow_design：前端可视化设计器只传 bpmn_xml 时，反解析为扁平 nodes/edges 基线，
    # 使 prompt 的增量语义与 BaselineValidator 真正生效（不把整段 XML 塞给模型）。
    if design_type == "flow_design":
        current_form_data = enrich_flow_baseline(current_form_data or {})
    current_form_data = normalize_design_baseline(design_type, current_form_data or {})
    # messages 用 add_messages reducer，自动追加到 checkpoint 现有消息
    initial_state: AppState = {
        "messages": [HumanMessage(content=user_input)],
        "current_form_data": current_form_data or {},
        "design_type": design_type,
        "mode": mode,
        "allow_full_replace": allow_full_replace,
        "intent": "clarification",
        "review_retry_count": 0,
        "review_error_history": [],
    }
    return config, trace_id, initial_state


def invoke_design_workflow(
    design_type: str,
    user_input: str,
    thread_id: str,
    trace_id: str | None = None,
    current_form_data: dict | None = None,
    mode: str = "design",
    allow_full_replace: bool = False,
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
        allow_full_replace,
        kwargs,
    )

    logger.info(f"[invoke] 开始执行 design_type={design_type}, thread_id={thread_id}")

    with (
        prompt_release(thread_id),
        request_cache.scope(),
        _thread_lock(thread_id),
        log_context(trace_id=trace_id, request_id=thread_id[:8] if thread_id else None),
        observe_workflow(
            "flowmind.design",
            input={
                "design_type": design_type,
                "mode": mode,
                "user_input": user_input,
                "current_form_data": current_form_data or {},
                "allow_full_replace": allow_full_replace,
            },
            session_id=thread_id,
            trace_id=trace_id,
            metadata={
                "design_type": design_type,
                "mode": mode,
                "stream": False,
                "allow_full_replace": allow_full_replace,
            },
            tags=["design", design_type, mode],
        ) as observation,
    ):
        result = design_workflow.invoke(initial_state, langchain_config(config))

        # 从最终状态提取 design_output
        if isinstance(result, dict):
            design_output = result.get("design_output", {})
            if design_output:
                design_output["trace_id"] = trace_id
                record_observation_output(observation, design_output)
                logger.info(f"[invoke] 完成, intent={result.get('intent')}")
                return design_output

        record_observation_output(observation, result)
        logger.warning(
            f"[invoke] 无 design_output, result_keys={list(result.keys()) if isinstance(result, dict) else type(result)}"
        )
        return result


def stream_design_workflow(
    design_type: str,
    user_input: str,
    thread_id: str,
    trace_id: str | None = None,
    current_form_data: dict | None = None,
    mode: str = "design",
    allow_full_replace: bool = False,
    **kwargs,
) -> Iterator[dict[str, Any]]:
    """流式设计 Workflow：逐个 yield 进度事件，最后 yield done 事件（含完整 design_output）"""
    config, trace_id, initial_state = _prepare_design_call(
        design_type,
        user_input,
        thread_id,
        trace_id,
        current_form_data,
        mode,
        allow_full_replace,
        kwargs,
    )

    max_retry = settings.validation.review_max_retry_count
    logger.info(f"[stream] 开始执行 design_type={design_type}, thread_id={thread_id}")

    with (
        prompt_release(thread_id),
        request_cache.scope(),
        _thread_lock(thread_id),
        log_context(trace_id=trace_id, request_id=thread_id[:8] if thread_id else None),
        observe_workflow(
            "flowmind.design",
            input={
                "design_type": design_type,
                "mode": mode,
                "user_input": user_input,
                "current_form_data": current_form_data or {},
                "allow_full_replace": allow_full_replace,
            },
            session_id=thread_id,
            trace_id=trace_id,
            metadata={
                "design_type": design_type,
                "mode": mode,
                "stream": True,
                "allow_full_replace": allow_full_replace,
            },
            tags=["design", design_type, mode, "stream"],
        ) as observation,
    ):
        design_count = 0
        last_error_count = 0
        for step in design_workflow.stream(
            initial_state, langchain_config(config), stream_mode="updates"
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
                        (node_state or {}).get("design_output", {}).get("review", {})
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
            (final_state.values or {}).get("design_output", {}) if final_state else {}
        )
        if isinstance(design_output, dict):
            design_output["trace_id"] = trace_id
        record_observation_output(observation, design_output)
        yield {
            "type": "done",
            **(design_output if isinstance(design_output, dict) else {}),
        }


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
