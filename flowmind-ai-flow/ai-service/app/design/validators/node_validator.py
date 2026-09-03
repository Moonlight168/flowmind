"""
FlowMind 智能流程设计服务 - 节点级校验器

在 JSON 层校验节点结构（flow_design 专属），生成 BPMN 之前早失败。
"""

from app.design.validators.base import (
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
                errors.append(
                    ValidationError(
                        "NODE_N002",
                        f"节点缺少 type 或 name: {node.get('id', '<无id>')}",
                        element_id=node.get("id"),
                    )
                )

            candidate_groups = node.get("candidate_groups") or []
            if candidate_groups and context.roles_lookup_complete:
                available_role_keys = {
                    f"ROLE{role.get('roleId')}"
                    for role in context.available_roles
                    if role.get("roleId") is not None
                }
                missing_groups = sorted(set(candidate_groups) - available_role_keys)
                if missing_groups:
                    errors.append(
                        ValidationError(
                            "NODE_N009",
                            f"节点 '{node.get('name')}' 引用了不存在的角色: {missing_groups}",
                            element_id=node.get("id"),
                        )
                    )
            node_id = node.get("id")
            if node_id:
                if node_id in seen_ids:
                    errors.append(
                        ValidationError(
                            "NODE_N003",
                            f"节点 id 重复: '{node_id}'",
                            element_id=node_id,
                        )
                    )
                seen_ids.add(node_id)
            node_type = (node.get("type") or "").upper()
            if node_type and node_type not in ALLOWED_NODE_TYPES:
                errors.append(
                    ValidationError(
                        "NODE_N007",
                        f"节点类型不在白名单内: '{node.get('type')}'",
                        element_id=node.get("id"),
                    )
                )
            name = node.get("name", "")
            if not name or not name.strip() or len(name) > 50:
                warnings.append(
                    ValidationError(
                        "NODE_N008",
                        f"节点名称长度应为 1-50 且非空白: '{name}'",
                        severity=ValidationSeverity.WARNING,
                        element_id=node.get("id"),
                    )
                )

        # NODE_N004: USER_TASK 至少 1 个审批/表单字段非空
        for node in nodes:
            if (node.get("type") or "").upper() != "USER_TASK":
                continue
            if not any(
                node.get(f)
                for f in ("form_key", "candidate_groups", "assignee", "data_type")
            ):
                errors.append(
                    ValidationError(
                        "NODE_N004",
                        f"审批节点 '{node.get('name')}' 未绑定表单或审批人（form_key/candidate_groups/assignee 至少一项）",
                        element_id=node.get("id"),
                    )
                )

        # NODE_N005: START_EVENT 必须有 form_key；所有显式引用都必须存在。
        for node in nodes:
            form_key = node.get("form_key", "")
            is_start = (node.get("type") or "").upper() == "START_EVENT"
            if is_start and not form_key:
                errors.append(
                    ValidationError(
                        "NODE_N005",
                        "开始节点缺少 form_key，请调用 search_forms 选择表单",
                        element_id=node.get("id"),
                    )
                )
            elif (
                form_key
                and context.forms_lookup_complete
                and not _form_key_exists(form_key, context.available_forms)
            ):
                errors.append(
                    ValidationError(
                        "NODE_N005",
                        f"节点 '{node.get('name')}' 的 form_key '{form_key}' 不在可用表单列表中",
                        element_id=node.get("id"),
                    )
                )

        # NODE_N006: 网关必须是分支（至少两条出边）或汇聚（至少两条入边）。
        for node in nodes:
            if (node.get("type") or "").upper() not in GATEWAY_TYPES:
                continue
            out_count = sum(1 for e in edges if e.get("source") == node.get("id"))
            in_count = sum(1 for e in edges if e.get("target") == node.get("id"))
            is_split = out_count >= 2
            is_merge = in_count >= 2 and out_count == 1
            if not (is_split or is_merge):
                errors.append(
                    ValidationError(
                        "NODE_N006",
                        f"网关 '{node.get('name')}' 不是有效分支或汇聚"
                        f"（入边 {in_count} 条，出边 {out_count} 条）",
                        element_id=node.get("id"),
                    )
                )

        return ValidationResult.from_errors(errors + warnings)


def _form_key_exists(form_key: str, available_forms: list[dict]) -> bool:
    """匹配后端可能返回的数字 ID、业务 key 和 Flowable key。"""
    expected = _normalize_form_key(form_key)
    for form in available_forms:
        identifiers = (
            form.get("formId"),
            form.get("id"),
            form.get("formKey"),
            form.get("form_key"),
        )
        if any(
            _normalize_form_key(value) == expected
            for value in identifiers
            if value is not None
        ):
            return True
    return False


def _normalize_form_key(value: object) -> str:
    normalized = str(value).strip()
    return normalized[4:] if normalized.startswith("key_") else normalized
