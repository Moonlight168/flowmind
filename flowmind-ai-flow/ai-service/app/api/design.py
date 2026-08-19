"""
FlowMind 智能流程设计服务 - 设计 API

本模块提供分类设计、流程设计、表单设计等统一的设计接口。
"""
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import require_auth
from app.domain.dto import ResponseVO
from app.domain.dto.design_request import DesignRequestDTO
from app.graph.workflows.design_workflow import (
    delete_design_thread,
    invoke_design_workflow,
)
from app.infra.logger import generate_trace_id, set_trace_id
from app.utils.auth import TokenUser

router = APIRouter(prefix="/design", tags=["设计"])


def _design_thread_id(design_type: str, user_key: str) -> str:
    """生成设计会话 thread_id，兼容 category_design / category 两种写法"""
    short = design_type.replace("_design", "")
    return f"design_{short}_{user_key}"


@router.post("/category", response_model=ResponseVO[dict[str, Any]])
def design_category(
    payload: DesignRequestDTO,
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[dict[str, Any]]:
    """分类设计接口"""
    trace_id = generate_trace_id()
    set_trace_id(trace_id)

    thread_id = payload.thread_id or _design_thread_id("category_design", current_user.user_key)

    try:
        result = invoke_design_workflow(
            design_type="category_design",
            user_input=payload.user_input,
            thread_id=thread_id,
            trace_id=trace_id,
            current_form_data=payload.current_form_data,
        )
    except RuntimeError as e:
        return ResponseVO.error(code=409, message=str(e), trace_id=trace_id)

    return ResponseVO.success(result, trace_id=trace_id)


@router.post("/flow", response_model=ResponseVO[dict[str, Any]])
def design_flow(
    payload: DesignRequestDTO,
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[dict[str, Any]]:
    """流程设计接口"""
    trace_id = generate_trace_id()
    set_trace_id(trace_id)

    thread_id = payload.thread_id or _design_thread_id("flow_design", current_user.user_key)

    try:
        result = invoke_design_workflow(
            design_type="flow_design",
            user_input=payload.user_input,
            thread_id=thread_id,
            trace_id=trace_id,
            current_form_data=payload.current_form_data,
            mode=payload.mode,
        )
    except RuntimeError as e:
        return ResponseVO.error(code=409, message=str(e), trace_id=trace_id)

    return ResponseVO.success(result, trace_id=trace_id)


@router.post("/form", response_model=ResponseVO[dict[str, Any]])
def design_form(
    payload: DesignRequestDTO,
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[dict[str, Any]]:
    """表单设计接口"""
    trace_id = generate_trace_id()
    set_trace_id(trace_id)

    thread_id = payload.thread_id or _design_thread_id("form_design", current_user.user_key)

    try:
        result = invoke_design_workflow(
            design_type="form_design",
            user_input=payload.user_input,
            thread_id=thread_id,
            trace_id=trace_id,
            current_form_data=payload.current_form_data,
        )
    except RuntimeError as e:
        return ResponseVO.error(code=409, message=str(e), trace_id=trace_id)

    return ResponseVO.success(result, trace_id=trace_id)


@router.delete("/state/{design_type}", response_model=ResponseVO[dict[str, Any]])
async def delete_design_state(
    design_type: str,
    thread_id: str | None = None,
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[dict[str, Any]]:
    """删除设计会话（thread_id 可选，不传则删除默认会话）"""
    tid = thread_id or _design_thread_id(design_type, current_user.user_key)
    delete_design_thread(tid)
    return ResponseVO.success({"thread_id": tid})
