"""
FlowMind 智能流程设计服务 - BPMN 反解析器测试
"""

import lxml.etree as etree

from app.design.bpmn_generator import generate_bpmn_xml
from app.design.bpmn_merge import preserve_bpmn_metadata
from app.design.bpmn_parser import enrich_flow_baseline, parse_bpmn_to_flat
from app.design.operations import apply_design_operations

BPMN_XML = """<?xml version='1.0' encoding='utf-8'?>
<bpmn2:definitions xmlns:bpmn2="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:flowable="http://flowable.org/bpmn"
    id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn2:process id="Process_leave" name="请假流程" isExecutable="true">
    <bpmn2:startEvent id="StartEvent_1" name="开始">
      <bpmn2:outgoing>Flow_1</bpmn2:outgoing>
    </bpmn2:startEvent>
    <bpmn2:userTask id="Task_1" name="提交申请" flowable:formKey="key_leave" flowable:assignee="张三" flowable:candidateGroups="hr,manager">
      <bpmn2:incoming>Flow_1</bpmn2:incoming>
      <bpmn2:outgoing>Flow_2</bpmn2:outgoing>
    </bpmn2:userTask>
    <bpmn2:exclusiveGateway id="Gateway_1" name="金额判断">
      <bpmn2:incoming>Flow_2</bpmn2:incoming>
      <bpmn2:outgoing>Flow_3</bpmn2:outgoing>
      <bpmn2:outgoing>Flow_4</bpmn2:outgoing>
    </bpmn2:exclusiveGateway>
    <bpmn2:userTask id="Task_2" name="总监审批" flowable:assignee="李四">
      <bpmn2:incoming>Flow_3</bpmn2:incoming>
      <bpmn2:outgoing>Flow_5</bpmn2:outgoing>
    </bpmn2:userTask>
    <bpmn2:endEvent id="EndEvent_1" name="结束">
      <bpmn2:incoming>Flow_4</bpmn2:incoming>
      <bpmn2:incoming>Flow_5</bpmn2:incoming>
    </bpmn2:endEvent>
    <bpmn2:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_1" />
    <bpmn2:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="Gateway_1" />
    <bpmn2:sequenceFlow id="Flow_3" sourceRef="Gateway_1" targetRef="Task_2">
      <bpmn2:conditionExpression xsi:type="bpmn2:tFormalExpression"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">金额&gt;10000</bpmn2:conditionExpression>
    </bpmn2:sequenceFlow>
    <bpmn2:sequenceFlow id="Flow_4" sourceRef="Gateway_1" targetRef="EndEvent_1" />
    <bpmn2:sequenceFlow id="Flow_5" sourceRef="Task_2" targetRef="EndEvent_1" />
  </bpmn2:process>
</bpmn2:definitions>
"""


def test_parse_nodes_and_edges():
    flat = parse_bpmn_to_flat(BPMN_XML)
    assert flat is not None

    nodes = flat["nodes"]
    edges = flat["edges"]

    node_map = {n["id"]: n for n in nodes}
    assert node_map["StartEvent_1"]["type"] == "START_EVENT"
    assert node_map["Task_1"]["type"] == "USER_TASK"
    assert node_map["Task_1"]["form_key"] == "key_leave"
    assert node_map["Task_1"]["assignee"] == "张三"
    assert node_map["Task_1"]["candidate_groups"] == ["hr", "manager"]
    assert node_map["Gateway_1"]["type"] == "EXCLUSIVE_GATEWAY"
    assert node_map["EndEvent_1"]["type"] == "END_EVENT"

    # 条件连线被保留
    conditioned = [e for e in edges if e.get("condition")]
    assert len(conditioned) == 1
    assert conditioned[0]["id"] == "Flow_3"
    assert conditioned[0]["source"] == "Gateway_1"
    assert conditioned[0]["target"] == "Task_2"
    assert conditioned[0]["condition"] == "金额>10000"


def test_parse_invalid_xml_returns_none():
    assert parse_bpmn_to_flat("not xml") is None
    assert parse_bpmn_to_flat("") is None
    assert parse_bpmn_to_flat(None) is None


