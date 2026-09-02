"""
FlowMind 智能流程设计服务 - 对话 API

本模块提供通用聊天接口和会话历史管理。
"""

import json
from collections.abc import Iterator
from typing import Any

import httpx
import redis
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openai import OpenAIError

from app.api.deps import require_auth
from app.core.auth import TokenUser
from app.domain.dto import ChatRequestDTO, ResponseVO
from app.graph.chat_graph import (
    chat_workflow,
    get_chat_workflow_state,
    invoke_chat_workflow,
    stream_chat_workflow,
)
from app.infra.logger import generate_trace_id, logger, set_trace_id
from app.llm import PartialStreamError

router = APIRouter(
    prefix="/chat",
    tags=["对话"],
)


@router.post("", response_model=ResponseVO[dict[str, Any]])
def chat(
    payload: ChatRequestDTO,
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[dict[str, Any]]:
    """通用聊天接口"""
    trace_id = generate_trace_id()
    set_trace_id(trace_id)

    thread_id = payload.thread_id or current_user.user_key or "default"

    result = invoke_chat_workflow(
        user_input=payload.user_input,
        thread_id=thread_id,
        trace_id=trace_id,
    )

    # 提取 chat_response
    chat_response = result.get("chat_response", "") if isinstance(result, dict) else ""

    return ResponseVO.success(
        {
            "response": chat_response,
            "thread_id": thread_id,
        },
        trace_id=trace_id,
    )


@router.post("/stream")
def chat_stream(
    payload: ChatRequestDTO,
    current_user: TokenUser = Depends(require_auth),
) -> StreamingResponse:
    """通用聊天流式接口（SSE：meta + delta + done）。"""
    trace_id = generate_trace_id()
    set_trace_id(trace_id)
    thread_id = payload.thread_id or current_user.user_key or "default"

    def event_stream() -> Iterator[str]:
        meta = {"type": "meta", "thread_id": thread_id, "trace_id": trace_id}
        yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"
        try:
            for event in stream_chat_workflow(
                user_input=payload.user_input,
                thread_id=thread_id,
                trace_id=trace_id,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except (
            OpenAIError,
            httpx.HTTPError,
            redis.RedisError,
            RuntimeError,
            ValueError,
            OSError,
            PartialStreamError,
        ) as exc:
            logger.error(f"[chat-stream] 流式调用失败: {exc}")
            error = {"type": "error", "message": "AI 服务暂时异常，请稍后重试"}
            yield f"data: {json.dumps(error, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/state/{thread_id}", response_model=ResponseVO[dict[str, Any]])
async def get_chat_state(
    thread_id: str,
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[dict[str, Any]]:
    """获取会话状态和消息历史"""
    state = get_chat_workflow_state(thread_id)
    if state is None:
        return ResponseVO.error("会话不存在或已过期", code=404)

    return ResponseVO.success({"messages": state.get("messages", [])})


@router.delete("/state/{thread_id}", response_model=ResponseVO[dict[str, Any]])
async def delete_chat_state(
    thread_id: str,
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[dict[str, Any]]:
    """删除会话"""
    try:
        checkpointer = chat_workflow.checkpointer
        if hasattr(checkpointer, "delete_thread"):
            checkpointer.delete_thread(thread_id)
        return ResponseVO.success({"thread_id": thread_id})
    except Exception as e:
        return ResponseVO.error(500, f"删除失败: {e!s}")


@router.post("/state/batch-delete", response_model=ResponseVO[dict[str, Any]])
async def batch_delete_chat_state(
    thread_ids: list[str],
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[dict[str, Any]]:
    """批量删除会话"""
    try:
        checkpointer = chat_workflow.checkpointer
        deleted_count = 0
        for thread_id in thread_ids:
            if hasattr(checkpointer, "delete_thread"):
                checkpointer.delete_thread(thread_id)
                deleted_count += 1
        return ResponseVO.success({"deleted_count": deleted_count})
    except Exception as e:
        return ResponseVO.error(f"批量删除失败: {e!s}")


@router.get("/history", response_model=ResponseVO[list[dict[str, Any]]])
async def get_chat_history(
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[list[dict[str, Any]]]:
    """获取会话历史列表"""
    try:
        checkpointer = chat_workflow.checkpointer
        if not hasattr(checkpointer, "list_threads"):
            return ResponseVO.success([])

        threads = checkpointer.list_threads(limit=100)
        # list_threads 已返回 {thread_id, ns, preview, updated_at}
        result = [
            {
                "thread_id": t.get("thread_id", ""),
                "preview": t.get("preview", "新对话"),
                "updated_at": t.get("updated_at", None),
            }
            for t in threads
            if t.get("thread_id")
        ]
        return ResponseVO.success(result)
    except Exception as e:
        return ResponseVO.error(f"获取历史失败: {e!s}")
