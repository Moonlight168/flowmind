"""
FlowMind 智能流程设计服务 - 分类工具

本模块提供流程分类相关的工具函数，包括分类查询和创建。
"""

from typing import Any

from app.adapters.backend.category import CategoryService
from app.infra.logger import logger


def _get_category_service(auth_token: str | None = None) -> CategoryService:
    """获取分类服务实例"""
    return CategoryService(auth_token=auth_token)


def search_categories(category_name: str, auth_token: str | None = None) -> list[dict[str, Any]]:
    """搜索所有匹配的分类

    Args:
        category_name: 分类名称
        auth_token: 用户认证令牌

    Returns:
        所有匹配的分类列表
    """
    try:
        category_service = _get_category_service(auth_token)
        result = category_service.search_categories(category_name)
        logger.info(f"工具调用：搜索到 {len(result)} 个分类 {category_name}")
        return result
    except Exception as e:
        logger.error(f"工具调用失败（search_categories）：{e}", exc_info=True)
        return []


def get_category(category_name: str, auth_token: str | None = None) -> dict[str, Any] | None:
    """根据分类名称查询分类是否已存在

    Args:
        category_name: 分类名称
        auth_token: 用户认证令牌

    Returns:
        分类信息（已存在时），不存在返回 None
    """
    try:
        category_service = _get_category_service(auth_token)
        result = category_service.get_category_by_name(category_name)
        if result:
            logger.info(f"工具调用：查询到分类 {category_name}")
        else:
            logger.info(f"工具调用：分类 {category_name} 不存在")
        return result
    except Exception as e:
        logger.error(f"工具调用失败（get_category）：{e}", exc_info=True)
        return None


def save_category(
    category_name: str,
    category_code: str,
    remark: str = "",
    auth_token: str | None = None,
) -> dict[str, Any] | None:
    """创建流程分类

    Args:
        category_name: 分类名称
        category_code: 分类编码
        remark: 备注说明
        auth_token: 用户认证令牌

    Returns:
        创建成功返回分类信息，失败返回 None
    """
    try:
        category_service = _get_category_service(auth_token)
        result = category_service.create_category(
            category_name=category_name,
            category_code=category_code,
            remark=remark,
        )
        if result:
            logger.info(f"工具调用：分类创建成功 {category_name}")
        else:
            logger.warning(f"工具调用：分类创建失败 {category_name}")
        return result
    except Exception as e:
        logger.error(f"工具调用失败（save_category）：{e}", exc_info=True)
        return None


def update_category(
    category_id: int | str,
    category_name: str,
    category_code: str,
    remark: str = "",
    auth_token: str | None = None,
) -> dict[str, Any] | None:
    """更新流程分类

    Args:
        category_id: 分类ID
        category_name: 分类名称
        category_code: 分类编码
        remark: 备注说明
        auth_token: 用户认证令牌

    Returns:
        更新成功返回分类信息，失败返回 None
    """
    try:
        category_service = _get_category_service(auth_token)
        result = category_service.update_category(
            category_id=category_id,
            category_name=category_name,
            category_code=category_code,
            remark=remark,
        )
        if result:
            logger.info(f"工具调用：分类更新成功 {category_name}")
        else:
            logger.warning(f"工具调用：分类更新失败 {category_name}")
        return result
    except Exception as e:
        logger.error(f"工具调用失败（update_category）：{e}", exc_info=True)
        return None


# 工具参数 Schema 定义
SEARCH_CATEGORIES_SCHEMA = {
    "type": "object",
    "properties": {
        "category_name": {
            "type": "string",
            "description": "要搜索的分类名称",
        }
    },
    "required": ["category_name"],
}

GET_CATEGORY_SCHEMA = {
    "type": "object",
    "properties": {
        "category_name": {
            "type": "string",
            "description": "要查询的分类名称",
        }
    },
    "required": ["category_name"],
}

SAVE_CATEGORY_SCHEMA = {
    "type": "object",
    "properties": {
        "category_name": {
            "type": "string",
            "description": "分类名称",
        },
        "category_code": {
            "type": "string",
            "description": "分类编码",
        },
        "remark": {
            "type": "string",
            "description": "分类备注说明",
        },
    },
    "required": ["category_name", "category_code"],
}

UPDATE_CATEGORY_SCHEMA = {
    "type": "object",
    "properties": {
        "category_id": {
            "type": "integer",
            "description": "分类ID",
        },
        "category_name": {
            "type": "string",
            "description": "分类名称",
        },
        "category_code": {
            "type": "string",
            "description": "分类编码",
        },
        "remark": {
            "type": "string",
            "description": "分类备注说明",
        },
    },
    "required": ["category_id", "category_name", "category_code"],
}
