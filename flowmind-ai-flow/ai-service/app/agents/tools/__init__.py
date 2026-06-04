"""
FlowMind 智能流程设计服务 - 工具模块

本模块提供 Agent 工具的注册与管理能力。
"""

from .category_tools import (
    SEARCH_CATEGORIES_SCHEMA,
    search_categories,
)
from .compress_tools import (
    COMPRESS_CONVERSATION_HISTORY_SCHEMA,
    compress_conversation_history,
)
from .flow_tools import (
    FORMAT_FLOW_PREVIEW_SCHEMA,
    SEARCH_FLOW_MODELS_SCHEMA,
    format_flow_preview,
    generate_unique_flow_key,
    search_flow_models,
)
from .registry import Tool, ToolRegistry, tool_registry


def register_category_tools() -> None:
    """注册分类相关工具"""
    tool_registry.register(
        name="search_categories",
        func=search_categories,
        permission="read",
        description="搜索所有匹配的分类",
        parameters_schema=SEARCH_CATEGORIES_SCHEMA,
    )


def register_flow_tools() -> None:
    """注册流程相关工具"""
    tool_registry.register(
        name="search_flow_models",
        func=search_flow_models,
        permission="read",
        description="搜索匹配的流程模型列表，用于检查流程是否存在",
        parameters_schema=SEARCH_FLOW_MODELS_SCHEMA,
    )

    tool_registry.register(
        name="format_flow_preview",
        func=format_flow_preview,
        permission="read",
        description="格式化流程预览文本，用于向用户展示流程步骤",
        parameters_schema=FORMAT_FLOW_PREVIEW_SCHEMA,
    )


def register_form_tools() -> None:
    """注册表单相关工具（预留）"""
    pass


def register_compress_tools() -> None:
    """注册压缩工具"""
    tool_registry.register(
        name="compress_conversation_history",
        func=compress_conversation_history,
        permission="read",
        description=COMPRESS_CONVERSATION_HISTORY_SCHEMA["description"],
        parameters_schema=COMPRESS_CONVERSATION_HISTORY_SCHEMA,
    )


def register_all_tools() -> None:
    """注册所有内置工具到工具注册表"""
    register_category_tools()
    register_flow_tools()
    register_form_tools()
    register_compress_tools()


# 模块导入时自动注册
register_all_tools()


__all__ = [
    "COMPRESS_CONVERSATION_HISTORY_SCHEMA",
    "Tool",
    "ToolRegistry",
    "compress_conversation_history",
    "format_flow_preview",
    "generate_unique_flow_key",
    "register_all_tools",
    "register_category_tools",
    "register_compress_tools",
    "register_flow_tools",
    "register_form_tools",
    "search_categories",
    "search_flow_models",
    "tool_registry",
]
