"""
FlowMind 智能审批服务 - BPMN XML 生成器

本模块提供将 nodes 结构转换为 BPMN XML 的功能。
"""

import json
import re

import lxml.etree as etree

Bounds = tuple[float, float, float, float]

GENERATE_BPMN_XML_SCHEMA = {
    "type": "object",
    "properties": {
        "bpmn_structure": {
            "type": "object",
            "description": "流程结构，包含 nodes 列表",
        },
        "category": {
            "type": "object",
            "description": "分类信息",
        },
    },
    "required": ["bpmn_structure", "category"],
}


def generate_bpmn_xml(bpmn_structure: dict, category: dict) -> str:
    """生成 BPMN XML 格式的流程定义

    支持所有节点类型：USER_TASK、EXCLUSIVE_GATEWAY、PARALLEL_GATEWAY、INCLUSIVE_GATEWAY、
    COMPLEX_GATEWAY、EVENT_GATEWAY、INTERMEDIATE_THROW_EVENT
    支持 Flowable 扩展属性：formKey、assignee、candidateGroups、dataType
    支持自定义 edges 或自动生成线性连线

    Args:
        bpmn_structure: 流程结构，包含 nodes 列表和可选的 edges 列表
        category: 分类信息

    Returns:
        BPMN XML 字符串
    """
    nodes = bpmn_structure.get("nodes", [])
    custom_edges = bpmn_structure.get("edges", [])
    category_name = category.get("category_name", category.get("categoryName", "流程"))
    process_id = f"Process_{category.get('code', 'default')}"

    ns = _get_bpmn_namespaces()
    flowable_ns = "http://flowable.org/bpmn"
    ns["flowable"] = flowable_ns
    ns["xsi"] = "http://www.w3.org/2001/XMLSchema-instance"

    definitions = _create_definitions_element(ns)
    process = _create_process_element(definitions, ns, process_id, category_name)

    # 为节点分配 ID
    node_ids = _assign_node_ids(nodes)

    # 创建所有节点元素
    _create_node_elements(process, ns, nodes, node_ids, flowable_ns)

    # 创建连线
    if custom_edges:
        _create_custom_edges(process, ns, custom_edges, node_ids, nodes)
    else:
        _create_auto_edges(process, ns, nodes, node_ids)

    # 生成 BPMNDI 画布布局
    _create_layered_bpmn_diagram(
        definitions, ns, process_id, nodes, node_ids, custom_edges
    )

    return etree.tostring(
        definitions, encoding="utf-8", xml_declaration=True, pretty_print=True
    ).decode("utf-8")


def _get_bpmn_namespaces() -> dict[str, str]:
    """获取 BPMN XML 命名空间

    注意：使用 bpmn2: 前缀以匹配前端 bpmn-js 的期望格式
    """
    return {
        "bpmn2": "http://www.omg.org/spec/BPMN/20100524/MODEL",
        "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
        "dc": "http://www.omg.org/spec/DD/20100524/DC",
        "di": "http://www.omg.org/spec/DD/20100524/DI",
    }


def _create_definitions_element(ns: dict[str, str]) -> etree._Element:
    """创建 BPMN definitions 根元素"""
    return etree.Element(
        "{%s}definitions" % ns["bpmn2"],
        id="Definitions_1",
        targetNamespace="http://bpmn.io/schema/bpmn",
        nsmap=ns,
    )


def _create_process_element(
    definitions: etree._Element,
    ns: dict[str, str],
    process_id: str,
    process_name: str,
) -> etree._Element:
    """创建 BPMN process 元素"""
    return etree.SubElement(
        definitions,
        "{%s}process" % ns["bpmn2"],
        id=process_id,
        name=process_name,
        isExecutable="true",
    )


