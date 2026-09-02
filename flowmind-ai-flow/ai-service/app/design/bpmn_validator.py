"""
FlowMind 智能审批服务 - BPMN XML 验证器

本模块提供对 BPMN XML 结构的静态验证能力，包括：
- XML 可解析性和 process 元素存在性检查
- 起止事件存在性检查
- 节点 ID 唯一性检查
- 连线 sourceRef / targetRef 引用有效性检查
- 排他网关分支数量和条件表达式检查
- 从 startEvent 到 endEvent 的连通性检查（BFS）
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from lxml import etree

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"

NSMAP = {"bpmn": BPMN_NS}

# 需要检查连通性的活动节点标签集合
ACTIVITY_TAGS: set[str] = {
    f"{{{BPMN_NS}}}userTask",
    f"{{{BPMN_NS}}}exclusiveGateway",
    f"{{{BPMN_NS}}}parallelGateway",
    f"{{{BPMN_NS}}}intermediateThrowEvent",
    f"{{{BPMN_NS}}}subProcess",
}

# 结构性错误的规则 ID 集合（用于决定是否执行连通性检查）
STRUCTURAL_ERROR_RULES = {
    "V001",
    "V002",
    "V003",
    "V005",
    "V006",
    "V007",
    "V008",
    "V009",
}


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ValidationError:
    """单条验证问题，包含规则 ID、可读消息和可选的关联元素 ID"""

    rule_id: str
    message: str
    element_id: str | None = None


@dataclass
class ValidationResult:
    """验证结果聚合，区分 ERROR 级别的 errors 和 WARNING 级别的 warnings"""

    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 核心验证函数
# ---------------------------------------------------------------------------


def validate_bpmn_xml(xml_string: str) -> ValidationResult:
    """验证 BPMN XML 字符串的结构和连通性

    Args:
        xml_string: 待验证的 BPMN XML 字符串

    Returns:
        ValidationResult 包含 errors（致命）和 warnings（建议）
    """
    errors: list[ValidationError] = []
    warnings: list[ValidationError] = []

    # ---- V001: XML 可解析性 + process 元素存在 ----
    process = _try_parse_and_get_process(xml_string, errors)
    if process is None:
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    # 收集所有具有 id 属性的节点元素（非 sequenceFlow）
    node_ids: list[str] = []
    nodes_by_id: dict[str, etree._Element] = {}
    for elem in process:
        eid = elem.get("id")
        if eid is not None and elem.tag != f"{{{BPMN_NS}}}sequenceFlow":
            node_ids.append(eid)
            nodes_by_id[eid] = elem

    # ---- V002: startEvent 存在 ----
    start_events = process.findall("bpmn:startEvent", NSMAP)
    if not start_events:
        errors.append(
            ValidationError(
                rule_id="V002",
                message="process 中缺少 startEvent 元素",
            )
        )

    # ---- V003: endEvent 存在 ----
    end_events = process.findall("bpmn:endEvent", NSMAP)
    if not end_events:
        errors.append(
            ValidationError(
                rule_id="V003",
                message="process 中缺少 endEvent 元素",
            )
        )

    # ---- V005: 节点 ID 唯一性 ----
    seen: set[str] = set()
    for eid in node_ids:
        if eid in seen:
            errors.append(
                ValidationError(
                    rule_id="V005",
                    message=f"节点 ID 重复: '{eid}'",
                    element_id=eid,
                )
            )
        seen.add(eid)

    # 收集所有节点 ID（含 sequenceFlow 的 id，用于唯一性检查）
    all_elem_ids: set[str] = set()
    for elem in process:
        eid = elem.get("id")
        if eid is not None:
            if eid in all_elem_ids:
                errors.append(
                    ValidationError(
                        rule_id="V005",
                        message=f"元素 ID 重复: '{eid}'",
                        element_id=eid,
                    )
                )
            all_elem_ids.add(eid)

    # ---- V006 / V007: sequenceFlow 引用有效性 ----
    # 收集所有元素 ID（含 sequenceFlow）用于引用检查
    all_ids: set[str] = set()
    for elem in process:
        eid = elem.get("id")
        if eid is not None:
            all_ids.add(eid)

    sequence_flows = process.findall("bpmn:sequenceFlow", NSMAP)
    flows_from: dict[str, list[str]] = {}  # node_id -> [flow_id]
    flows_to: dict[str, list[str]] = {}

    for flow in sequence_flows:
        flow_id = flow.get("id", "<unknown>")
        source = flow.get("sourceRef")
        target = flow.get("targetRef")

        if source and source not in nodes_by_id:
            errors.append(
                ValidationError(
                    rule_id="V006",
                    message=f"sequenceFlow '{flow_id}' 的 sourceRef '{source}' 引用不存在的节点",
                    element_id=flow_id,
                )
            )
        if target and target not in nodes_by_id:
            errors.append(
                ValidationError(
                    rule_id="V007",
                    message=f"sequenceFlow '{flow_id}' 的 targetRef '{target}' 引用不存在的节点",
                    element_id=flow_id,
                )
            )

        # 记录出入关系（用于后续网关和连通性检查）
        if source:
            flows_from.setdefault(source, []).append(flow_id)
        if target:
            flows_to.setdefault(target, []).append(flow_id)

    # ---- V008 / V009: 排他网关检查 ----
    exclusive_gateways = process.findall("bpmn:exclusiveGateway", NSMAP)
    for gw in exclusive_gateways:
        gw_id = gw.get("id", "<unknown>")
        out_flows = flows_from.get(gw_id, [])

        if len(out_flows) < 2:
            errors.append(
                ValidationError(
                    rule_id="V008",
                    message=f"排他网关 '{gw_id}' 出线数量不足（至少需要 2 条，当前 {len(out_flows)} 条）",
                    element_id=gw_id,
                )
            )

        # V009: 每条出线必须有 conditionExpression
        for flow_id in out_flows:
            flow_elem = process.find(f"bpmn:sequenceFlow[@id='{flow_id}']", NSMAP)
            if flow_elem is not None:
                cond = flow_elem.find("bpmn:conditionExpression", NSMAP)
                if cond is None:
                    errors.append(
                        ValidationError(
                            rule_id="V009",
                            message=f"排他网关 '{gw_id}' 的出线 '{flow_id}' 缺少 conditionExpression",
                            element_id=flow_id,
                        )
                    )

    # ---- 连通性检查（仅在无结构性错误时执行）----
    has_structural_errors = any(e.rule_id in STRUCTURAL_ERROR_RULES for e in errors)

    if not has_structural_errors and start_events and end_events:
        # V010: 所有活动节点从 startEvent 可达
        start_id = start_events[0].get("id")
        reachable_from_start = _find_reachable(process, start_id, flows_from)

        for eid in node_ids:
            elem = nodes_by_id[eid]
            if elem.tag in ACTIVITY_TAGS and eid not in reachable_from_start:
                warnings.append(
                    ValidationError(
                        rule_id="V010",
                        message=f"节点 '{eid}' 无法从 startEvent 到达",
                        element_id=eid,
                    )
                )

        # V011: 所有活动节点可到达 endEvent
        end_id = end_events[0].get("id")
        reachable_to_end = _find_reachable_reverse(process, end_id, flows_to)

        for eid in node_ids:
            elem = nodes_by_id[eid]
            if elem.tag in ACTIVITY_TAGS and eid not in reachable_to_end:
                # 避免重复报告同一个节点
                already_warned = any(
                    w.element_id == eid and w.rule_id == "V011" for w in warnings
                )
                if not already_warned:
                    warnings.append(
                        ValidationError(
                            rule_id="V011",
                            message=f"节点 '{eid}' 无法到达 endEvent",
                            element_id=eid,
                        )
                    )

    is_valid = len(errors) == 0
    return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)


# ---------------------------------------------------------------------------
# 内部辅助函数
# ---------------------------------------------------------------------------


def _try_parse_and_get_process(
    xml_string: str,
    errors: list[ValidationError],
) -> etree._Element | None:
    """尝试解析 XML 并返回 <process> 元素，失败时向 errors 追加 V001"""
    if not xml_string or not xml_string.strip():
        errors.append(
            ValidationError(
                rule_id="V001",
                message="XML 字符串为空或仅包含空白字符",
            )
        )
        return None

    try:
        root = etree.fromstring(xml_string.encode("utf-8"))
    except etree.XMLSyntaxError as exc:
        errors.append(
            ValidationError(
                rule_id="V001",
                message=f"XML 解析失败: {exc}",
            )
        )
        return None

    # 在 definitions 下查找 process
    process = root.find("bpmn:process", NSMAP)
    if process is None:
        # 尝试直接作为 process
        if root.tag == f"{{{BPMN_NS}}}process":
            process = root
        else:
            errors.append(
                ValidationError(
                    rule_id="V001",
                    message="XML 中未找到 <process> 元素",
                )
            )
            return None

    return process


def _find_reachable(
    process: etree._Element,
    start_id: str,
    flows_from: dict[str, list[str]],
) -> set[str]:
    """从 start_id 出发进行正向 BFS，返回所有可达节点 ID"""
    adj: dict[str, list[str]] = {}
    for flow in process.findall("bpmn:sequenceFlow", NSMAP):
        src = flow.get("sourceRef")
        tgt = flow.get("targetRef")
        if src and tgt:
            adj.setdefault(src, []).append(tgt)

    visited: set[str] = set()
    queue: deque[str] = deque([start_id])
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                queue.append(neighbor)
    return visited


def _find_reachable_reverse(
    process: etree._Element,
    end_id: str,
    flows_to: dict[str, list[str]],
) -> set[str]:
    """从 end_id 出发进行反向 BFS，返回所有能到达 end_id 的节点 ID"""
    rev_adj: dict[str, list[str]] = {}
    for flow in process.findall("bpmn:sequenceFlow", NSMAP):
        src = flow.get("sourceRef")
        tgt = flow.get("targetRef")
        if src and tgt:
            rev_adj.setdefault(tgt, []).append(src)

    visited: set[str] = set()
    queue: deque[str] = deque([end_id])
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        for neighbor in rev_adj.get(node, []):
            if neighbor not in visited:
                queue.append(neighbor)
    return visited
