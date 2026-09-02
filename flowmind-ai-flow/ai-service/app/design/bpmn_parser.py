"""
FlowMind 智能流程设计服务 - BPMN XML 反解析器

可视化流程设计器传回的是 BPMN XML（前端 bpmn-js 产物），但 LLM 的结构化输出
与校验层都基于扁平 JSON（nodes / edges）。本模块把 XML 反解析为扁平结构，
避免把整段 XML 塞给模型，同时让增量修改与基线保留校验真正生效。

正方向：bpmn_generator.generate_bpmn_xml(nodes, edges) -> xml
反方向：parse_bpmn_to_flat(xml) -> {nodes, edges}
"""

from typing import Any

from lxml import etree

# 元素 localname -> FlowNode.type（与 domain/design_models.py 的 Literal 对齐）
_NODE_TYPE_MAP = {
    "startEvent": "START_EVENT",
    "endEvent": "END_EVENT",
    "userTask": "USER_TASK",
    "exclusiveGateway": "EXCLUSIVE_GATEWAY",
    "parallelGateway": "PARALLEL_GATEWAY",
    "inclusiveGateway": "INCLUSIVE_GATEWAY",
    "complexGateway": "COMPLEX_GATEWAY",
    "eventBasedGateway": "EVENT_GATEWAY",
    "intermediateThrowEvent": "INTERMEDIATE_THROW_EVENT",
}


def _localname(qname: str) -> str:
    """取元素/属性的 localname，屏蔽 bpmn2: / flowable: / 默认命名空间等前缀差异。"""
    return etree.QName(qname).localname


def _attr(el: etree._Element, localname: str) -> str | None:
    """按 localname 取属性值（用于 flowable:formKey 等命名空间属性）。"""
    for key, value in el.attrib.items():
        if _localname(key) == localname:
            return value
    return None


def _child_text(el: etree._Element, localname: str) -> str | None:
    """取直接子元素文本（用于 conditionExpression 等）。"""
    for child in el:
        if _localname(child.tag) == localname:
            return child.text
    return None


def _parse_node(el: etree._Element, node_type: str) -> dict[str, Any]:
    node: dict[str, Any] = {
        "type": node_type,
        "id": el.get("id") or "",
        "name": el.get("name") or "",
    }
    if node_type == "USER_TASK":
        form_key = _attr(el, "formKey")
        if form_key:
            node["form_key"] = form_key
        assignee = _attr(el, "assignee")
        if assignee:
            node["assignee"] = assignee
        groups = _attr(el, "candidateGroups")
        if groups:
            node["candidate_groups"] = [
                g.strip() for g in groups.split(",") if g.strip()
            ]
        data_type = _attr(el, "dataType")
        if data_type:
            node["data_type"] = data_type
    return node


def _parse_edge(el: etree._Element) -> dict[str, Any] | None:
    source = el.get("sourceRef")
    target = el.get("targetRef")
    if not source or not target:
        return None
    edge: dict[str, Any] = {"source": source, "target": target}
    condition = _child_text(el, "conditionExpression")
    if condition and condition.strip():
        edge["condition"] = condition.strip()
    return edge


def parse_bpmn_to_flat(bpmn_xml: str) -> dict[str, Any] | None:
    """把 BPMN XML 反解析为扁平 {nodes, edges}。

    解析失败或解析不出任何节点时返回 None，由调用方回退到原有逻辑。
    """
    if not bpmn_xml or not bpmn_xml.strip():
        return None
    try:
        root = etree.fromstring(bpmn_xml.encode("utf-8"))
    except (etree.XMLSyntaxError, ValueError):
        return None

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for el in root.iter():
        local = _localname(el.tag)
        node_type = _NODE_TYPE_MAP.get(local)
        if node_type is not None:
            node = _parse_node(el, node_type)
            if node["id"]:
                nodes.append(node)
        elif local == "sequenceFlow":
            edge = _parse_edge(el)
            if edge is not None:
                edges.append(edge)

    return {"nodes": nodes, "edges": edges} if nodes else None


def enrich_flow_baseline(current_form_data: dict[str, Any] | None) -> dict[str, Any]:
    """flow_design 基线补齐：只有 bpmn_xml 而缺 nodes/edges 时，反解析为扁平结构。

    保持幂等：已有 nodes/edges、或没有 XML、或解析失败时，原样返回。
    """
    if not isinstance(current_form_data, dict):
        return current_form_data or {}
    if current_form_data.get("nodes") or current_form_data.get("edges"):
        return current_form_data
    bpmn_xml = current_form_data.get("bpmnXml") or current_form_data.get("bpmn_xml")
    if not bpmn_xml:
        return current_form_data

    flat = parse_bpmn_to_flat(bpmn_xml)
    if not flat:
        return current_form_data

    enriched = dict(current_form_data)
    enriched["nodes"] = flat["nodes"]
    enriched["edges"] = flat["edges"]
    return enriched
