"""
FlowMind 智能流程设计服务 - Tool 注册表

本模块实现工具注册与管理，提供统一的工具存储、查询和权限过滤能力。
"""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Tool:
    """工具定义数据类。"""

    name: str
    func: Callable
    permission: str  # "read" 或 "write"
    description: str
    parameters_schema: dict | None = None  # JSON Schema 格式


class ToolRegistry:
    """工具注册表，管理工具的注册、查询和过滤。"""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(
        self,
        name: str,
        func: Callable,
        permission: str,
        description: str,
        parameters_schema: dict | None = None,
    ) -> None:
        """注册工具到注册表。

        Args:
            name: 工具名称，唯一标识
            func: 工具执行函数
            permission: 权限类型，"read" 或 "write"
            description: 工具功能描述
            parameters_schema: 参数的 JSON Schema，可选
        """
        self._tools[name] = Tool(
            name=name,
            func=func,
            permission=permission,
            description=description,
            parameters_schema=parameters_schema,
        )

    def get(self, name: str) -> Tool:
        """获取指定名称的工具。

        Args:
            name: 工具名称

        Returns:
            Tool 实例

        Raises:
            KeyError: 工具不存在时抛出
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        return self._tools[name]

    def list_tools(self, permission: str | None = None) -> list[Tool]:
        """列出所有工具，可按权限过滤。

        Args:
            permission: 权限类型过滤，"read" 或 "write"，为 None 时返回全部

        Returns:
            工具列表
        """
        if permission is None:
            return list(self._tools.values())
        return [tool for tool in self._tools.values() if tool.permission == permission]

    def has(self, name: str) -> bool:
        """检查工具是否存在于注册表。

        Args:
            name: 工具名称

        Returns:
            存在返回 True，否则返回 False
        """
        return name in self._tools


# 全局单例实例
tool_registry = ToolRegistry()
