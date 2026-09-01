"""
FlowMind 智能流程设计服务 - 检索工具

供 ReAct agent 按需检索真实数据（分类/角色/表单/流程模型），
替代之前的 prefetch 全量拼 prompt。工具内部从 contextvar 取认证 token。
"""

from langchain_core.tools import tool

from app.adapters.backend.category import CategoryService
from app.adapters.backend.flow import FlowService
from app.adapters.backend.form import FormService
from app.adapters.backend.role import RoleService
from app.core import request_cache
from app.core.auth_context import get_auth_token
from app.prompts.loader import load_prompt

_LIMIT = 50


@tool(description=load_prompt("tools/search_categories.md"))
def search_categories(name: str = "") -> list[dict]:
    rows = request_cache.get(
        f"backend:categories:{name}",
        lambda: CategoryService(auth_token=get_auth_token()).search_categories(name),
    )
    return [
        {
            "categoryId": r.get("categoryId"),
            "categoryName": r.get("categoryName"),
            "code": r.get("code"),
        }
        for r in rows[:_LIMIT]
    ]


@tool(description=load_prompt("tools/search_forms.md"))
def search_forms(name: str = "") -> list[dict]:
    rows = request_cache.get(
        f"backend:forms:{name}",
        lambda: FormService(auth_token=get_auth_token()).search_forms(name),
    )
    return [
        {
            "formId": r.get("formId"),
            "formName": r.get("formName"),
            "formKey": r.get("formKey"),
        }
        for r in rows[:_LIMIT]
    ]


@tool(description=load_prompt("tools/search_roles.md"))
def search_roles(name: str = "") -> list[dict]:
    rows = request_cache.get(
        f"backend:roles:{name}",
        lambda: RoleService(auth_token=get_auth_token()).search_roles(name),
    )
    return [
        {"name": r.get("roleName", ""), "key": f"ROLE{r.get('roleId', '')}"}
        for r in rows[:_LIMIT]
        if r.get("roleId")
    ]


@tool(description=load_prompt("tools/search_flow_models.md"))
def search_flow_models(name: str = "") -> list[dict]:
    rows = request_cache.get(
        f"backend:models:{name}",
        lambda: FlowService(auth_token=get_auth_token()).search_flow_models(name),
    )
    return [
        {
            "modelId": r.get("modelId"),
            "modelName": r.get("modelName"),
            "modelKey": r.get("modelKey"),
        }
        for r in rows[:_LIMIT]
    ]