def _assign_node_ids(nodes: list[dict]) -> list[str]:
    """为节点分配唯一 ID

    如果节点已有 id 则使用，否则自动生成

    Returns:
        节点 ID 列表（与 nodes 顺序一致）
    """
    node_ids = []
    task_counter = 1
    gw_counter = 1
    event_counter = 1

    gateway_types = {
        "EXCLUSIVE_GATEWAY",
        "PARALLEL_GATEWAY",
        "INCLUSIVE_GATEWAY",
        "COMPLEX_GATEWAY",
        "EVENT_GATEWAY",
    }

    for node in nodes:
        if node.get("id"):
            node_ids.append(node["id"])
        else:
            node_type = node.get("type", "USER_TASK").upper()
            if node_type == "USER_TASK":
                node_ids.append(f"Task_{task_counter}")
                task_counter += 1
            elif node_type in gateway_types:
                node_ids.append(f"Gateway_{gw_counter}")
                gw_counter += 1
            elif node_type == "SUB_PROCESS":
                node_ids.append(f"SubProcess_{gw_counter}")
                gw_counter += 1
            elif node_type == "DATA_OBJECT":
                node_ids.append(f"DataObject_{event_counter}")
                event_counter += 1
            elif node_type == "DATA_STORE":
                node_ids.append(f"DataStore_{event_counter}")
                event_counter += 1
            elif node_type == "PARTICIPANT":
                node_ids.append(f"Participant_{event_counter}")
                event_counter += 1
            elif node_type == "GROUP":
                node_ids.append(f"Group_{event_counter}")
                event_counter += 1
            else:
                node_ids.append(f"Event_{event_counter}")
                event_counter += 1

    return node_ids


def _create_node_elements(
    process: etree._Element,
    ns: dict[str, str],
    nodes: list[dict],
    node_ids: list[str],
    flowable_ns: str,
) -> None:
    """创建所有节点元素"""
    bpmn = ns["bpmn2"]
    fl = flowable_ns

    for i, node in enumerate(nodes):
        node_type = node.get("type", "USER_TASK").upper()
        node_id = node_ids[i]
        node_name = node.get("name", "")

        if node_type == "USER_TASK":
            attrs = {"id": node_id}
            if node_name:
                attrs["name"] = node_name
            # Flowable 扩展属性
            if node.get("form_key"):
                form_key = node["form_key"]
                # 统一格式：前端 ElementForm 使用 key_{id}，LLM 可能返回纯 id
                if not form_key.startswith("key_"):
                    form_key = f"key_{form_key}"
                attrs[f"{{{fl}}}formKey"] = form_key
            if node.get("assignee"):
                attrs[f"{{{fl}}}assignee"] = node["assignee"]
            if node.get("candidate_groups"):
                # 转为逗号分隔的字符串
                groups = node["candidate_groups"]
                attrs[f"{{{fl}}}candidateGroups"] = (
                    ",".join(groups) if isinstance(groups, list) else str(groups)
                )
            if node.get("text"):
                attrs[f"{{{fl}}}text"] = node["text"]
            if node.get("candidate_users"):
                users = node["candidate_users"]
                attrs[f"{{{fl}}}candidateUsers"] = (
                    ",".join(users) if isinstance(users, list) else str(users)
                )
            if node.get("data_type"):
                attrs[f"{{{fl}}}dataType"] = node["data_type"]

            etree.SubElement(process, f"{{{bpmn}}}userTask", **attrs)

        elif node_type == "EXCLUSIVE_GATEWAY":
            attrs = {"id": node_id}
            if node_name:
                attrs["name"] = node_name
            etree.SubElement(process, f"{{{bpmn}}}exclusiveGateway", **attrs)

        elif node_type == "PARALLEL_GATEWAY":
            attrs = {"id": node_id}
            if node_name:
                attrs["name"] = node_name
            etree.SubElement(process, f"{{{bpmn}}}parallelGateway", **attrs)

        elif node_type == "INCLUSIVE_GATEWAY":
            attrs = {"id": node_id}
            if node_name:
                attrs["name"] = node_name
            etree.SubElement(process, f"{{{bpmn}}}inclusiveGateway", **attrs)

        elif node_type == "COMPLEX_GATEWAY":
            attrs = {"id": node_id}
            if node_name:
                attrs["name"] = node_name
            etree.SubElement(process, f"{{{bpmn}}}complexGateway", **attrs)

        elif node_type == "EVENT_GATEWAY":
            attrs = {"id": node_id}
            if node_name:
                attrs["name"] = node_name
            etree.SubElement(process, f"{{{bpmn}}}eventBasedGateway", **attrs)

        elif node_type == "INTERMEDIATE_THROW_EVENT":
            attrs = {"id": node_id}
            if node_name:
                attrs["name"] = node_name
            etree.SubElement(process, f"{{{bpmn}}}intermediateThrowEvent", **attrs)

        elif node_type == "SUB_PROCESS":
            attrs = {"id": node_id}
            if node_name:
                attrs["name"] = node_name
            sub = etree.SubElement(process, f"{{{bpmn}}}subProcess", **attrs)
            for sub_node in node.get("sub_nodes", []):
                sub_node_type = sub_node.get("type", "USER_TASK").upper()
                sub_node_id = sub_node.get("id", "")
                sub_attrs = {"id": sub_node_id}
                if sub_node.get("name"):
                    sub_attrs["name"] = sub_node["name"]
                if sub_node_type == "USER_TASK":
                    etree.SubElement(sub, f"{{{bpmn}}}userTask", **sub_attrs)
                elif sub_node_type == "START_EVENT":
                    etree.SubElement(sub, f"{{{bpmn}}}startEvent", **sub_attrs)
                elif sub_node_type == "END_EVENT":
                    etree.SubElement(sub, f"{{{bpmn}}}endEvent", **sub_attrs)

        elif node_type == "DATA_OBJECT":
            attrs = {"id": node_id}
            if node_name:
                attrs["name"] = node_name
            etree.SubElement(process, f"{{{bpmn}}}dataObject", **attrs)

        elif node_type == "DATA_STORE":
            attrs = {"id": node_id}
            if node_name:
                attrs["name"] = node_name
            etree.SubElement(process, f"{{{bpmn}}}dataStoreReference", **attrs)

        elif node_type == "PARTICIPANT":
            attrs = {"id": node_id}
            if node_name:
                attrs["name"] = node_name
            etree.SubElement(process, f"{{{bpmn}}}participant", **attrs)

        elif node_type == "GROUP":
            attrs = {"id": node_id}
            if node_name:
                attrs["name"] = node_name
            etree.SubElement(process, f"{{{bpmn}}}group", **attrs)


