"""
FlowMind 智能流程设计服务 - 模型错误类型定义

本模块定义模型调用过程中可能出现的错误类型。
"""

from app.core.exceptions import AIApprovalException


# 错误码常量（与 AIApprovalException.error_code 一致）
class ModelErrorCode:
    NETWORK_ERROR = "MODEL_NETWORK_ERROR"
    AUTH_ERROR = "MODEL_AUTH_ERROR"
    RATE_LIMIT_ERROR = "MODEL_RATE_LIMIT_ERROR"
    SERVICE_ERROR = "MODEL_SERVICE_ERROR"
    PARSE_ERROR = "MODEL_PARSE_ERROR"
    TIMEOUT_ERROR = "MODEL_TIMEOUT_ERROR"
    UNKNOWN_ERROR = "MODEL_UNKNOWN_ERROR"


# 可恢复错误码集合（可以尝试切换到其他模型）
RECOVERABLE_ERROR_CODES = {
    ModelErrorCode.NETWORK_ERROR,
    ModelErrorCode.RATE_LIMIT_ERROR,
    ModelErrorCode.SERVICE_ERROR,
    ModelErrorCode.TIMEOUT_ERROR,
}


class ModelError(AIApprovalException):
    """模型调用错误

    当 LLM 模型调用失败时抛出，支持错误分类和可恢复性判断。
    """

    def __init__(
        self,
        message: str,
        error_code: str = ModelErrorCode.UNKNOWN_ERROR,
        model_name: str | None = None,
        status_code: int = 500,
        details: dict | None = None,
    ):
        self.model_name = model_name
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details or {},
        )

    def __str__(self) -> str:
        prefix = f"[{self.model_name}] " if self.model_name else ""
        return f"{prefix}{self.message}"

    def is_recoverable(self) -> bool:
        """错误是否可恢复（可以尝试切换到其他模型）"""
        return self.error_code in RECOVERABLE_ERROR_CODES


def classify_error(error: Exception, status_code: int | None = None) -> str:
    """分类错误类型并返回错误码

    Args:
        error: 原始异常
        status_code: HTTP 状态码（如果有）

    Returns:
        错误码字符串
    """
    error_str = str(error).lower()

    # 404 Not Found - 通常表示 API 路径错误或资源不存在
    if status_code == 404:
        return ModelErrorCode.SERVICE_ERROR

    if "timeout" in error_str or "timed out" in error_str:
        return ModelErrorCode.TIMEOUT_ERROR

    if (
        "connection" in error_str
        or "network" in error_str
        or "unreachable" in error_str
    ):
        return ModelErrorCode.NETWORK_ERROR

    if (
        "unauthorized" in error_str
        or "invalid api key" in error_str
        or "authentication" in error_str
    ):
        return ModelErrorCode.AUTH_ERROR

    if (
        "rate limit" in error_str
        or "too many requests" in error_str
        or "429" in error_str
    ):
        return ModelErrorCode.RATE_LIMIT_ERROR

    if (
        "service" in error_str
        or "503" in error_str
        or "500" in error_str
        or "unavailable" in error_str
    ):
        return ModelErrorCode.SERVICE_ERROR

    if "json" in error_str or "parse" in error_str or "decode" in error_str:
        return ModelErrorCode.PARSE_ERROR

    return ModelErrorCode.UNKNOWN_ERROR
