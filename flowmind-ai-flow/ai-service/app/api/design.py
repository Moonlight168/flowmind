"""
FlowMind 智能流程设计服务 - 设计 API

本模块提供分类设计、流程设计、表单设计等统一的设计接口。

三个流式端点只捕获可预期的业务、网络和输入异常并转换为 error 事件；未知异常
继续抛出，避免掩盖程序错误。
"""

import json
from hashlib import sha256
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api._sse import to_async_stream
from app.api.deps import require_auth
from app.core.auth import TokenUser
from app.core.exceptions import EXPECTED_RUNTIME_ERRORS, ErrorCode
from app.domain.dto import ResponseVO
from app.domain.dto.design_request import DesignRequestDTO, RollbackRequestDTO
from app.graph.design_graph import (
    delete_design_thread,
    stream_design_workflow,
)
from app.infra.checkpoint import checkpointer
from app.infra.logger import generate_trace_id, logger, set_trace_id

router = APIRouter(prefix="/design", tags=["设计"])
SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


def _safe_stream_error(trace_id: str) -> str:
    event = {
        "type": "error",
        "status": "error",
        "error_type": ErrorCode.INTERNAL.value,
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
    user: TokenUser,
    mode: str = "design",
    conversation_id: str | None = None,
) -> str:
    """Namespace a client conversation by user, artifact type and mode.

    隔离键使用 user_id（登录会话无关的稳定标识），避免重新登录后
    user_key 变化导致 AI 上下文断裂。
    """
    short = design_type.replace("_design", "")
    raw = f"{user.user_id or user.user_key}:{conversation_id or 'default'}"
    conversation_key = sha256(raw.encode()).hexdigest()[:16]
    return f"design_{short}_{mode}_{conversation_key}"


def _run_design_stream(
    design_type: str,
    payload: DesignRequestDTO,
    current_user: TokenUser,
    *,
    mode: str = "design",
) -> StreamingResponse:
    """三个设计端点的共享执行体：会话命名 → SSE 进度/错误事件流。"""
    trace_id = generate_trace_id()
    set_trace_id(trace_id)
    thread_id = _design_thread_id(
        design_type, current_user, mode, payload.thread_id
    )

    def event_stream():
        try:
            for event in stream_design_workflow(
                design_type=design_type,
                user_input=payload.user_input,
                thread_id=thread_id,
                trace_id=trace_id,
                current_form_data=payload.current_form_data,
                mode=payload.mode,
                history_count=payload.history_count,
                allow_full_replace=payload.allow_full_replace,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except EXPECTED_RUNTIME_ERRORS as exc:
            # 兜底捕获全部异常：白名单外的异常类型（如 XML 解析错误）
            # 会穿透到桥接层导致流静默截断，这里统一转为 error 事件并记日志。
            logger.error(f"设计流式处理异常: {exc}", exc_info=True)
            yield _safe_stream_error(trace_id)

    return _sse_response(to_async_stream(event_stream()))


@router.post("/category")
def design_category(
    payload: DesignRequestDTO,
    current_user: TokenUser = Depends(require_auth),
) -> StreamingResponse:
    """分类设计接口（SSE：进度事件 + done 事件）"""
    return _run_design_stream("category_design", payload, current_user)


@router.post("/flow")
def design_flow(
    payload: DesignRequestDTO,
    current_user: TokenUser = Depends(require_auth),
) -> StreamingResponse:
    """流程设计接口（SSE：进度事件 + done 事件）"""
    return _run_design_stream(
        "flow_design", payload, current_user, mode=payload.mode
    )


@router.post("/form")
def design_form(
    payload: DesignRequestDTO,
    current_user: TokenUser = Depends(require_auth),
) -> StreamingResponse:
    """表单设计接口（SSE：进度事件 + done 事件）"""
    return _run_design_stream("form_design", payload, current_user)


@router.delete("/state/{design_type}", response_model=ResponseVO[dict[str, Any]])
async def delete_design_state(
    design_type: str,
    thread_id: str | None = None,
    mode: str = "design",
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[dict[str, Any]]:
    """删除设计会话（thread_id 可选，不传则删除默认会话）"""
    tid = _design_thread_id(design_type, current_user, mode, thread_id)
    delete_design_thread(tid)
    return ResponseVO.success({"thread_id": tid})


@router.post("/state/{design_type}/rollback", response_model=ResponseVO[dict[str, Any]])
async def rollback_design_state(
    design_type: str,
    payload: RollbackRequestDTO,
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[dict[str, Any]]:
    """回退设计会话历史：把 checkpoint 的 messages 裁剪到 message_count 条。"""
    tid = _design_thread_id(design_type, current_user, payload.mode, payload.thread_id)
    checkpointer.trim_messages(tid, payload.message_count)
    return ResponseVO.success({"thread_id": tid})
