"""
FlowMind 智能流程设计服务 - 异常处理

本模块定义统一异常处理体系，提供异常类定义和全局异常处理器。
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.domain.dto import ResponseVO
from app.infra.logger import get_trace_id, logger

# ============== 异常基类 ==============


class AIApprovalException(Exception):  # noqa: N818 - 既有命名，改 Error 后缀会影响继承类与调用方
    """AI 智能流程设计服务业务异常基类

    所有业务异常都应继承此类，以便统一处理。
    """

    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def to_error_response(self) -> dict[str, Any]:
        """转换为错误响应格式。"""
        return ResponseVO.error(
            code=self.status_code,
            message=self.message,
            trace_id=get_trace_id(),
        ).model_dump()


# ============== 具体异常类型 ==============


class FlowDesignException(AIApprovalException):
    """流程设计异常

    当流程设计或修改失败时抛出。
    """

    def __init__(
        self,
        message: str,
        stage: str | None = None,
    ):
        details = {}
        if stage:
            details["stage"] = stage

        super().__init__(
            message=message,
            error_code="FLOW_DESIGN_ERROR",
            status_code=500,
            details=details,
        )


class ValidationException(AIApprovalException):
    """参数验证异常

    当请求参数验证失败时抛出。
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
    ):
        details = {}
        if field:
            details["field"] = field

        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details,
        )


class ResourceNotFoundException(AIApprovalException):
    """资源未找到异常

    当请求的资源不存在时抛出。
    """

    def __init__(
        self,
        resource_type: str,
        resource_id: str | None = None,
    ):
        message = f"{resource_type}不存在"
        if resource_id:
            message += f" (ID: {resource_id})"

        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )


class ServiceUnavailableException(AIApprovalException):
    """服务不可用异常

    当依赖的外部服务不可用时抛出。
    """

    def __init__(
        self,
        service_name: str,
        reason: str | None = None,
    ):
        details = {"service_name": service_name}
        message = f"服务 {service_name} 不可用"
        if reason:
            message += f": {reason}"
            details["reason"] = reason

        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            status_code=503,
            details=details,
        )


class ConfigurationException(AIApprovalException):
    """配置异常

    当配置错误或缺失时抛出。
    """

    def __init__(self, message: str, config_key: str | None = None):
        details = {}
        if config_key:
            details["config_key"] = config_key

        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details=details,
        )


# ============== 错误响应格式 ==============


def create_error_response(
    error_code: str,
    message: str,
    status_code: int = 500,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建统一格式的错误响应。"""
    return ResponseVO.error(
        code=status_code,
        message=message,
        trace_id=get_trace_id(),
    ).model_dump()


# ============== 异常处理中间件 ==============


def register_exception_handlers(app: FastAPI) -> None:
    """注册异常处理器到 FastAPI 应用

    Args:
        app: FastAPI 应用实例
    """

    @app.exception_handler(AIApprovalException)
    async def ai_approval_exception_handler(
        request: Request, exc: AIApprovalException
    ) -> JSONResponse:
        """处理 AIApprovalException 及其子类异常

        返回统一格式的错误响应。
        """
        logger.warning(
            f"业务异常 - 路径：{request.url.path}, "
            f"错误码：{exc.error_code}, 消息：{exc.message}"
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_error_response(),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """处理 HTTPException

        将 FastAPI 的 HTTPException 转换为统一格式。
        """
        logger.warning(
            f"HTTP 异常 - 路径：{request.url.path}, "
            f"状态码：{exc.status_code}, 详情：{exc.detail}"
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(
                error_code="HTTP_ERROR",
                message=str(exc.detail),
                status_code=exc.status_code,
            ),
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """处理 Pydantic 验证异常

        将验证错误转换为统一的业务异常格式。
        """
        logger.warning(f"验证异常 - 路径：{request.url.path}, 错误：{exc.errors()}")

        errors = exc.errors()
        field = errors[0]["loc"][-1] if errors else None
        message = errors[0]["msg"] if errors else "验证失败"

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=create_error_response(
                error_code="VALIDATION_ERROR",
                message=message,
                status_code=status.HTTP_400_BAD_REQUEST,
                details={"field": field} if field else {},
            ),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """处理未预期的全局异常

        作为最后一道防线，捕获所有未处理的异常。
        """
        logger.error(
            f"未预期异常 - 路径：{request.url.path}, "
            f"类型：{type(exc).__name__}, 消息：{exc!s}",
            exc_info=True,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=create_error_response(
                error_code="INTERNAL_SERVER_ERROR",
                message="服务器内部错误",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details={"type": type(exc).__name__} if settings.debug else {},
            ),
        )


# 延迟导入 settings，避免循环依赖
def _get_debug_mode(self=None) -> bool:
    """获取调试模式状态"""
    try:
        from app.config.settings import settings

        return settings.debug
    except Exception:
        return False


settings = type("settings", (), {"debug": property(_get_debug_mode)})()