def test_roundtrip_generated_xml():
    """正向生成后反解析，节点数与连线数应一致。"""
    nodes = [
        {"type": "USER_TASK", "id": "Task_1", "name": "提交申请", "assignee": "张三"},
        {"type": "EXCLUSIVE_GATEWAY", "id": "Gateway_1", "name": "判断"},
        {"type": "USER_TASK", "id": "Task_2", "name": "审批"},
    ]
    edges = [
        {"source": "start", "target": "Task_1"},
        {"source": "Task_1", "target": "Gateway_1"},
        {"source": "Gateway_1", "target": "Task_2", "condition": "金额>10000"},
        {"source": "Task_2", "target": "end"},
    ]
    xml = generate_bpmn_xml({"nodes": nodes, "edges": edges}, {"code": "leave"})
    flat = parse_bpmn_to_flat(xml)
    assert flat is not None
    # 生成器会额外加入 start/end 两个事件节点
    assert len(flat["nodes"]) == 5
    assert len(flat["edges"]) == 4


def test_enrich_flow_baseline():
    # 只有 bpmnXml -> 补齐 nodes/edges
    data = {"modelId": "1", "bpmnXml": BPMN_XML}
    enriched = enrich_flow_baseline(data)
    assert enriched["nodes"]
    assert enriched["edges"]
    assert enriched["modelId"] == "1"

    # 已有 nodes -> 幂等返回原对象
    existing = {"nodes": [{"id": "Task_1"}], "bpmnXml": BPMN_XML}
    assert enrich_flow_baseline(existing) is existing

    # 无 XML -> 原样返回
    assert enrich_flow_baseline({"modelId": "1"}) == {"modelId": "1"}
    assert enrich_flow_baseline(None) == {}


def test_incremental_bpmn_merge_preserves_extensions_and_existing_layout():
    flat = parse_bpmn_to_flat(BPMN_XML)
    original = etree.fromstring(generate_bpmn_xml(flat, {"code": "leave"}).encode())
    task = next(item for item in original.iter() if item.get("id") == "Task_1")
    task.set("{http://flowable.org/bpmn}customFlag", "keep-me")
    extension = etree.SubElement(
        task, "{http://www.omg.org/spec/BPMN/20100524/MODEL}extensionElements"
    )
    etree.SubElement(
        extension, "{http://flowable.org/bpmn}taskListener", event="create"
    )
    service = etree.SubElement(
        next(
            item for item in original.iter() if etree.QName(item).localname == "process"
        ),
        "{http://www.omg.org/spec/BPMN/20100524/MODEL}serviceTask",
        id="Service_Keep",
        name="保留服务任务",
    )
    assert service is not None
    shape = next(
        item for item in original.iter() if item.get("bpmnElement") == "Task_1"
    )
    bounds = next(item for item in shape if etree.QName(item).localname == "Bounds")
    bounds.set("x", "999")

    flat["nodes"][1]["name"] = "更新后的任务"
    generated = generate_bpmn_xml(flat, {"code": "leave"})
    merged = preserve_bpmn_metadata(etree.tostring(original).decode(), generated)
    root = etree.fromstring(merged.encode())
    merged_task = next(item for item in root.iter() if item.get("id") == "Task_1")

    assert merged_task.get("name") == "更新后的任务"
    assert merged_task.get("{http://flowable.org/bpmn}customFlag") == "keep-me"
    assert any(
        etree.QName(item).localname == "taskListener" for item in merged_task.iter()
    )
    assert any(item.get("id") == "Service_Keep" for item in root.iter())
    merged_shape = next(
        item for item in root.iter() if item.get("bpmnElement") == "Task_1"
    )
    merged_bounds = next(
        item for item in merged_shape if etree.QName(item).localname == "Bounds"
    )
    assert merged_bounds.get("x") == "999"


