"""
FlowMind 智能流程设计服务 - 日志装饰器

使用 structlog 实现自动追踪。
"""

import inspect
import time
import typing
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

        # FastAPI 用 `wrapper.__globals__` 解析参数注解，而 @wraps 会让
        # inspect.signature 取回**原函数**的注解。被装饰的模块若写了
        # `from __future__ import annotations`，注解就是字符串，在装饰器所在模块的
        # 命名空间里解析不出来 —— FastAPI 会把 Request / BackgroundTasks / 请求 DTO
        # 当成必填 query 参数，接口从此只返回 422，而且单测直接调 __wrapped__ 时
        # 完全看不出来。这里按原函数自己的命名空间把注解解析好再交给 FastAPI。
        try:
            hints = typing.get_type_hints(func)
            original = inspect.signature(func)
            wrapper.__signature__ = original.replace(
                parameters=[
                    param.replace(annotation=hints.get(name, param.annotation))
                    for name, param in original.parameters.items()
                ]
            )
        except Exception:  # noqa: BLE001 - 解析不了就维持原样，交给 FastAPI 自己报错
            pass

        return wrapper

    return decorator


__all__ = ["log_api_endpoint"]
