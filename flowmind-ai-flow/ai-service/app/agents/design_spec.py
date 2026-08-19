"""
FlowMind 智能流程设计服务 - 设计规格配置 + 预取摘要

DESIGN_SPEC：按 design_type 定义预取清单 / schema / 基线字段。
预取的是"轻量摘要"（标识字段），不是完整对象。
"""

from app.adapters.backend.category import CategoryService
from app.adapters.backend.flow import FlowService
from app.adapters.backend.form import FormService
from app.adapters.backend.role import RoleService
from app.domain.schemas.pydantic_models import (
    CategoryDesign,
    FlowDesign,
    FormDesign,
)

DESIGN_SPEC = {
    "flow_design": {
        "prefetch": ["categories", "forms", "roles", "models"],
        "schema": FlowDesign,
        "baseline": ["nodes", "edges"],
    },
    "form_design": {
        "prefetch": ["forms"],
        "schema": FormDesign,
        "baseline": ["widgetList", "formConfig"],
    },
    "category_design": {
        "prefetch": ["categories"],
        "schema": CategoryDesign,
        "baseline": ["category_name", "code", "remark"],
    },
}

_PREFETCH_LIMIT = 50


def prefetch_summaries(design_type: str, auth_token: str | None = None) -> dict:
    """按 design_type 预取轻量摘要（service 内部兜底返回空列表，失败不抛）"""
    spec = DESIGN_SPEC.get(design_type)
    if not spec:
        return {}
    return {name: _PREFETCHERS[name](auth_token) for name in spec["prefetch"]}


def _summary_categories(auth_token):
    rows = CategoryService(auth_token=auth_token).search_categories()
    return [
        {"categoryId": r.get("categoryId"), "categoryName": r.get("categoryName"), "code": r.get("code")}
        for r in rows[:_PREFETCH_LIMIT]
    ]


def _summary_forms(auth_token):
    rows = FormService(auth_token=auth_token).search_forms("")
    return [
        {"formId": r.get("formId"), "formName": r.get("formName"), "formKey": r.get("formKey")}
        for r in rows[:_PREFETCH_LIMIT]
    ]


def _summary_roles(auth_token):
    rows = RoleService(auth_token=auth_token).search_roles()
    return [
        {"name": r.get("roleName", ""), "key": f"ROLE{r.get('roleId', '')}"}
        for r in rows[:_PREFETCH_LIMIT]
        if r.get("roleId")
    ]


def _summary_models(auth_token):
    rows = FlowService(auth_token=auth_token).search_flow_models()
    return [
        {"modelId": r.get("modelId"), "modelName": r.get("modelName"), "modelKey": r.get("modelKey")}
        for r in rows[:_PREFETCH_LIMIT]
    ]


_PREFETCHERS = {
    "categories": _summary_categories,
    "forms": _summary_forms,
    "roles": _summary_roles,
    "models": _summary_models,
}
