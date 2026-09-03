"""
FlowMind 智能流程设计服务 - 基线保留校验器

增量修改场景：拦截 LLM 静默删除/修改基线内容（用户未要求却删/改了）。
覆盖 flow（nodes+edges）、form（widgetList）、category（code）。
"""

from app.design.validators.base import (
    ValidationError,
    ValidationResult,
    ValidatorContext,
)

# 用户指令中表示"删除"意图的关键词（避免"不要/取消"误报："不要财务审批改成总监"是修改非删除）
DELETE_KEYWORDS = ("删", "去掉", "移除")


class BaselineValidator:
    name = "baseline"

    def validate(self, output: dict, context: ValidatorContext) -> ValidationResult:
        if context.design_type == "flow_design":
            return self._validate_flow(output, context)
        if context.design_type == "form_design":
            return self._validate_form(output, context)
        if context.design_type == "category_design":
            return ValidationResult.ok()
        return ValidationResult.ok()

    def _has_delete_intent(self, context: ValidatorContext) -> bool:
        return any(kw in (context.user_input or "") for kw in DELETE_KEYWORDS)

    def _validate_flow(
        self, output: dict, context: ValidatorContext
    ) -> ValidationResult:
        if context.allow_full_replace and _has_operation(output, "replace_graph"):
            return ValidationResult.ok()
        baseline_nodes = context.current_form_data.get("nodes") or []
        if not baseline_nodes:
            return ValidationResult.ok()

        baseline_ids = {n.get("id") for n in baseline_nodes if n.get("id")}
        output_ids = {n.get("id") for n in (output.get("nodes") or []) if n.get("id")}
        deleted = baseline_ids - output_ids
        if deleted and not self._has_delete_intent(context):
            return ValidationResult.from_errors(
                [
                    ValidationError(
                        "BASE_B001",
                        f"删除了基线节点 {sorted(deleted)}，但用户未要求删除",
                    )
                ]
            )

        # edges 保留：基线的 source->target 连线不能被静默删
        baseline_edges = {
            (e.get("source"), e.get("target"))
            for e in (context.current_form_data.get("edges") or [])
        }
        output_edges = {
            (e.get("source"), e.get("target")) for e in (output.get("edges") or [])
        }
        deleted_edges = baseline_edges - output_edges
        deleted_edges = {
            edge for edge in deleted_edges if not _is_valid_edge_split(edge, output)
        }
        if deleted_edges and not self._has_delete_intent(context):
            return ValidationResult.from_errors(
                [
                    ValidationError(
                        "BASE_B002",
                        f"删除了基线连线 {sorted(map(str, deleted_edges))}，但用户未要求删除",
                    )
                ]
            )
        return ValidationResult.ok()

    def _validate_form(
        self, output: dict, context: ValidatorContext
    ) -> ValidationResult:
        if context.allow_full_replace and _has_operation(output, "replace_form"):
            return ValidationResult.ok()
        baseline_widgets = context.current_form_data.get("widgetList") or []
        if not baseline_widgets:
            return ValidationResult.ok()

        deleted = _widget_names(baseline_widgets) - _widget_names(
            output.get("widgetList") or []
        )
        if deleted and not self._has_delete_intent(context):
            return ValidationResult.from_errors(
                [
                    ValidationError(
                        "BASE_B003",
                        f"删除了基线字段 {sorted(deleted)}，但用户未要求删除",
                    )
                ]
            )
        return ValidationResult.ok()


def _has_operation(output: dict, operation_name: str) -> bool:
    return any(
        operation.get("op") == operation_name
        for operation in output.get("operations") or []
    )


def _is_valid_edge_split(edge: tuple, output: dict) -> bool:
    output_edges = {
        (item.get("source"), item.get("target")) for item in output.get("edges") or []
    }
    for operation in output.get("operations") or []:
        node_id = (operation.get("node") or {}).get("id")
        if operation.get("op") != "add_node" or operation.get("after_id") != edge[0]:
            continue
        if (edge[0], node_id) in output_edges and (node_id, edge[1]) in output_edges:
            return True
    return False


def _widget_names(widgets: list[dict]) -> set[str]:
    names: set[str] = set()
    for widget in widgets:
        name = (widget.get("options") or {}).get("name")
        if name:
            names.add(name)
        direct = widget.get("widgetList")
        if isinstance(direct, list):
            names.update(_widget_names(direct))
        for key in ("cols", "tabs", "rows"):
            for child in widget.get(key) or []:
                if not isinstance(child, dict):
                    continue
                children = child.get("widgetList")
                if isinstance(children, list):
                    names.update(_widget_names(children))
                for cell in child.get("cols") or child.get("cells") or []:
                    cell_children = (
                        cell.get("widgetList") if isinstance(cell, dict) else None
                    )
                    if isinstance(cell_children, list):
                        names.update(_widget_names(cell_children))
    return names
