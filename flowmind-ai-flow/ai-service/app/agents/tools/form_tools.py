"""
FlowMind 智能流程设计服务 - 表单工具

本模块提供表单设计相关的工具函数，包括表单查询和保存。
"""

import json
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


def get_form(
    form_name: str,
    auth_token: str | None = None,
) -> dict[str, Any] | None:
    """根据表单名称查询表单是否已存在

    Args:
        form_name: 表单名称
        auth_token: 用户认证令牌

    Returns:
        表单信息（已存在时），不存在返回 None
    """
    try:
        service = FormService(auth_token=auth_token)
        result = service.get_form_by_name(form_name)
        if result:
            logger.info(f"工具调用：查询到表单 {form_name}")
        else:
            logger.info(f"工具调用：表单 {form_name} 不存在")
        return result
    except Exception as e:
        logger.error(f"工具调用失败（get_form）：{e}", exc_info=True)
        return None


def save_form(
    form_name: str,
    widget_list: list[dict[str, Any]],
    form_config: dict[str, Any] | None = None,
    auth_token: str | None = None,
) -> dict[str, Any] | None:
    """保存表单设计

    将生成的表单结构保存到后端系统。
    widget_list 和 form_config 将被合并为 content JSON 字符串。

    Args:
        form_name: 表单名称
        widget_list: 表单组件列表
        form_config: 表单配置（可选）
        auth_token: 用户认证令牌

    Returns:
        保存成功返回表单信息，失败返回 None
    """
    try:
        service = FormService(auth_token=auth_token)

        # 将 widget_list 和 form_config 合并为 content JSON 字符串
        content = {
            "widgetList": widget_list,
            "formConfig": form_config or {},
        }
        content_str = json.dumps(content, ensure_ascii=False)

        result = service.create_form(
            form_name=form_name,
            content=content_str,
        )
        if result:
            logger.info(f"工具调用：表单保存成功 {form_name}")
        else:
            logger.warning(f"工具调用：表单保存失败 {form_name}")
        return result
    except Exception as e:
        logger.error(f"工具调用失败（save_form）：{e}", exc_info=True)
        return None


def update_form(
    form_id: int | str,
    form_name: str,
    widget_list: list[dict[str, Any]],
    form_config: dict[str, Any] | None = None,
    auth_token: str | None = None,
) -> dict[str, Any] | None:
    """更新表单设计

    widget_list 和 form_config 将被合并为 content JSON 字符串。

    Args:
        form_id: 表单ID
        form_name: 表单名称
        widget_list: 表单组件列表
        form_config: 表单配置（可选）
        auth_token: 用户认证令牌

    Returns:
        更新成功返回表单信息，失败返回 None
    """
    try:
        service = FormService(auth_token=auth_token)

        # 将 widget_list 和 form_config 合并为 content JSON 字符串
        content = {
            "widgetList": widget_list,
            "formConfig": form_config or {},
        }
        content_str = json.dumps(content, ensure_ascii=False)

        result = service.update_form(
            form_id=form_id,
            form_name=form_name,
            content=content_str,
        )
        if result:
            logger.info(f"工具调用：表单更新成功 {form_name}")
        else:
            logger.warning(f"工具调用：表单更新失败 {form_name}")
        return result
    except Exception as e:
        logger.error(f"工具调用失败（update_form）：{e}", exc_info=True)
        return None


def _get_default_form_config() -> dict[str, Any]:
    """获取默认表单配置"""
    return {
        "modelName": "formData",
        "refName": "ruleForm",
        "labelWidth": 80,
        "labelPosition": "right",
    }


# 工具参数 Schema 定义
SAVE_FORM_SCHEMA = {
    "type": "object",
    "properties": {
        "form_name": {
            "type": "string",
            "description": "表单名称（如'请假申请表'、'报销申请表'等）",
        },
        "node_role": {
            "type": "string",
            "description": "节点角色标识（如 applicant、approver、cc）",
        },
        "widget_list": {
            "type": "array",
            "description": "表单组件列表",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "label": {"type": "string"},
                    "name": {"type": "string"},
                    "options": {"type": "object"},
                },
            },
        },
        "form_config": {
            "type": "object",
            "description": "表单配置（可选）",
            "properties": {
                "modelName": {"type": "string"},
                "refName": {"type": "string"},
                "labelWidth": {"type": "number"},
                "labelPosition": {"type": "string"},
            },
        },
    },
    "required": ["form_name", "node_role", "widget_list"],
}
