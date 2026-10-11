"""
FlowMind 智能流程设计服务 - API 依赖注入

AI 服务位于 RuoYi Gateway 之后，自身不校验 JWT：网关已完成 token 校验，
并以请求头覆盖式注入 user_id / username / user_key，本模块仅读取这些头。

安全前提：AI 服务端口不可对宿主机发布（见 docker-compose.prod.yml），
仅经网关 /flowmind-ai/** 访问。若端口直接暴露，请求方可伪造身份头冒充任意用户。
"""

from urllib.parse import unquote_plus

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth import TokenUser
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
    """解析当前用户身份（信任网关注入的请求头，不重复验签）。

    在需要认证的路由上使用：
        @router.post("/xxx")
        async def endpoint(user: TokenUser = Depends(require_auth)):
            ...

    同时将原始 token 与解析出的用户信息存入请求上下文，后续代码可通过
    auth_context.get_auth_token() / get_current_user() 获取。
    """
    token_user = _gateway_user(request)
    if token_user is None:
        logger.warning("Missing gateway identity headers")
        raise HTTPException(status_code=403, detail="Missing gateway identity headers")

    set_auth_token(credentials.credentials if credentials else None)
    set_current_user(token_user)
    return token_user
