"""
FlowMind 智能流程设计服务 - Token 解析工具

本模块提供从 Java RuoYi 后端 JWT Token 中解析用户信息的工具。
Token 格式遵循 RuoYi 的 SecurityConstants 标准：
- 算法: HS512（密钥需 ≥64 字节）
- Claims: user_key(用户标识), user_id(用户ID), username(用户名)
"""

from dataclasses import dataclass

import jwt

from app.config.settings import settings


@dataclass(frozen=True)
class TokenUser:
    """Token 中的用户信息"""

    user_id: int
    """用户ID"""
    username: str
    """用户名"""
    user_key: str
    """用户唯一标识（Token UUID）"""


class TokenParseError(Exception):
    """Token 解析失败"""


def _get_jwt_secret() -> str:
    return settings.jwt_secret


def parse_token(token: str | None) -> TokenUser | None:
    """解析 JWT Token，提取用户信息。

    Args:
        token: JWT Token 字符串（不含 Bearer 前缀）

    Returns:
        TokenUser 对象，解析失败返回 None
    """
    if not token:
        return None

    # TODO: 生产环境建议开启签名验证，确保 Token 的真实性和完整性
    try:
        claims = jwt.decode(
            token,
            _get_jwt_secret(),
            algorithms=["HS512"],
            options={"verify_signature": False},
        )
        return TokenUser(
            user_id=int(claims.get("user_id") or 0),
            username=claims.get("username") or "",
            user_key=claims.get("user_key") or "",
        )
    except jwt.exceptions.PyJWTError:
        return None
    except (ValueError, TypeError):
        return None


def parse_token_strict(token: str | None) -> TokenUser:
    """解析 JWT Token，提取用户信息。解析失败则抛出异常。

    Args:
        token: JWT Token 字符串（不含 Bearer 前缀）

    Returns:
        TokenUser 对象

    Raises:
        TokenParseError: Token 无效或解析失败
    """
    if not token:
        raise TokenParseError("Token is empty")

    try:
        claims = jwt.decode(
            token,
            _get_jwt_secret(),
            algorithms=["HS512"],
            options={"verify_signature": False},
        )
        user_id = int(claims.get("user_id") or 0)
        username = claims.get("username") or ""
        user_key = claims.get("user_key") or ""

        if not user_id and not username:
            raise TokenParseError("Token claims missing user_id and username")

        return TokenUser(
            user_id=user_id,
            username=username,
            user_key=user_key,
        )
    except jwt.exceptions.PyJWTError as e:
        raise TokenParseError(f"Invalid token: {e}")
    except ValueError as e:
        raise TokenParseError(f"Invalid user_id in token: {e}")
