"""
FlowMind 智能流程设计服务 - 设计规格配置

按 design_type 定义结构化输出 schema 与检索工具集。
"""

from app.agents.tools import (
    search_categories,
    search_flow_models,
    search_forms,
    search_roles,
)
from app.domain.schemas.pydantic_models import (
    CategoryDesign,
    FlowDesign,
    FormDesign,
)

DESIGN_SPEC = {
    "flow_design": {
        "schema": FlowDesign,
        "tools": [search_categories, search_forms, search_roles, search_flow_models],
    },
    "form_design": {
        "schema": FormDesign,
        "tools": [search_forms],
    },
    "category_design": {
        "schema": CategoryDesign,
        "tools": [search_categories],
    },
}
