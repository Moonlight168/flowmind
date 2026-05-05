"""
FlowMind 智能流程设计服务 - JSON Schema 注册中心

本模块提供 JSON Schema 的注册和获取功能。
"""

from typing import Any


class SchemaRegistry:
    """JSON Schema 注册中心

    单例模式，全局管理所有 JSON Schema 定义。
    """

    _schemas: dict[str, dict[str, Any]] = {}

    @classmethod
    def register(cls, name: str, schema: dict[str, Any]) -> None:
        """注册 JSON Schema

        Args:
            name: Schema 名称（用于引用）
            schema: JSON Schema 定义
        """
        cls._schemas[name] = schema

    @classmethod
    def get(cls, name: str) -> dict[str, Any] | None:
        """获取已注册的 Schema

        Args:
            name: Schema 名称

        Returns:
            JSON Schema 定义，如果不存在则返回 None
        """
        return cls._schemas.get(name)

    @classmethod
    def get_all(cls) -> dict[str, dict[str, Any]]:
        """获取所有已注册的 Schema

        Returns:
            所有 Schema 的字典
        """
        return cls._schemas.copy()

    @classmethod
    def unregister(cls, name: str) -> bool:
        """注销 Schema

        Args:
            name: Schema 名称

        Returns:
            是否成功注销
        """
        if name in cls._schemas:
            del cls._schemas[name]
            return True
        return False
