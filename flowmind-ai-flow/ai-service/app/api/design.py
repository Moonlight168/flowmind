"""
FlowMind 智能流程设计服务 - 设计 API

本模块提供分类设计、流程设计、表单设计等统一的设计接口。
"""
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import require_auth
from app.domain.dto import ResponseVO
from app.domain.dto.design_request import DesignRequestDTO
from app.graph.workflows.design_workflow import invoke_design_workflow
from app.infra.logger import generate_trace_id, set_trace_id
from app.utils.auth import TokenUser

router = APIRouter(prefix="/design", tags=["设计"])


@router.post("/category", response_model=ResponseVO[dict[str, Any]])
async def design_category(
    payload: DesignRequestDTO,
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[dict[str, Any]]:
    """分类设计接口"""
    trace_id = generate_trace_id()
    set_trace_id(trace_id)

    result = invoke_design_workflow(
        design_type="category",
        user_input=payload.user_input,
        thread_id=current_user.user_key or "default",
        trace_id=trace_id,
        conversation_history=payload.conversation_history,
        current_form_data=payload.current_form_data,
    )

    return ResponseVO.success(result, trace_id=trace_id)


@router.post("/flow", response_model=ResponseVO[dict[str, Any]])
async def design_flow(
    payload: DesignRequestDTO,
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[dict[str, Any]]:
    """流程设计接口"""
    trace_id = generate_trace_id()
    set_trace_id(trace_id)

    result = invoke_design_workflow(
        design_type="flow",
        user_input=payload.user_input,
        thread_id=current_user.user_key or "default",
        trace_id=trace_id,
        conversation_history=payload.conversation_history,
        current_form_data=payload.current_form_data,
        mode=payload.mode,
    )

    return ResponseVO.success(result, trace_id=trace_id)


@router.post("/form", response_model=ResponseVO[dict[str, Any]])
async def design_form(
    payload: DesignRequestDTO,
    current_user: TokenUser = Depends(require_auth),
) -> ResponseVO[dict[str, Any]]:
    """表单设计接口"""
    trace_id = generate_trace_id()
    set_trace_id(trace_id)

    result = invoke_design_workflow(
        design_type="form",
        user_input=payload.user_input,
        thread_id=current_user.user_key or "default",
        trace_id=trace_id,
        conversation_history=payload.conversation_history,
        current_form_data=payload.current_form_data,
    )

    return ResponseVO.success(result, trace_id=trace_id)
