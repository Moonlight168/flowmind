"""
FlowMind 智能流程设计服务 - 流程工具

本模块提供流程设计相关的工具函数，包括流程模型查询和 BPMN XML 生成。
"""

from typing import Any

from app.adapters.backend.flow import FlowService
from app.infra.logger import logger


def search_flow_models(
    name: str | None = None,
    key: str | None = None,
    auth_token: str | None = None,
) -> list[dict[str, Any]]:
    """搜索匹配的流程模型列表

    Args:
        name: 流程名称（支持模糊匹配）
        key: 流程编码（精确匹配）
        auth_token: 用户认证令牌

    Returns:
        匹配的流程模型列表，每个流程包含：
        - modelId: 流程 ID
        - modelName: 流程名称
        - modelKey: 流程编码
        - category: 所属分类
        - description: 流程描述
    """
    try:
        service = FlowService(auth_token=auth_token)
        return service.search_flow_models(model_name=name, model_key=key)
    except Exception as e:
        logger.error(f"工具调用失败（search_flow_models）：{e}", exc_info=True)
        return []


# 工具参数 Schema 定义
SEARCH_FLOW_MODELS_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "流程名称，支持模糊匹配",
        },
        "key": {
            "type": "string",
            "description": "流程编码，精确匹配",
        },
    },
}


def format_flow_preview(nodes: list[dict]) -> str:
    """格式化流程预览，生成可读性高的流程描述

    Args:
        nodes: 节点列表

    Returns:
        格式化的流程预览文本
    """
    if not nodes:
        return "（无节点）"

    flow_arrow = " → ".join([node.get("name", f"节点{i}") for i, node in enumerate(nodes, 1)])
    return f"**流程步骤：** {flow_arrow}"


FORMAT_FLOW_PREVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "nodes": {
            "type": "array",
            "description": "节点列表",
        },
    },
    "required": ["nodes"],
}


def generate_unique_flow_key(base_key: str, existing_flows: list[dict]) -> str:
    """生成唯一的流程编码

    Args:
        base_key: 基础编码
        existing_flows: 已有的流程列表

    Returns:
        唯一的编码
    """
    existing_keys = {flow.get("modelKey", "") for flow in existing_flows}

    if base_key not in existing_keys:
        return base_key

    suffix = 1
    while f"{base_key}_{suffix}" in existing_keys:
        suffix += 1

    return f"{base_key}_{suffix}"
