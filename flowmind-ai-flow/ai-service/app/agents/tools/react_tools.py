"""
FlowMind 智能审批服务 - ReAct 工具工厂

本模块将现有工具函数包装为 LangChain @tool 格式，
供 LangGraph create_react_agent 使用。
auth_token 通过闭包注入，不暴露给 LLM。
"""

from typing import Any

from langchain_core.tools import tool

from app.infra.logger import logger


def create_tools(design_type: str, auth_token: str) -> list:
    """根据设计类型创建工具列表

    Args:
        design_type: 设计类型 (category/flow/form)
        auth_token: 用户认证令牌，通过闭包注入

    Returns:
        LangChain @tool 装饰的工具列表
    """
    tools = []

    if design_type in ("category_design", "flow_design"):
        tools.append(_make_search_categories_tool(auth_token))

    if design_type == "flow_design":
        tools.extend([
            _make_search_flow_models_tool(auth_token),
            _make_search_roles_tool(auth_token),
            _make_search_forms_tool(auth_token),
        ])

    if design_type == "form_design":
        tools.append(_make_search_forms_tool(auth_token))

    tool_names = [t.name for t in tools]
    return tools


def _make_search_categories_tool(auth_token: str):
    """search_categories 工具"""
    from app.agents.tools.category_tools import search_categories as _search

    @tool
    def search_categories(
        category_name: str | None = None,
        category_code: str | None = None,
    ) -> list[dict[str, Any]]:
        """搜索流程分类。当需要确认分类是否存在、查找分类编码、或验证 code 是否重复时使用。

        Args:
            category_name: 要搜索的分类名称（可选，支持模糊搜索）
            category_code: 要搜索的分类编码（可选，精确匹配）
        """
        logger.info("[TOOL_CALL] search_categories", category_name=category_name, category_code=category_code)
        result = _search(category_name=category_name, category_code=category_code, auth_token=auth_token)
        logger.info(f"[TOOL_CALL] search_categories 完成，返回 {len(result)} 条记录")
        return result

    return search_categories


def _make_search_flow_models_tool(auth_token: str):
    """search_flow_models 工具"""
    from app.agents.tools.flow_tools import search_flow_models as _search

    @tool
    def search_flow_models(name: str = "", key: str = "") -> list[dict[str, Any]]:
        """搜索流程模型。当需要确认流程是否已存在时使用。

        Args:
            name: 流程名称（支持模糊匹配）
            key: 流程编码（精确匹配）
        """
        logger.info("[TOOL_CALL] search_flow_models", name=name, key=key)
        result = _search(name=name, key=key, auth_token=auth_token)
        logger.info(f"[TOOL_CALL] search_flow_models 完成，返回 {len(result)} 条记录")
        return result

    return search_flow_models


def _make_search_roles_tool(auth_token: str):
    """search_roles 工具"""
    from app.adapters.backend.role import RoleService

    @tool
    def search_roles() -> list[dict[str, str]]:
        """获取所有可用角色。设计流程节点审批人时使用。

        Returns:
            角色列表，每项包含 name（显示名）和 key（标识，格式为 ROLE{roleId}）
        """
        logger.info("[TOOL_CALL] search_roles")
        service = RoleService(auth_token=auth_token)
        roles = service.search_roles()
        result = [
            {"name": r.get("roleName", ""), "key": f"ROLE{r.get('roleId', '')}"}
            for r in roles
            if r.get("roleId")
        ]
        logger.info(f"[TOOL_CALL] search_roles 完成，返回 {len(result)} 个角色")
        return result

    return search_roles


def _make_search_forms_tool(auth_token: str):
    """search_forms 工具"""
    from app.agents.tools.form_tools import search_forms as _search

    @tool
    def search_forms(form_name: str = "") -> list[dict[str, Any]]:
        """搜索可用表单。当流程节点需要绑定表单、或设计新表单参考时使用。

        Args:
            form_name: 表单名称（空字符串返回全部）
        """
        logger.info("[TOOL_CALL] search_forms", form_name=form_name)
        result = _search(form_name, auth_token=auth_token)
        logger.info(f"[TOOL_CALL] search_forms 完成，返回 {len(result)} 个表单")
        return result

    return search_forms

