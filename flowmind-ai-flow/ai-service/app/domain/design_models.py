"""Structured AI design operations.

The model describes a change set. The application applies it to a copy of the
current artifact and validates the materialized result before it can be used.
"""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    priority: int | str | None = None
    due_date: str | None = None
    multi_instance: dict[str, Any] | None = None
    task_listeners: list[dict[str, Any]] | None = None
    execution_listeners: list[dict[str, Any]] | None = None
    extension_properties: dict[str, Any] | None = None


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


class FlowFormDraft(StrictModel):
    """A complete, directly creatable form proposed for flow nodes."""

    form_name: str = Field(min_length=2, max_length=50)
    node_ids: list[str] = Field(min_length=1)
    widgetList: list[FormWidget] = Field(min_length=1)  # noqa: N815
    formConfig: dict[str, Any] = Field(default_factory=dict)  # noqa: N815

    @model_validator(mode="after")
    def validate_business_fields(self) -> "FlowFormDraft":
        business_fields: list[dict[str, Any]] = []

        def collect(value: object) -> None:
            if isinstance(value, dict):
                if value.get("formItemFlag") is True:
                    business_fields.append(value)
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)

        collect([widget.model_dump() for widget in self.widgetList])
        if not business_fields:
            raise ValueError("generated form must contain at least one business field")
        for field in business_fields:
            options = field.get("options") or {}
            if not str(options.get("name") or "").strip() or not str(
                options.get("label") or ""
            ).strip():
                raise ValueError("generated form fields require options.name and options.label")
            if field.get("type") in {"radio", "checkbox", "select", "cascader"} and not (
                options.get("optionItems") or []
            ):
                raise ValueError("choice fields require non-empty options.optionItems")
        return self


class FlowDesign(StrictModel):
    operations: list[FlowOperation] = Field(min_length=1)
    new_forms: list[FlowFormDraft] = Field(default_factory=list)


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
    #: 新建/未命名表单时建议的表单名；已有名字的表单不必重复给出
    form_name: str | None = None


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
    #: 分类不存在时给出分类名称，前端据此在应用变更时创建
    category_name: str | None = None


class UpdateFlowMetadataOperation(StrictModel):
    op: Literal["update_flow_metadata"]
    changes: FlowMetadataChanges


class BasicDesign(StrictModel):
    """Operations for the basic-information mode of flow design."""

    operations: list[UpdateFlowMetadataOperation] = Field(min_length=1)
