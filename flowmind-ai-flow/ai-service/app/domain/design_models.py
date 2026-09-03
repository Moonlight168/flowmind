"""Structured AI design operations.

The model describes a change set. The application applies it to a copy of the
current artifact and validates the materialized result before it can be used.
"""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FlowCondition(StrictModel):
    field: str
    operator: Literal["eq", "ne", "gt", "ge", "lt", "le"]
    value: Any


class FlowNode(StrictModel):
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
    candidate_users: list[str] | None = None
    text: str | None = None
    data_type: str | None = None


class FlowEdge(StrictModel):
    id: str | None = None
    name: str | None = None
    source: str
    target: str
    condition: FlowCondition | str | None = None
    is_default: bool = False


class ReplaceGraphOperation(StrictModel):
    op: Literal["replace_graph"]
    nodes: list[FlowNode]
    edges: list[FlowEdge] = Field(default_factory=list)


class AddFlowNodeOperation(StrictModel):
    op: Literal["add_node"]
    node: FlowNode
    after_id: str | None = None


class UpdateFlowNodeOperation(StrictModel):
    op: Literal["update_node"]
    node_id: str
    changes: dict[str, Any]


class RemoveFlowNodeOperation(StrictModel):
    op: Literal["remove_node"]
    node_id: str


class AddFlowEdgeOperation(StrictModel):
    op: Literal["add_edge"]
    edge: FlowEdge


class UpdateFlowEdgeOperation(StrictModel):
    op: Literal["update_edge"]
    edge_id: str | None = None
    source: str | None = None
    target: str | None = None
    changes: dict[str, Any]


class RemoveFlowEdgeOperation(StrictModel):
    op: Literal["remove_edge"]
    edge_id: str | None = None
    source: str | None = None
    target: str | None = None


FlowOperation = Annotated[
    ReplaceGraphOperation
    | AddFlowNodeOperation
    | UpdateFlowNodeOperation
    | RemoveFlowNodeOperation
    | AddFlowEdgeOperation
    | UpdateFlowEdgeOperation
    | RemoveFlowEdgeOperation,
    Field(discriminator="op"),
]


class FlowDesign(StrictModel):
    operations: list[FlowOperation] = Field(min_length=1)


class FormWidget(StrictModel):
    type: str
    formItemFlag: bool  # noqa: N815 - VForm3 uses camelCase
    options: dict[str, Any]
    id: str | None = None
    key: int | str | None = None
    widgetList: list[dict[str, Any]] | None = None  # noqa: N815
    cols: list[dict[str, Any]] | None = None
    tabs: list[dict[str, Any]] | None = None
    rows: list[dict[str, Any]] | None = None
    category: str | None = None
    internal: bool | None = None


class ReplaceFormOperation(StrictModel):
    op: Literal["replace_form"]
    form_name: str
    widgetList: list[FormWidget]  # noqa: N815
    formConfig: dict[str, Any] | None = None  # noqa: N815


class AddFormWidgetOperation(StrictModel):
    op: Literal["add_widget"]
    widget: FormWidget
    after_name: str | None = None


class UpdateFormWidgetOperation(StrictModel):
    op: Literal["update_widget"]
    widget_name: str
    changes: dict[str, Any]


class RemoveFormWidgetOperation(StrictModel):
    op: Literal["remove_widget"]
    widget_name: str


class MoveFormWidgetOperation(StrictModel):
    op: Literal["move_widget"]
    widget_name: str
    after_name: str | None = None


FormOperation = Annotated[
    ReplaceFormOperation
    | AddFormWidgetOperation
    | UpdateFormWidgetOperation
    | RemoveFormWidgetOperation
    | MoveFormWidgetOperation,
    Field(discriminator="op"),
]


class FormDesign(StrictModel):
    operations: list[FormOperation] = Field(min_length=1)


class CategoryChanges(StrictModel):
    category_name: str | None = None
    code: str | None = None
    remark: str | None = None


class UpdateCategoryOperation(StrictModel):
    op: Literal["update_category"]
    changes: CategoryChanges


class CategoryDesign(StrictModel):
    operations: list[UpdateCategoryOperation] = Field(min_length=1)


class FlowMetadataChanges(StrictModel):
    flow_name: str | None = None
    code: str | None = None
    description: str | None = None
    flow_key: str | None = None


class UpdateFlowMetadataOperation(StrictModel):
    op: Literal["update_flow_metadata"]
    changes: FlowMetadataChanges


class BasicDesign(StrictModel):
    """Operations for the basic-information mode of flow design."""

    operations: list[UpdateFlowMetadataOperation] = Field(min_length=1)
