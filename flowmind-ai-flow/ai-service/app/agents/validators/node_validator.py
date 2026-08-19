"""
FlowMind 智能流程设计服务 - 节点级校验器

在 JSON 层校验节点结构（flow_design 专属），生成 BPMN 之前早失败。
"""

from app.agents.validators.base import (
    ValidationError,
    ValidationResult,
    ValidationSeverity,
    ValidatorContext,
)

ALLOWED_NODE_TYPES = {
    "START_EVENT",
    "END_EVENT",
    "USER_TASK",
    "EXCLUSIVE_GATEWAY",
    "PARALLEL_GATEWAY",
    "INCLUSIVE_GATEWAY",
    "COMPLEX_GATEWAY",
    "EVENT_GATEWAY",
    "INTERMEDIATE_THROW_EVENT",
}

GATEWAY_TYPES = {
    "EXCLUSIVE_GATEWAY",
    "PARALLEL_GATEWAY",
    "INCLUSIVE_GATEWAY",
    "COMPLEX_GATEWAY",
    "EVENT_GATEWAY",
}


class NodeValidator:
    name = "node"

    def validate(self, output: dict, context: ValidatorContext) -> ValidationResult:
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []
        nodes = output.get("nodes", []) or []
        edges = output.get("edges", []) or []

        # NODE_N001: nodes 非空
        if not nodes:
            errors.append(ValidationError("NODE_N001", "nodes 数组为空"))
            return ValidationResult.from_errors(errors)

        # NODE_N002: 每个 node 有 type 与 name
        # NODE_N003: id 全局唯一
        # NODE_N007: type 在白名单
        # NODE_N008: name 长度
        seen_ids: set[str] = set()
        for node in nodes:
            if not node.get("type") or not node.get("name"):
                errors.append(ValidationError(
                    "NODE_N002",
                    f"节点缺少 type 或 name: {node.get('id', '<无id>')}",
                    element_id=node.get("id"),
                ))
            node_id = node.get("id")
            if node_id:
                if node_id in seen_ids:
                    errors.append(ValidationError("NODE_N003", f"节点 id 重复: '{node_id}'", element_id=node_id))
                seen_ids.add(node_id)
            node_type = (node.get("type") or "").upper()
            if node_type and node_type not in ALLOWED_NODE_TYPES:
                errors.append(ValidationError(
                    "NODE_N007", f"节点类型不在白名单内: '{node.get('type')}'", element_id=node.get("id"),
                ))
            name = node.get("name", "")
            if not name or not name.strip() or len(name) > 50:
                warnings.append(ValidationError(
                    "NODE_N008", f"节点名称长度应为 1-50 且非空白: '{name}'", severity=ValidationSeverity.WARNING, element_id=node.get("id"),
                ))

        # NODE_N004: USER_TASK 至少 1 个审批/表单字段非空
        for node in nodes:
            if (node.get("type") or "").upper() != "USER_TASK":
                continue
            if not any(node.get(f) for f in ("form_key", "candidate_groups", "assignee", "data_type")):
                errors.append(ValidationError(
                    "NODE_N004",
                    f"审批节点 '{node.get('name')}' 未绑定表单或审批人（form_key/candidate_groups/assignee 至少一项）",
                    element_id=node.get("id"),
                ))

        # NODE_N005: START_EVENT 必须有 form_key
        for node in nodes:
            if (node.get("type") or "").upper() != "START_EVENT":
                continue
            form_key = node.get("form_key", "")
            if not form_key:
                errors.append(ValidationError(
                    "NODE_N005", "开始节点缺少 form_key，请调用 search_forms 选择表单", element_id=node.get("id"),
                ))
            elif context.available_forms and not _form_key_exists(form_key, context.available_forms):
                errors.append(ValidationError(
                    "NODE_N005", f"开始节点的 form_key '{form_key}' 不在可用表单列表中", element_id=node.get("id"),
                ))

        # NODE_N006: GATEWAY 类节点必须有 ≥2 出边
        for node in nodes:
            if (node.get("type") or "").upper() not in GATEWAY_TYPES:
                continue
            out_count = sum(1 for e in edges if e.get("source") == node.get("id"))
            if out_count < 2:
                errors.append(ValidationError(
                    "NODE_N006",
                    f"网关 '{node.get('name')}' 出边数量不足（至少 2 条，当前 {out_count} 条）",
                    element_id=node.get("id"),
                ))

        return ValidationResult.from_errors(errors + warnings)


def _form_key_exists(form_key: str, available_forms: list[dict]) -> bool:
    """宽松匹配 form_key 是否在可用表单列表中"""
    for form in available_forms:
        if form_key in (form.get("formId"), form.get("id"), form.get("formKey"), form.get("form_key")):
            return True
    return False
