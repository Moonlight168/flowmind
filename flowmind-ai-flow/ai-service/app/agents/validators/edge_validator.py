"""
FlowMind 智能流程设计服务 - 连线级校验器

在 JSON 层校验连线结构（flow_design 专属），生成 BPMN 之前早失败。
"""

from collections import deque

from app.agents.validators.base import (
    ValidationError,
    ValidationResult,
    ValidationSeverity,
    Validator,
    ValidatorContext,
)

from app.agents.validators.node_validator import GATEWAY_TYPES

VIRTUAL_START = "start"
VIRTUAL_END = "end"


class EdgeValidator:
    name = "edge"

    def validate(self, output: dict, context: ValidatorContext) -> ValidationResult:
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []
        nodes = output.get("nodes", []) or []
        edges = output.get("edges", []) or []

        node_ids = {n.get("id") for n in nodes if n.get("id")}
        node_by_id = {n.get("id"): n for n in nodes if n.get("id")}

        if not edges:
            return ValidationResult.ok()

        valid_refs = node_ids | {VIRTUAL_START, VIRTUAL_END}

        # EDGE_E001: source/target 引用存在
        for edge in edges:
            for field in ("source", "target"):
                ref = edge.get(field)
                if ref not in valid_refs:
                    errors.append(ValidationError(
                        "EDGE_E001", f"连线 {field} 引用不存在的节点: '{ref}'",
                    ))

        # EDGE_E002/E003: 网关出边 condition
        gateway_ids = {n.get("id") for n in nodes if (n.get("type") or "").upper() in GATEWAY_TYPES}
        for edge in edges:
            src = edge.get("source")
            if src not in gateway_ids:
                continue
            src_type = (node_by_id.get(src, {}).get("type") or "").upper()
            if src_type == "EXCLUSIVE_GATEWAY" and not edge.get("condition"):
                errors.append(ValidationError(
                    "EDGE_E002", f"排他网关 '{src}' 的出边缺少 condition 表达式",
                ))
            elif src_type == "PARALLEL_GATEWAY" and edge.get("condition"):
                errors.append(ValidationError(
                    "EDGE_E003", f"并行网关 '{src}' 的出边不能有 condition（语义冲突）",
                ))

        # EDGE_E005: 不允许自环
        for edge in edges:
            if edge.get("source") == edge.get("target") and edge.get("source") not in (VIRTUAL_START, VIRTUAL_END):
                errors.append(ValidationError("EDGE_E005", f"不允许自环: '{edge.get('source')}'"))

        # EDGE_E006: START_EVENT 只能 1 条出边
        start_ids = {n.get("id") for n in nodes if (n.get("type") or "").upper() == "START_EVENT"}
        start_out = [e for e in edges if e.get("source") in (start_ids | {VIRTUAL_START})]
        if len(start_out) > 1:
            errors.append(ValidationError("EDGE_E006", f"START_EVENT 只能有 1 条出边，当前 {len(start_out)} 条"))

        # EDGE_E007: END_EVENT 只能 1 条入边
        end_ids = {n.get("id") for n in nodes if (n.get("type") or "").upper() == "END_EVENT"}
        end_in = [e for e in edges if e.get("target") in (end_ids | {VIRTUAL_END})]
        if len(end_in) > 1:
            errors.append(ValidationError("EDGE_E007", f"END_EVENT 只能有 1 条入边，当前 {len(end_in)} 条"))

        # EDGE_E004: 孤立节点（从 start 不可达）WARNING
        reachable = _reachable_from_start(edges)
        for node_id in node_ids:
            if node_id not in reachable and node_id not in (start_ids | end_ids):
                warnings.append(ValidationError(
                    "EDGE_E004", f"节点 '{node_id}' 无法从 startEvent 到达",
                    severity=ValidationSeverity.WARNING, element_id=node_id,
                ))

        return ValidationResult.from_errors(errors + warnings)


def _reachable_from_start(edges: list[dict]) -> set[str]:
    """从虚拟起点 'start' 出发做 BFS，返回可达的节点 id 集合"""
    adj: dict[str, list[str]] = {}
    for edge in edges:
        adj.setdefault(edge.get("source"), []).append(edge.get("target"))

    visited: set[str] = set()
    queue: deque[str] = deque([VIRTUAL_START])
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                queue.append(neighbor)
    return visited
