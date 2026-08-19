"""
FlowMind 智能流程设计服务 - 日志装饰器

使用 structlog 实现自动追踪。
"""

import time
from functools import wraps

from structlog.contextvars import bind_contextvars, clear_contextvars

from .logger_config import generate_request_id, generate_trace_id, logger


def log_api_endpoint(skip_paths: list[str] | None = None):
    """API 接口装饰器 - 自动绑定 trace_id、request_id 并记录请求信息"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 提取 request 对象
            request = None
            for arg in args:
                if hasattr(arg, "url") and hasattr(arg, "method"):
                    request = arg
                    break
            if not request:
                for v in kwargs.values():
                    if hasattr(v, "url") and hasattr(v, "method"):
                        request = v
                        break

            path = request.url.path if request else func.__name__

            # 跳过路径检查
            if skip_paths:
                for skip_path in skip_paths:
                    if path.startswith(skip_path):
                        return await func(*args, **kwargs)

            # 生成 ID 并绑定上下文
            trace_id = generate_trace_id()
            request_id = request.headers.get("X-Request-ID") or generate_request_id()
            bind_contextvars(trace_id=trace_id, request_id=request_id)

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                status = getattr(result, "status_code", 200)
                logger.info(
                    "请求完成",
                    path=path,
                    status=status,
                    elapsed_ms=int((time.time() - start_time) * 1000),
                )
                return result
            except Exception as e:
                logger.error(
                    "请求失败",
                    path=path,
                    error=str(e),
                    elapsed_ms=int((time.time() - start_time) * 1000),
                )
                raise
            finally:
                clear_contextvars()

        return wrapper

    return decorator


def log_node_execution(node: str):
    """节点执行装饰器 - 自动绑定 node 名称并记录执行信息"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                logger.info(
                    "节点执行完成",
                    node=node,
                    elapsed_ms=int((time.time() - start_time) * 1000),
                )
                return result
            except Exception as e:
                logger.error(
                    "节点执行失败",
                    node=node,
                    error=str(e),
                    elapsed_ms=int((time.time() - start_time) * 1000),
                )
                raise

        return wrapper

    return decorator


__all__ = ["log_api_endpoint", "log_node_execution"]
