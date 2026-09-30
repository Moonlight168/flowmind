"""
FlowMind 智能流程设计服务 - API 依赖注入

本模块提供统一的认证依赖：生产环境信任网关注入的用户身份，
配置 JWT_SECRET 时可用于直连测试并执行严格验签。
所有需要认证的 API 路由通过 Depends(require_auth) 注入用户信息。
"""

from urllib.parse import unquote_plus

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config.settings import settings
from app.core.auth import TokenParseError, TokenUser, parse_token_strict
from app.core.auth_context import set_auth_token, set_current_user
from app.infra.logger import logger

security = HTTPBearer(auto_error=False)


def _gateway_user(request: Request) -> TokenUser | None:
    """读取已由 RuoYi Gateway 校验并注入的用户身份。"""
    try:
        user_id = int(unquote_plus(request.headers.get("user_id", "")))
    except ValueError:
        return None
    username = unquote_plus(request.headers.get("username", ""))
    user_key = unquote_plus(request.headers.get("user_key", ""))
    if not user_id or not username or not user_key:
        return None
    return TokenUser(user_id=user_id, username=username, user_key=user_key)


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> TokenUser:
    """解析当前用户身份。

    在需要认证的路由上使用：
        @router.post("/xxx")
        async def endpoint(user: TokenUser = Depends(require_auth)):
            ...

    该依赖会同时将 token 和解析后的用户信息存入请求上下文，
    后续代码可通过 auth_context.get_auth_token() 和 auth_context.get_current_user() 获取。

    JWT_SECRET 为空时不重复验签，信任 RuoYi Gateway 已校验并注入的
    user_id、username 和 user_key；配置密钥时执行严格 JWT 验签。
    """
    if not settings.jwt_secret:
        token_user = _gateway_user(request)
        if token_user is None:
            logger.warning("Missing gateway identity headers")
            raise HTTPException(
                status_code=403, detail="Missing gateway identity headers"
            )
        set_auth_token(credentials.credentials if credentials else None)
        set_current_user(token_user)
        return token_user

    if credentials is None:
        logger.warning(
            f"[{request.state.trace_id if hasattr(request.state, 'trace_id') else 'unknown'}] Missing authorization header"
        )
        raise HTTPException(status_code=403, detail="Missing authorization header")

    if credentials.scheme.lower() != "bearer":
        logger.warning(
            f"[{request.state.trace_id if hasattr(request.state, 'trace_id') else 'unknown'}] Invalid authentication scheme: {credentials.scheme}"
        )
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
    except TokenParseError as e:
        logger.warning(
            f"[{request.state.trace_id if hasattr(request.state, 'trace_id') else 'unknown'}] Token validation failed: {e}"
        )
        raise HTTPException(status_code=403, detail="Invalid or expired token")
