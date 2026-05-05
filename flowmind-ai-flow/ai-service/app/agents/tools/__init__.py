"""
FlowMind 智能流程设计服务 - 工具模块

本模块提供 Agent 工具的注册与管理能力。
"""

from .category_tools import (
    GET_CATEGORY_SCHEMA,
    SAVE_CATEGORY_SCHEMA,
    SEARCH_CATEGORIES_SCHEMA,
    UPDATE_CATEGORY_SCHEMA,
    get_category,
    save_category,
    search_categories,
    update_category,
)
from .compress_tools import (
    COMPRESS_CONVERSATION_HISTORY_SCHEMA,
    compress_conversation_history,
)
from .flow_tools import (
    FORMAT_FLOW_PREVIEW_SCHEMA,
    GENERATE_BPMN_XML_SCHEMA,
    SAVE_FLOW_MODEL_SCHEMA,
    SEARCH_FLOW_MODELS_SCHEMA,
    format_flow_preview,
    generate_bpmn_xml,
    generate_unique_flow_key,
    save_flow_model,
    search_flow_models,
)
from .form_tools import SAVE_FORM_SCHEMA, save_form
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

    tool_registry.register(
        name="get_category",
        func=get_category,
        permission="read",
        description="根据分类名称查询分类是否已存在",
        parameters_schema=GET_CATEGORY_SCHEMA,
    )

    tool_registry.register(
        name="save_category",
        func=save_category,
        permission="write",
        description="创建流程分类",
        parameters_schema=SAVE_CATEGORY_SCHEMA,
    )

    tool_registry.register(
        name="update_category",
        func=update_category,
        permission="write",
        description="更新流程分类",
        parameters_schema=UPDATE_CATEGORY_SCHEMA,
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
        name="save_flow_model",
        func=save_flow_model,
        permission="write",
        description="保存流程模型到后端",
        parameters_schema=SAVE_FLOW_MODEL_SCHEMA,
    )

    tool_registry.register(
        name="generate_bpmn_xml",
        func=generate_bpmn_xml,
        permission="read",
        description="将流程结构生成为 BPMN XML 格式",
        parameters_schema=GENERATE_BPMN_XML_SCHEMA,
    )

    tool_registry.register(
        name="format_flow_preview",
        func=format_flow_preview,
        permission="read",
        description="格式化流程预览文本，用于向用户展示流程步骤",
        parameters_schema=FORMAT_FLOW_PREVIEW_SCHEMA,
    )


def register_form_tools() -> None:
    """注册表单相关工具"""
    tool_registry.register(
        name="save_form",
        func=save_form,
        permission="write",
        description="保存表单设计",
        parameters_schema=SAVE_FORM_SCHEMA,
    )


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
    "SAVE_FLOW_MODEL_SCHEMA",
    "Tool",
    "ToolRegistry",
    "compress_conversation_history",
    "register_all_tools",
    "register_category_tools",
    "register_compress_tools",
    "register_flow_tools",
    "register_form_tools",
    "save_flow_model",
    "tool_registry",
]
