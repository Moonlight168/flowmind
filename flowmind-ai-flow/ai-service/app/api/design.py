"""
FlowMind 智能流程设计服务 - 设计 API

本模块提供分类设计、流程设计、表单设计等统一的设计接口。
"""

import json
from hashlib import sha256
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import require_auth
from app.core.auth import TokenUser
from app.core.exceptions import FlowDesignException
from app.domain.dto import ResponseVO
from app.domain.dto.design_request import DesignRequestDTO
from app.graph.design_graph import (
    delete_design_thread,
    stream_design_workflow,
)
from app.infra.logger import generate_trace_id, set_trace_id

router = APIRouter(prefix="/design", tags=["设计"])
STREAM_ERRORS = (RuntimeError, ValueError, TypeError, FlowDesignException)
SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


def _safe_stream_error(trace_id: str) -> str:
    event = {
        "type": "error",
        "status": "error",
        "error_type": "internal",
        "retryable": True,
        "message": "AI 服务暂时异常，请稍后重试",
        "trace_id": trace_id,
    }
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def _sse_response(content: Any) -> StreamingResponse:
    return StreamingResponse(
        content, media_type="text/event-stream", headers=SSE_HEADERS
    )


def _design_thread_id(
    design_type: str,
    user_key: str,
    mode: str = "design",
    conversation_id: str | None = None,
) -> str:
    """Namespace a client conversation by user, artifact type and mode."""
    short = design_type.replace("_design", "")
    raw = f"{user_key}:{conversation_id or 'default'}"
    conversation_key = sha256(raw.encode()).hexdigest()[:16]
    return f"design_{short}_{mode}_{conversation_key}"


@router.post("/category")
def design_category(
    payload: DesignRequestDTO,
    current_user: TokenUser = Depends(require_auth),
) -> StreamingResponse:
    """分类设计接口（SSE：进度事件 + done 事件）"""
    trace_id = generate_trace_id()
    set_trace_id(trace_id)
    thread_id = _design_thread_id(
        "category_design", current_user.user_key, conversation_id=payload.thread_id
    )

    def event_stream():
        try:
            for event in stream_design_workflow(
                design_type="category_design",
                user_input=payload.user_input,
                thread_id=thread_id,
                trace_id=trace_id,
                current_form_data=payload.current_form_data,
                allow_full_replace=payload.allow_full_replace,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except STREAM_ERRORS:
            yield _safe_stream_error(trace_id)

    return _sse_response(event_stream())


@router.post("/flow")
def design_flow(
    payload: DesignRequestDTO,
    current_user: TokenUser = Depends(require_auth),
) -> StreamingResponse:
    """流程设计接口（SSE：进度事件 + done 事件）"""
    trace_id = generate_trace_id()
    set_trace_id(trace_id)
    thread_id = _design_thread_id(
        "flow_design",
        current_user.user_key,
        payload.mode,
        payload.thread_id,
    )

    def event_stream():
        try:
            for event in stream_design_workflow(
                design_type="flow_design",
                user_input=payload.user_input,
                thread_id=thread_id,
                trace_id=trace_id,
                current_form_data=payload.current_form_data,
                mode=payload.mode,
                allow_full_replace=payload.allow_full_replace,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except STREAM_ERRORS:
            yield _safe_stream_error(trace_id)

    return _sse_response(event_stream())


@router.post("/form")
def design_form(
    payload: DesignRequestDTO,
    current_user: TokenUser = Depends(require_auth),
) -> StreamingResponse:
    """表单设计接口（SSE：进度事件 + done 事件）"""
    trace_id = generate_trace_id()
    set_trace_id(trace_id)
    thread_id = _design_thread_id(
        "form_design", current_user.user_key, conversation_id=payload.thread_id
    )

    def event_stream():
        try:
            for event in stream_design_workflow(
                design_type="form_design",
                user_input=payload.user_input,
                thread_id=thread_id,
                trace_id=trace_id,
                current_form_data=payload.current_form_data,
                allow_full_replace=payload.allow_full_replace,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except STREAM_ERRORS:
            yield _safe_stream_error(trace_id)

    return _sse_response(event_stream())


@router.delete("/state/{design_type}", response_model=ResponseVO[dict[str, Any]])
async def delete_design_state(
    design_type: str,
    thread_id: str | None = None,
    mode: str = "design",
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[dict[str, Any]]:
    """删除设计会话（thread_id 可选，不传则删除默认会话）"""
    tid = _design_thread_id(design_type, current_user.user_key, mode, thread_id)
    delete_design_thread(tid)
    return ResponseVO.success({"thread_id": tid})
