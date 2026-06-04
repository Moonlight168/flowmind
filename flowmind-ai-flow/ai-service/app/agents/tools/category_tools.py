"""
FlowMind 智能流程设计服务 - 分类工具

本模块提供流程分类相关的工具函数，包括分类查询。
"""

from typing import Any

from app.adapters.backend.category import CategoryService
from app.infra.logger import logger


def _get_category_service(auth_token: str | None = None) -> CategoryService:
    """获取分类服务实例"""
    return CategoryService(auth_token=auth_token)


def search_categories(
    category_name: str | None = None,
    category_code: str | None = None,
    auth_token: str | None = None,
) -> list[dict[str, Any]]:
    """搜索所有匹配的分类

    Args:
        category_name: 分类名称（可选，支持模糊搜索）
        category_code: 分类编码（可选，精确匹配）
        auth_token: 用户认证令牌

    Returns:
        所有匹配的分类列表
    """
    try:
        category_service = _get_category_service(auth_token)
        result = category_service.search_categories(
            category_name=category_name if category_name else None,
            category_code=category_code if category_code else None,
        )
        logger.info(f"工具调用：搜索到 {len(result)} 个分类，name={category_name}, code={category_code}")
        return result
    except Exception as e:
        logger.error(f"工具调用失败（search_categories）：{e}", exc_info=True)
        return []


# 工具参数 Schema 定义
SEARCH_CATEGORIES_SCHEMA = {
    "type": "object",
    "properties": {
        "category_name": {
            "type": "string",
            "description": "要搜索的分类名称（可选，与 code 二选一）",
        },
        "category_code": {
            "type": "string",
            "description": "要搜索的分类编码（可选，与 name 二选一）",
        },
    },
}
