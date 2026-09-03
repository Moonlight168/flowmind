"""
FlowMind 智能流程设计服务 - 健康检查API

本模块提供系统健康检查接口，用于监控服务运行状态。
主要功能：
1. 提供HTTP健康检查端点
2. 返回服务状态和时间戳信息
3. 支持负载均衡器和监控系统探测
4. 提供模型适配器健康状态

作者: wish168
版本: 1.0.0
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request

from app.domain.dto import ResponseVO
from app.infra.logger import log_api_endpoint
from app.llm import get_model_runtime

router = APIRouter(
    prefix="/health",
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=ResponseVO[dict[str, str]])
@log_api_endpoint()
async def health_check(request: Request) -> ResponseVO[dict[str, str]]:
    """健康检查接口"""
    return ResponseVO.success(
        {
            "status": "healthy",
            "service": "flowmind-ai-flow",
            "timestamp": datetime.now().isoformat(),
        }
    )


@router.get("/models", response_model=ResponseVO[dict[str, Any]])
@log_api_endpoint()
async def model_health_check(request: Request) -> ResponseVO[dict[str, Any]]:
    """返回脱敏后的模型配置与结构化能力状态。"""
    providers = get_model_runtime().describe_providers()
    total_count = len(providers)
    structured_count = sum(
        bool(provider["supports_structured_output"]) for provider in providers
    )

    return ResponseVO.success(
        {
            "status": "configured" if total_count > 0 else "unconfigured",
            "primary_provider": providers[0]["name"] if providers else None,
            "total_count": total_count,
            "structured_provider_count": structured_count,
            "structured_fallback_ready": structured_count >= 2,
            "providers": providers,
            "timestamp": datetime.now().isoformat(),
        }
    )