def _create_auto_edges(
    process: etree._Element,
    ns: dict[str, str],
    nodes: list[dict],
    node_ids: list[str],
) -> None:
    """自动生成线性连线：Start -> Node1 -> Node2 -> ... -> End"""
    bpmn = ns["bpmn2"]
    start_id = "StartEvent_1"
    end_id = "EndEvent_1"
    flowable_ns = "http://flowable.org/bpmn"

    # 从 nodes 中查找 START_EVENT 节点获取 form_key
    start_form_key = ""
    for node in nodes:
        if node.get("type", "").upper() == "START_EVENT" and node.get("form_key"):
            start_form_key = node["form_key"]
            break

    # 创建开始事件
    start_attrs = {"id": start_id, "name": "开始"}
    if start_form_key:
        # 统一格式：前端 ElementForm 使用 key_{id}
        if not start_form_key.startswith("key_"):
            start_form_key = f"key_{start_form_key}"
        start_attrs[f"{{{flowable_ns}}}formKey"] = start_form_key
    start_event = etree.SubElement(process, f"{{{bpmn}}}startEvent", **start_attrs)
    if nodes:
        etree.SubElement(start_event, f"{{{bpmn}}}outgoing").text = "Flow_1"
    else:
        etree.SubElement(start_event, f"{{{bpmn}}}outgoing").text = "Flow_End"

    # 创建结束事件
    end_event = etree.SubElement(process, f"{{{bpmn}}}endEvent", id=end_id, name="结束")
    etree.SubElement(end_event, f"{{{bpmn}}}incoming").text = "Flow_End"

    if not nodes:
        etree.SubElement(
            process,
            f"{{{bpmn}}}sequenceFlow",
            id="Flow_End",
            sourceRef=start_id,
            targetRef=end_id,
        )
        return

    # 为每个节点添加 incoming/outgoing
    for i, node_id in enumerate(node_ids):
        node_elem = process.find(f".//*[@id='{node_id}']")
        if node_elem is None:
            continue
        etree.SubElement(node_elem, f"{{{bpmn}}}incoming").text = (
            "Flow_1" if i == 0 else f"Flow_{i + 1}"
        )
        etree.SubElement(node_elem, f"{{{bpmn}}}outgoing").text = (
            "Flow_End" if i == len(node_ids) - 1 else f"Flow_{i + 2}"
        )

    # 开始 -> 第一个节点
    etree.SubElement(
        process,
        f"{{{bpmn}}}sequenceFlow",
        id="Flow_1",
        sourceRef=start_id,
        targetRef=node_ids[0],
    )

    # 节点之间
    for i in range(len(node_ids) - 1):
        etree.SubElement(
            process,
            f"{{{bpmn}}}sequenceFlow",
            id=f"Flow_{i + 2}",
            sourceRef=node_ids[i],
            targetRef=node_ids[i + 1],
        )

    # 最后一个节点 -> 结束
    etree.SubElement(
        process,
        f"{{{bpmn}}}sequenceFlow",
        id="Flow_End",
        sourceRef=node_ids[-1],
        targetRef=end_id,
    )