def test_incremental_bpmn_merge_restores_custom_boundary_ids():
    original = BPMN_XML.replace("StartEvent_1", "Start_Custom").replace(
        "EndEvent_1", "End_Custom"
    )
    flat = parse_bpmn_to_flat(original)
    generated = generate_bpmn_xml(flat, {"code": "leave"})

    merged = preserve_bpmn_metadata(original, generated)
    root = etree.fromstring(merged.encode())
    ids = {item.get("id") for item in root.iter() if item.get("id")}

    assert "Start_Custom" in ids
    assert "End_Custom" in ids
    assert "StartEvent_1" not in ids
    assert "EndEvent_1" not in ids
    assert all(
        item.get("sourceRef") != "StartEvent_1"
        and item.get("targetRef") != "EndEvent_1"
        and item.get("bpmnElement") not in {"StartEvent_1", "EndEvent_1"}
        for item in root.iter()
    )


def test_incremental_bpmn_merge_keeps_connected_unsupported_task():
    original = etree.fromstring(BPMN_XML.encode())
    task = next(item for item in original.iter() if item.get("id") == "Task_1")
    namespace = etree.QName(task).namespace
    task.tag = f"{{{namespace}}}serviceTask"
    original_xml = etree.tostring(original).decode()

    flat = parse_bpmn_to_flat(original_xml)
    assert any(node["id"] == "Task_1" for node in flat["nodes"])
    old_edge = next(edge for edge in flat["edges"] if edge["source"] == "Task_1")
    old_target = old_edge["target"]
    old_id = old_edge.pop("id")
    old_edge["target"] = "Inserted_Task"
    flat["nodes"].append(
        {"id": "Inserted_Task", "name": "新增审批", "type": "USER_TASK"}
    )
    flat["edges"].append(
        {"id": old_id, "source": "Inserted_Task", "target": old_target}
    )
    merged = preserve_bpmn_metadata(
        original_xml, generate_bpmn_xml(flat, {"code": "leave"})
    )
    merged_root = etree.fromstring(merged.encode())
    merged_task = next(
        item for item in merged_root.iter() if item.get("id") == "Task_1"
    )

    assert etree.QName(merged_task).localname == "serviceTask"
    outgoing = next(
        child for child in merged_task if etree.QName(child).localname == "outgoing"
    )
    actual_outgoing = next(
        item.get("id")
        for item in merged_root.iter()
        if etree.QName(item).localname == "sequenceFlow"
        and item.get("sourceRef") == "Task_1"
    )
    assert outgoing.text == actual_outgoing
    assert outgoing.text != old_id
    business_ids = {item.get("id") for item in merged_root.iter() if item.get("id")}
    assert all(
        item.get("sourceRef") in business_ids and item.get("targetRef") in business_ids
        for item in merged_root.iter()
        if etree.QName(item).localname == "sequenceFlow"
    )


def test_subprocess_is_an_opaque_node_instead_of_flattening_its_children():
    original = etree.fromstring(BPMN_XML.encode())
    task = next(item for item in original.iter() if item.get("id") == "Task_1")
    namespace = etree.QName(task).namespace
    task.tag = f"{{{namespace}}}subProcess"
    etree.SubElement(task, f"{{{namespace}}}userTask", id="Inner_Task", name="内部任务")

    flat = parse_bpmn_to_flat(etree.tostring(original).decode())
    node_ids = {node["id"] for node in flat["nodes"]}

    assert "Task_1" in node_ids
    assert "Inner_Task" not in node_ids


def test_changed_edge_id_does_not_restore_stale_waypoints():
    flat = parse_bpmn_to_flat(BPMN_XML)
    original = generate_bpmn_xml(flat, {"code": "leave"})
    updated = apply_design_operations(
        "flow_design",
        flat,
        [
            {
                "op": "add_node",
                "after_id": "Task_1",
                "node": {"id": "Inserted_Task", "name": "新增", "type": "USER_TASK"},
            }
        ],
    )
    root = etree.fromstring(
        preserve_bpmn_metadata(
            original, generate_bpmn_xml(updated, {"code": "leave"})
        ).encode()
    )
    shape = next(
        item for item in root.iter() if item.get("bpmnElement") == "Inserted_Task"
    )
    bounds = next(item for item in shape if etree.QName(item).localname == "Bounds")
    edge = next(item for item in root.iter() if item.get("bpmnElement") == "Flow_2")
    first_waypoint = next(
        item for item in edge if etree.QName(item).localname == "waypoint"
    )

    assert float(first_waypoint.get("x")) == float(bounds.get("x")) + float(
        bounds.get("width")
    )
