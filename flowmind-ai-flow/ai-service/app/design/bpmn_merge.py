"""Preserve existing BPMN metadata while materializing AI graph operations."""

from copy import deepcopy

import lxml.etree as etree

from app.design.bpmn_parser import OPAQUE_BPMN_NODE_TYPES

_MANAGED_ATTRIBUTES = {
    "id",
    "name",
    "sourceRef",
    "targetRef",
    "default",
    "formKey",
    "assignee",
    "candidateGroups",
    "candidateUsers",
    "dataType",
    "text",
}
_MANAGED_CHILDREN = {"incoming", "outgoing", "conditionExpression"}
_MANAGED_FLOW_ELEMENTS = {
    "startEvent",
    "endEvent",
    "userTask",
    "exclusiveGateway",
    "parallelGateway",
    "inclusiveGateway",
    "complexGateway",
    "eventBasedGateway",
    "intermediateThrowEvent",
}


def preserve_bpmn_metadata(original_xml: str, generated_xml: str) -> str:
    """Merge unmanaged elements, attributes and existing diagram positions.

    The generated document remains authoritative for the flat graph fields that
    AI is allowed to edit. Everything outside that contract is copied from the
    original BPMN document so an incremental edit cannot silently erase it.
    """
    original = etree.fromstring(original_xml.encode("utf-8"))
    generated = etree.fromstring(generated_xml.encode("utf-8"))
    original_process = _first_by_localname(original, "process")
    generated_process = _first_by_localname(generated, "process")
    if original_process is None or generated_process is None:
        raise ValueError("BPMN XML 缺少 process 元素")

    _restore_boundary_ids(original_process, generated)
    _copy_unmanaged_attributes(original, generated)
    _copy_unmanaged_attributes(original_process, generated_process)
    _merge_process_elements(original_process, generated_process)
    _copy_definition_extensions(original, generated)
    _preserve_existing_diagram(original, generated)
    return etree.tostring(
        generated, encoding="utf-8", xml_declaration=True, pretty_print=True
    ).decode("utf-8")


def _merge_process_elements(
    original_process: etree._Element, generated_process: etree._Element
) -> None:
    generated_elements = _elements_by_id(generated_process)
    for source in original_process:
        _merge_process_element(source, generated_process, generated_elements)


def _merge_process_element(
    source: etree._Element,
    process: etree._Element,
    generated_elements: dict[str, etree._Element],
) -> None:
    element_id = source.get("id")
    if not element_id:
        identities = {_child_identity(child) for child in process}
        if _child_identity(source) not in identities:
            process.append(deepcopy(source))
        return
    target = generated_elements.get(element_id)
    if target is None:
        localname = _localname(source)
        managed_edge = localname == "sequenceFlow" and _edge_is_managed(
            source, generated_elements
        )
        if localname not in _MANAGED_FLOW_ELEMENTS and not managed_edge:
            process.append(deepcopy(source))
        return
    if _localname(source) in OPAQUE_BPMN_NODE_TYPES:
        replacement = _restore_opaque_element(source, target)
        target.getparent().replace(target, replacement)
        generated_elements[element_id] = replacement
        return
    _copy_unmanaged_attributes(source, target)
    _copy_unmanaged_children(source, target)


def _restore_opaque_element(
    source: etree._Element, generated: etree._Element
) -> etree._Element:
    """Keep the original tag/extensions but use generated graph references."""
    replacement = deepcopy(source)
    for key in list(replacement.attrib):
        if etree.QName(key).localname in _MANAGED_ATTRIBUTES:
            del replacement.attrib[key]
    for key, value in generated.attrib.items():
        if etree.QName(key).localname in _MANAGED_ATTRIBUTES:
            replacement.set(key, value)
    for child in list(replacement):
        if _localname(child) in _MANAGED_CHILDREN:
            replacement.remove(child)
    for child in generated:
        if _localname(child) in _MANAGED_CHILDREN:
            replacement.append(deepcopy(child))
    return replacement


def _copy_unmanaged_children(source: etree._Element, target: etree._Element) -> None:
    existing_children = {_child_identity(child) for child in target}
    for child in source:
        if _localname(child) in _MANAGED_CHILDREN:
            continue
        identity = _child_identity(child)
        if identity not in existing_children:
            target.append(deepcopy(child))
            existing_children.add(identity)


def _copy_unmanaged_attributes(source: etree._Element, target: etree._Element) -> None:
    for key, value in source.attrib.items():
        if (
            etree.QName(key).localname not in _MANAGED_ATTRIBUTES
            and key not in target.attrib
        ):
            target.set(key, value)