def _create_custom_edges(
    process: etree._Element,
    ns: dict[str, str],
    edges: list[dict],
    node_ids: list[str],
    nodes: list[dict] | None = None,
) -> None:
    """根据自定义 edges 创建连线"""
    bpmn = ns["bpmn2"]
    start_id = "StartEvent_1"
    end_id = "EndEvent_1"
    flowable_ns = "http://flowable.org/bpmn"

    # 从 nodes 中查找 START_EVENT 节点获取 form_key
    start_form_key = ""
    if nodes:
        for node in nodes:
            if node.get("type", "").upper() == "START_EVENT" and node.get("form_key"):
                start_form_key = node["form_key"]
                break

    # 创建开始事件
    start_attrs = {"id": start_id, "name": "开始"}
    if start_form_key:
        # 统一格式：前端 ElementForm 使用 key_{id}
        if not start_form_key.startswith("key_"):
            start_form_key = f"key_{start_form_key}"
        start_attrs[f"{{{flowable_ns}}}formKey"] = start_form_key
    etree.SubElement(process, f"{{{bpmn}}}startEvent", **start_attrs)
    # 创建结束事件
    etree.SubElement(process, f"{{{bpmn}}}endEvent", id=end_id, name="结束")

    # 构建节点类型映射，用于识别 START_EVENT 和 END_EVENT 节点
    node_type_map = {}
    if nodes:
        for node in nodes:
            node_id = node.get("id", "")
            node_type = node.get("type", "").upper()
            if node_id:
                node_type_map[node_id] = node_type

    # 收集每个节点的 incoming/outgoing
    incoming_map: dict[str, list[str]] = {}
    outgoing_map: dict[str, list[str]] = {}

    for i, edge in enumerate(edges):
        flow_id = edge.get("id") or f"Flow_{i + 1}"
        source = edge["source"]
        target = edge["target"]

        # 解析实际的 source/target ID
        # 处理 "start" 特殊值或 START_EVENT 节点 id
        if source == "start" or node_type_map.get(source) == "START_EVENT":
            source_id = start_id
        else:
            source_id = source

        # 处理 "end" 特殊值或 END_EVENT 节点 id
        if target == "end" or node_type_map.get(target) == "END_EVENT":
            target_id = end_id
        else:
            target_id = target

        outgoing_map.setdefault(source_id, []).append(flow_id)
        incoming_map.setdefault(target_id, []).append(flow_id)

        # 创建 sequenceFlow
        flow_attrs = {"id": flow_id, "sourceRef": source_id, "targetRef": target_id}
        if edge.get("name"):
            flow_attrs["name"] = edge["name"]
        if edge.get("is_default"):
            source_element = process.find(f".//*[@id='{source_id}']")
            if source_element is not None:
                source_element.set("default", flow_id)
        if edge.get("condition"):
            condition_expr = etree.SubElement(
                process, f"{{{bpmn}}}sequenceFlow", **flow_attrs
            )
            condition_elem = etree.SubElement(
                condition_expr, f"{{{bpmn}}}conditionExpression"
            )
            condition_elem.text = _compile_condition(edge["condition"])
            condition_elem.set(
                "{http://www.w3.org/2001/XMLSchema-instance}type",
                "bpmn2:tFormalExpression",
            )
        else:
            etree.SubElement(process, f"{{{bpmn}}}sequenceFlow", **flow_attrs)

    # 为每个节点添加 incoming/outgoing 元素
    for elem_id, flow_ids in incoming_map.items():
        elem = process.find(f".//*[@id='{elem_id}']")
        if elem is not None:
            for fid in flow_ids:
                etree.SubElement(elem, f"{{{bpmn}}}incoming").text = fid

    for elem_id, flow_ids in outgoing_map.items():
        elem = process.find(f".//*[@id='{elem_id}']")
        if elem is not None:
            for fid in flow_ids:
                etree.SubElement(elem, f"{{{bpmn}}}outgoing").text = fid


