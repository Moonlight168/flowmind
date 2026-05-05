"""
FlowMind 智能流程设计服务 - API 依赖注入

本模块提供统一的认证依赖，实现 Token 验证过滤链。
所有需要认证的 API 路由通过 Depends(require_auth) 注入用户信息。
"""

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth_context import set_auth_token, set_current_user
from app.infra.logger import logger
from app.utils.auth import TokenUser, parse_token_strict

security = HTTPBearer(auto_error=False)


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> TokenUser:
    """认证依赖 - 验证用户 Token

    在需要认证的路由上使用：
        @router.post("/xxx")
        async def endpoint(user: TokenUser = Depends(require_auth)):
            ...

    该依赖会同时将 token 和解析后的用户信息存入请求上下文，
    后续代码可通过 auth_context.get_auth_token() 和 auth_context.get_current_user() 获取。

    Raises:
        HTTPException: Token 无效或缺失时返回 403
    """
    if credentials is None:
        logger.warning(f"[{request.state.trace_id if hasattr(request.state, 'trace_id') else 'unknown'}] Missing authorization header")
        raise HTTPException(status_code=403, detail="Missing authorization header")

    if credentials.scheme.lower() != "bearer":
        logger.warning(f"[{request.state.trace_id if hasattr(request.state, 'trace_id') else 'unknown'}] Invalid authentication scheme: {credentials.scheme}")
        raise HTTPException(status_code=403, detail="Invalid authentication scheme")

    try:
        token_user = parse_token_strict(credentials.credentials)
        if not token_user.user_key:
            raise HTTPException(status_code=403, detail="Invalid or expired token")

        # 存入请求上下文，供后续代码使用
        set_auth_token(credentials.credentials)
        set_current_user(token_user)

        return token_user
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"[{request.state.trace_id if hasattr(request.state, 'trace_id') else 'unknown'}] Token validation failed: {e}")
        raise HTTPException(status_code=403, detail="Invalid or expired token")
