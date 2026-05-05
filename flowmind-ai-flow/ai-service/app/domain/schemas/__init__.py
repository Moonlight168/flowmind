"""
FlowMind 智能流程设计服务 - JSON Schema 定义层
"""

from app.adapters.base import build_json_schema
from app.domain.schemas.design_schemas import (
    CATEGORY_GENERATION_SCHEMA,
    FLOW_DESIGN_SCHEMA,
    FORM_GENERATION_SCHEMA,
)
from app.domain.schemas.schema_registry import SchemaRegistry

SchemaRegistry.register("flow_design", FLOW_DESIGN_SCHEMA)
SchemaRegistry.register("category_classification", CATEGORY_GENERATION_SCHEMA)
SchemaRegistry.register("form_generation", FORM_GENERATION_SCHEMA)

__all__ = [
    "CATEGORY_GENERATION_SCHEMA",
    "FLOW_DESIGN_SCHEMA",
    "FORM_GENERATION_SCHEMA",
    "SchemaRegistry",
    "build_json_schema",
]