def _compile_condition(condition: dict | str) -> str:
    """Compile a typed condition to a Flowable expression; keep legacy strings."""
    if isinstance(condition, str):
        return condition
    field = str(condition.get("field", ""))
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", field):
        raise ValueError(f"非法条件字段: {field}")
    operator = condition.get("operator")
    symbols = {
        "eq": "==",
        "ne": "!=",
        "gt": ">",
        "ge": ">=",
        "lt": "<",
        "le": "<=",
    }
    if operator not in symbols:
        raise ValueError(f"暂不支持的条件操作符: {operator}")
    value = json.dumps(condition.get("value"), ensure_ascii=False)
    return f"${{{field} {symbols[operator]} {value}}}"


def _create_layered_bpmn_diagram(
    definitions: etree._Element,
    ns: dict[str, str],
    process_id: str,
    nodes: list[dict],
    node_ids: list[str],
    custom_edges: list[dict],
) -> None:
    """Create a deterministic left-to-right diagram with separated branches."""
    bpmndi, dc, di = ns["bpmndi"], ns["dc"], ns["di"]
    diagram = etree.SubElement(
        definitions, f"{{{bpmndi}}}BPMNDiagram", id="BPMNDiagram_1"
    )
    plane = etree.SubElement(
        diagram, f"{{{bpmndi}}}BPMNPlane", id="BPMNPlane_1", bpmnElement=process_id
    )

    canonical = _canonical_node_ids(nodes, node_ids)
    normalized_edges = _normalize_di_edges(nodes, node_ids, custom_edges, canonical)
    bounds = _calculate_di_bounds(nodes, node_ids, normalized_edges, canonical)
    _append_di_shapes(plane, bpmndi, dc, bounds)
    _append_di_edges(plane, bpmndi, di, normalized_edges, bounds)


def _normalize_di_edges(
    nodes: list[dict],
    node_ids: list[str],
    custom_edges: list[dict],
    canonical: dict[str, str],
) -> list[dict]:
    edges = custom_edges or _build_auto_edges_list(nodes, node_ids)
    return [
        {
            **edge,
            "source": canonical.get(edge["source"], edge["source"]),
            "target": canonical.get(edge["target"], edge["target"]),
        }
        for edge in edges
    ]


def _calculate_di_bounds(
    nodes: list[dict],
    node_ids: list[str],
    edges: list[dict],
    canonical: dict[str, str],
) -> dict[str, Bounds]:
    levels = _calculate_levels(edges)
    drawable_ids = [
        canonical[node_id]
        for node, node_id in zip(nodes, node_ids, strict=False)
        if node.get("type", "").upper() not in {"START_EVENT", "END_EVENT"}
    ]
    for index, node_id in enumerate(drawable_ids, start=1):
        levels.setdefault(node_id, index)
    levels["StartEvent_1"] = 0
    levels["EndEvent_1"] = (
        max([levels.get(node_id, 0) for node_id in drawable_ids] or [0]) + 1
    )

    ids_by_level = _group_ids_by_level(drawable_ids, levels)
    bounds: dict[str, Bounds] = {
        "StartEvent_1": (180, 222, 36, 36),
        "EndEvent_1": (180 + levels["EndEvent_1"] * 220, 222, 36, 36),
    }
    node_by_canonical = {
        canonical[node_id]: node
        for node, node_id in zip(nodes, node_ids, strict=False)
        if canonical[node_id] not in {"StartEvent_1", "EndEvent_1"}
    }
    for level, level_ids in ids_by_level.items():
        for row, node_id in enumerate(level_ids):
            node = node_by_canonical[node_id]
            node_type = node.get("type", "USER_TASK").upper()
            width, height = (50, 50) if "GATEWAY" in node_type else (100, 80)
            y = 220 + (row - (len(level_ids) - 1) / 2) * 150
            bounds[node_id] = (180 + level * 220, y, width, height)
    return bounds


