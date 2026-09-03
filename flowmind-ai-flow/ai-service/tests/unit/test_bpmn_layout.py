"""BPMN generation semantics and deterministic layout tests."""

from lxml import etree

from app.design.bpmn_generator import generate_bpmn_xml
from app.design.bpmn_validator import validate_bpmn_xml

NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
}


def _branching_xml() -> etree._Element:
    structure = {
        "nodes": [
            {
                "id": "start-source",
                "type": "START_EVENT",
                "name": "开始",
                "form_key": "1",
            },
            {"id": "split", "type": "PARALLEL_GATEWAY", "name": "并行"},
            {
                "id": "manager",
                "type": "USER_TASK",
                "name": "经理",
                "candidate_groups": ["manager"],
            },
            {
                "id": "director",
                "type": "USER_TASK",
                "name": "总监",
                "candidate_groups": ["director"],
            },
            {"id": "join", "type": "PARALLEL_GATEWAY", "name": "汇聚"},
            {"id": "end-source", "type": "END_EVENT", "name": "结束"},
        ],
        "edges": [
            {"id": "to_split", "source": "start-source", "target": "split"},
            {"id": "to_manager", "source": "split", "target": "manager"},
            {"id": "to_director", "source": "split", "target": "director"},
            {"id": "manager_join", "source": "manager", "target": "join"},
            {"id": "director_join", "source": "director", "target": "join"},
            {"id": "to_end", "source": "join", "target": "end-source"},
        ],
    }
    return etree.fromstring(generate_bpmn_xml(structure, {"code": "test"}).encode())


def test_parallel_branches_are_placed_on_separate_rows():
    root = _branching_xml()

    def y(node_id: str) -> float:
        shape = root.xpath(
            f"//bpmndi:BPMNShape[@bpmnElement='{node_id}']/dc:Bounds",
            namespaces=NS,
        )[0]
        return float(shape.get("y"))

    assert y("manager") != y("director")


def test_edge_waypoints_use_canonical_start_shape_and_explicit_edge_id():
    root = _branching_xml()
    start_bounds = root.xpath(
        "//bpmndi:BPMNShape[@bpmnElement='StartEvent_1']/dc:Bounds",
        namespaces=NS,
    )[0]
    waypoint = root.xpath(
        "//bpmndi:BPMNEdge[@bpmnElement='to_split']/di:waypoint[1]",
        namespaces=NS,
    )[0]
    assert float(waypoint.get("x")) == float(start_bounds.get("x")) + float(
        start_bounds.get("width")
    )


def test_exclusive_gateway_default_and_structured_condition_are_emitted():
    structure = {
        "nodes": [
            {"id": "start", "type": "START_EVENT", "name": "开始", "form_key": "1"},
            {"id": "decision", "type": "EXCLUSIVE_GATEWAY", "name": "判断"},
            {
                "id": "approve",
                "type": "USER_TASK",
                "name": "审批",
                "candidate_groups": ["manager"],
            },
            {"id": "end", "type": "END_EVENT", "name": "结束"},
        ],
        "edges": [
            {
                "id": "conditional",
                "source": "decision",
                "target": "approve",
                "condition": {"field": "amount", "operator": "gt", "value": 100},
            },
            {
                "id": "default_path",
                "source": "decision",
                "target": "end",
                "is_default": True,
            },
        ],
    }
    xml = generate_bpmn_xml(structure, {"code": "test"})
    root = etree.fromstring(xml.encode())
    gateway = root.xpath("//bpmn:exclusiveGateway[@id='decision']", namespaces=NS)[0]
    condition = root.xpath(
        "//bpmn:sequenceFlow[@id='conditional']/bpmn:conditionExpression",
        namespaces=NS,
    )[0]
    assert gateway.get("default") == "default_path"
    assert condition.text == "${amount > 100}"
    assert validate_bpmn_xml(xml).is_valid
