"""
FlowMind 智能流程设计服务 - 表单工具

本模块提供表单设计相关的工具函数，包括表单查询。
"""

from typing import Any

from app.adapters.backend.form import FormService
from app.infra.logger import logger


def search_forms(
    form_name: str,
    auth_token: str | None = None,
) -> list[dict[str, Any]]:
    """搜索所有匹配的表单

    Args:
        form_name: 表单名称
        auth_token: 用户认证令牌

    Returns:
        所有匹配的表单列表
    """
    try:
        service = FormService(auth_token=auth_token)
        result = service.search_forms(form_name)
        logger.info(f"工具调用：搜索到 {len(result)} 个表单 {form_name}")
        return result
    except Exception as e:
        logger.error(f"工具调用失败（search_forms）：{e}", exc_info=True)
        return []
