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

from app.adapters.factory import ModelFactory
from app.domain.dto import ResponseVO
from app.infra.logger import log_api_endpoint

router = APIRouter(
    prefix="/health",
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=ResponseVO[dict[str, str]])
@log_api_endpoint()
def health_check(request: Request) -> ResponseVO[dict[str, str]]:
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
def model_health_check(request: Request) -> ResponseVO[dict[str, Any]]:
    """模型适配器状态接口"""
    manager = ModelFactory.get_model_manager()
    adapters = manager.get_available_adapters_info()
    current_adapter = manager.get_current_adapter()

    total_count = len(adapters)

    return ResponseVO.success(
        {
            "status": "healthy" if total_count > 0 else "unhealthy",
            "current_adapter": current_adapter,
            "total_count": total_count,
            "adapters": adapters,
            "timestamp": datetime.now().isoformat(),
        }
    )
