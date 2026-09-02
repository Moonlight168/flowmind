"""
FlowMind 智能流程设计服务 - 请求级认证上下文

本模块提供请求级别的用户认证信息存储，基于 ContextVar 实现线程安全的上下文隔离。
"""

from __future__ import annotations

from contextvars import ContextVar

from app.core.auth import TokenUser

_auth_token: ContextVar[str | None] = ContextVar("auth_token", default=None)
_current_user: ContextVar[TokenUser | None] = ContextVar("current_user", default=None)


def set_auth_token(token: str | None) -> None:
    """设置当前上下文的认证 token。"""
    _auth_token.set(token)


def get_auth_token() -> str | None:
    """获取当前上下文的认证 token。"""
    return _auth_token.get()


def set_current_user(user: TokenUser | None) -> None:
    """设置当前上下文的用户信息。"""
    _current_user.set(user)


def get_current_user() -> TokenUser | None:
    """获取当前上下文的用户信息。"""
    return _current_user.get()
