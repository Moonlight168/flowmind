"""
FlowMind 智能流程设计服务 - Agent 基类

本模块定义 Agent 基类和数据结构，提供统一的 Agent 执行框架和工具管理能力。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from app.agents.tools.registry import Tool, tool_registry
from app.infra.logger import logger

if TYPE_CHECKING:
    from app.graph.state import AppState


@dataclass
class ToolResult:
    """工具执行结果

    Attributes:
        success: 执行是否成功
        data: 返回数据（成功时）
        error: 错误信息（失败时）
    """

    success: bool
    data: Any = None
    error: str | None = None


class BaseAgent(ABC):
    """Agent 抽象基类

    提供统一的 Agent 执行框架：
    - 工具管理和获取
    - 异常处理
    - 状态流转

    子类需要实现 _process 方法完成核心逻辑。
    """

    def __init__(self, tools: list[str] | None = None):
        """初始化 Agent

        Args:
            tools: Agent 可用的工具名称列表
        """
        self._tool_names = tools or []

    @property
    def tools(self) -> list[Tool]:
        """获取 Agent 可用的工具列表"""
        return [tool_registry.get(name) for name in self._tool_names if tool_registry.has(name)]

    def execute(self, state: "AppState") -> "AppState":
        """执行入口 - 调用 _process 并处理异常

        Args:
            state: 当前流程设计状态

        Returns:
            更新后的状态
        """
        try:
            return self._process(state)
        except Exception as e:
            logger.error(f"Agent 执行失败：{e}", exc_info=True)
            return state

    @abstractmethod
    def _process(self, state: "AppState") -> "AppState":
        """核心逻辑 - 子类实现

        Args:
            state: 当前流程设计状态

        Returns:
            更新后的状态
        """
        pass
