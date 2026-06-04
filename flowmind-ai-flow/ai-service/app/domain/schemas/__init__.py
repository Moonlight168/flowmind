"""
FlowMind 智能流程设计服务 - JSON Schema 定义层
"""

from typing import Any

from app.domain.schemas.design_schemas import (
    CATEGORY_GENERATION_SCHEMA,
    FLOW_DESIGN_BASIC_SCHEMA,
    FLOW_DESIGN_NODES_SCHEMA,
    FORM_GENERATION_SCHEMA,
)
from app.domain.schemas.schema_registry import SchemaRegistry

SchemaRegistry.register("category_design", CATEGORY_GENERATION_SCHEMA)
SchemaRegistry.register("flow_design_basic", FLOW_DESIGN_BASIC_SCHEMA)
SchemaRegistry.register("flow_design_nodes", FLOW_DESIGN_NODES_SCHEMA)
SchemaRegistry.register("form_design", FORM_GENERATION_SCHEMA)


def build_json_schema(
    schema: dict[str, Any],
    name: str,
    description: str = "",
    strict: bool = True,
) -> dict[str, Any]:
    """构建 JSON Schema 格式的 response_format"""
    result = {
        "type": "json_schema",
        "json_schema": {"name": name, "schema": schema, "strict": strict},
    }
    if description:
        result["json_schema"]["description"] = description
    return result


__all__ = [
    "CATEGORY_GENERATION_SCHEMA",
    "FLOW_DESIGN_BASIC_SCHEMA",
    "FLOW_DESIGN_NODES_SCHEMA",
    "FORM_GENERATION_SCHEMA",
    "SchemaRegistry",
    "build_json_schema",
]
