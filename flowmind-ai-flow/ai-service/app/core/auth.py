"""
FlowMind 智能流程设计服务 - 用户身份模型

AI 服务位于 RuoYi Gateway 之后，身份由网关注入的请求头提供（见 app.api.deps），
本模块只定义承载用户信息的 TokenUser 数据结构。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TokenUser:
    """Token 中的用户信息"""

    user_id: int
    """用户ID"""
    username: str
    """用户名"""
    user_key: str
    """用户唯一标识（Token UUID）"""