def _restore_boundary_ids(
    original_process: etree._Element, generated: etree._Element
) -> None:
    """Keep custom start/end IDs and update every generated reference."""
    generated_process = _first_by_localname(generated, "process")
    if generated_process is None:
        return
    for localname in ("startEvent", "endEvent"):
        original_items = [
            item for item in original_process if _localname(item) == localname
        ]
        generated_items = [
            item for item in generated_process if _localname(item) == localname
        ]
        if len(original_items) != 1 or len(generated_items) != 1:
            continue
        original_id = original_items[0].get("id")
        generated_id = generated_items[0].get("id")
        if not original_id or not generated_id or original_id == generated_id:
            continue
        generated_items[0].set("id", original_id)
        for element in generated.iter():
            for attribute in ("sourceRef", "targetRef", "bpmnElement"):
                if element.get(attribute) == generated_id:
                    element.set(attribute, original_id)


def _copy_definition_extensions(
    original: etree._Element, generated: etree._Element
) -> None:
    generated_ids = _elements_by_id(generated)
    for child in original:
        if _localname(child) in {"process", "BPMNDiagram"}:
            continue
        element_id = child.get("id")
        if element_id and element_id in generated_ids:
            continue
        generated.append(deepcopy(child))


def _preserve_existing_diagram(
    original: etree._Element, generated: etree._Element
) -> None:
    original_plane = _first_by_localname(original, "BPMNPlane")
    generated_plane = _first_by_localname(generated, "BPMNPlane")
    if original_plane is None or generated_plane is None:
        return
    generated_di = _diagram_elements_by_business_id(generated_plane)
    original_elements = _elements_by_id(original)
    generated_elements = _elements_by_id(generated)
    preserved_business_ids: set[str] = set()
    business_ids = set(_elements_by_id(generated))
    for source in original_plane:
        business_id = source.get("bpmnElement")
        if not business_id:
            continue
        target = generated_di.get(business_id)
        if target is None:
            if business_id in business_ids:
                generated_plane.append(deepcopy(source))
            continue
        if _localname(source) == "BPMNEdge" and not _same_edge_endpoints(
            original_elements.get(business_id), generated_elements.get(business_id)
        ):
            continue
        target.getparent().replace(target, deepcopy(source))
        preserved_business_ids.add(business_id)
    _align_new_edge_endpoints(generated, generated_plane, preserved_business_ids)


def _diagram_elements_by_business_id(
    plane: etree._Element,
) -> dict[str, etree._Element]:
    return {
        business_id: child
        for child in plane
        if (business_id := child.get("bpmnElement"))
    }


def _same_edge_endpoints(
    original: etree._Element | None, generated: etree._Element | None
) -> bool:
    if original is None or generated is None:
        return False
    return all(
        original.get(attribute) == generated.get(attribute)
        for attribute in ("sourceRef", "targetRef")
    )


def _elements_by_id(root: etree._Element) -> dict[str, etree._Element]:
    return {
        element_id: element
        for element in root.iter()
        if (element_id := element.get("id"))
    }


def _first_by_localname(root: etree._Element, localname: str) -> etree._Element | None:
    return next((item for item in root.iter() if _localname(item) == localname), None)


def _localname(element: etree._Element) -> str:
    return etree.QName(element.tag).localname


def _child_identity(element: etree._Element) -> tuple[str, str | None]:
    return _localname(element), element.get("id")


def _edge_is_managed(
    edge: etree._Element, generated_elements: dict[str, etree._Element]
) -> bool:
    return all(
        endpoint in generated_elements
        for endpoint in (edge.get("sourceRef"), edge.get("targetRef"))
    )


def _align_new_edge_endpoints(
    root: etree._Element,
    plane: etree._Element,
    preserved_business_ids: set[str],
) -> None:
    business_elements = _elements_by_id(root)
    shapes = {
        child.get("bpmnElement"): _first_by_localname(child, "Bounds")
        for child in plane
        if _localname(child) == "BPMNShape"
    }
    for diagram_edge in plane:
        flow_id = diagram_edge.get("bpmnElement")
        if _localname(diagram_edge) != "BPMNEdge" or flow_id in preserved_business_ids:
            continue
        flow = business_elements.get(flow_id or "")
        if flow is None:
            continue
        source = shapes.get(flow.get("sourceRef"))
        target = shapes.get(flow.get("targetRef"))
        waypoints = [child for child in diagram_edge if _localname(child) == "waypoint"]
        if source is None or target is None or len(waypoints) < 2:
            continue
        source_x, source_y = _right_center(source)
        target_x, target_y = _left_center(target)
        waypoints[0].set("x", str(source_x))
        waypoints[0].set("y", str(source_y))
        waypoints[-1].set("x", str(target_x))
        waypoints[-1].set("y", str(target_y))


def _right_center(bounds: etree._Element) -> tuple[float, float]:
    return (
        float(bounds.get("x", 0)) + float(bounds.get("width", 0)),
        float(bounds.get("y", 0)) + float(bounds.get("height", 0)) / 2,
    )


def _left_center(bounds: etree._Element) -> tuple[float, float]:
    return (
        float(bounds.get("x", 0)),
        float(bounds.get("y", 0)) + float(bounds.get("height", 0)) / 2,
    )