def _group_ids_by_level(
    node_ids: list[str], levels: dict[str, int]
) -> dict[int, list[str]]:
    grouped: dict[int, list[str]] = {}
    for node_id in node_ids:
        grouped.setdefault(levels[node_id], []).append(node_id)
    return grouped


def _append_di_shapes(
    plane: etree._Element,
    bpmndi: str,
    dc: str,
    bounds: dict[str, Bounds],
) -> None:
    for node_id, (x, y, width, height) in bounds.items():
        shape = etree.SubElement(
            plane,
            f"{{{bpmndi}}}BPMNShape",
            id=f"{node_id}_di",
            bpmnElement=node_id,
        )
        etree.SubElement(
            shape,
            f"{{{dc}}}Bounds",
            x=str(x),
            y=str(y),
            width=str(width),
            height=str(height),
        )


def _append_di_edges(
    plane: etree._Element,
    bpmndi: str,
    di: str,
    edges: list[dict],
    bounds: dict[str, Bounds],
) -> None:
    for index, edge in enumerate(edges, start=1):
        flow_id = edge.get("id") or edge.get("flow_id") or f"Flow_{index}"
        source_bounds = bounds.get(edge["source"])
        target_bounds = bounds.get(edge["target"])
        if not source_bounds or not target_bounds:
            continue
        waypoints = _edge_waypoints(source_bounds, target_bounds)
        bpmn_edge = etree.SubElement(
            plane,
            f"{{{bpmndi}}}BPMNEdge",
            id=f"{flow_id}_di",
            bpmnElement=flow_id,
        )
        for x, y in waypoints:
            etree.SubElement(bpmn_edge, f"{{{di}}}waypoint", x=str(x), y=str(y))


def _edge_waypoints(
    source_bounds: Bounds, target_bounds: Bounds
) -> list[tuple[float, float]]:
    source = (
        source_bounds[0] + source_bounds[2],
        source_bounds[1] + source_bounds[3] / 2,
    )
    target = (target_bounds[0], target_bounds[1] + target_bounds[3] / 2)
    if source[1] == target[1]:
        return [source, target]
    middle_x = (source[0] + target[0]) / 2
    return [source, (middle_x, source[1]), (middle_x, target[1]), target]


def _canonical_node_ids(nodes: list[dict], node_ids: list[str]) -> dict[str, str]:
    canonical = {"start": "StartEvent_1", "end": "EndEvent_1"}
    for node, node_id in zip(nodes, node_ids, strict=False):
        node_type = node.get("type", "").upper()
        if node_type == "START_EVENT":
            canonical[node_id] = "StartEvent_1"
        elif node_type == "END_EVENT":
            canonical[node_id] = "EndEvent_1"
        else:
            canonical[node_id] = node_id
    return canonical


def _calculate_levels(edges: list[dict]) -> dict[str, int]:
    adjacency: dict[str, list[str]] = {}
    for edge in edges:
        adjacency.setdefault(edge["source"], []).append(edge["target"])
    levels = {"StartEvent_1": 0}
    queue = ["StartEvent_1"]
    while queue:
        source = queue.pop(0)
        for target in adjacency.get(source, []):
            if target not in levels:
                levels[target] = levels[source] + 1
                queue.append(target)
    return levels


def _build_auto_edges_list(nodes: list[dict], node_ids: list[str]) -> list[dict]:
    """构建自动生成的边列表（flow_id 与 _create_auto_edges 保持一致）"""
    edges = []
    if nodes:
        edges.append({"flow_id": "Flow_1", "source": "start", "target": node_ids[0]})
        for i in range(len(node_ids) - 1):
            edges.append(
                {
                    "flow_id": f"Flow_{i + 2}",
                    "source": node_ids[i],
                    "target": node_ids[i + 1],
                }
            )
        edges.append({"flow_id": "Flow_End", "source": node_ids[-1], "target": "end"})
    else:
        edges.append({"flow_id": "Flow_End", "source": "start", "target": "end"})
    return edges
