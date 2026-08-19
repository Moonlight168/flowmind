"""
FlowMind 智能流程设计服务 - Pydantic 设计 schema

结构化输出用：with_structured_output 约束 LLM 输出字段合法。
extra="forbid" 等价 JSON Schema 的 additionalProperties: false。
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class FlowNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal[
        "START_EVENT",
        "END_EVENT",
        "USER_TASK",
        "EXCLUSIVE_GATEWAY",
        "PARALLEL_GATEWAY",
        "INCLUSIVE_GATEWAY",
        "COMPLEX_GATEWAY",
        "EVENT_GATEWAY",
        "INTERMEDIATE_THROW_EVENT",
    ]
    id: str
    name: str
    form_key: str | None = None
    assignee: str | None = None
    candidate_groups: list[str] | None = None
    text: str | None = None
    data_type: str | None = None


class FlowEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    target: str
    condition: str | None = None


class FlowDesign(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[FlowNode]
    edges: list[FlowEdge] = []


class FormWidget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    formItemFlag: bool  # noqa: N815 - VForm3 字段名必须 camelCase
    options: dict  # options 字段过多，内部不逐个锁，用 dict


class FormDesign(BaseModel):
    model_config = ConfigDict(extra="forbid")

    form_name: str
    node_role: Literal["applicant", "approver", "cc"] | None = None
    widgetList: list[FormWidget]  # noqa: N815 - VForm3 字段名必须 camelCase
    formConfig: dict | None = None  # noqa: N815 - VForm3 字段名必须 camelCase


class CategoryDesign(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_name: str
    code: str
    remark: str | None = None


class BasicDesign(BaseModel):
    """flow_design basic 模式：仅流程基本信息"""
    model_config = ConfigDict(extra="forbid")

    flow_name: str
    code: str
    description: str | None = None
    flow_key: str | None = None
