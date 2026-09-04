"""
FlowMind 智能审批服务 - BPMN 验证器单元测试

测试 validate_bpmn_xml 函数的各种验证规则，包括结构检查、节点唯一性、
连线引用正确性、网关分支和连通性检查。
"""

from __future__ import annotations

import pytest

from app.utils.bpmn_validator import ValidationError, ValidationResult, validate_bpmn_xml


# ---------------------------------------------------------------------------
# 辅助函数：快速生成 BPMN XML 片段
# ---------------------------------------------------------------------------

def _wrap_bpmn(body: str, process_attrs: str = "") -> str:
    """将 process 内容包装为完整 BPMN definitions XML"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
             xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
             xmlns:omgdc="http://www.omg.org/spec/DD/20100524/DC"
             xmlns:omgdi="http://www.omg.org/spec/DD/20100524/DI"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             targetNamespace="http://www.flowable.org/processdef">
  <process id="TestProcess" isExecutable="true" {process_attrs}>
{body}
  </process>
</definitions>"""


# ---------------------------------------------------------------------------
# 1. test_valid_xml_passes
# ---------------------------------------------------------------------------

class TestValidXml:
    """有效 BPMN XML 应通过验证"""

    def test_valid_xml_passes(self):
        """startEvent -> userTask -> endEvent 应无错误"""
        xml = _wrap_bpmn("""
    <startEvent id="start" />
    <userTask id="task1" />
    <endEvent id="end" />
    <sequenceFlow id="f1" sourceRef="start" targetRef="task1" />
    <sequenceFlow id="f2" sourceRef="task1" targetRef="end" />
""")
        result = validate_bpmn_xml(xml)
        assert result.is_valid is True
        assert len(result.errors) == 0


# ---------------------------------------------------------------------------
# 2. test_missing_start_event (V002)
# ---------------------------------------------------------------------------

class TestMissingStartEvent:
    """缺少 startEvent 应报告 V002 错误"""

    def test_missing_start_event(self):
        xml = _wrap_bpmn("""
    <userTask id="task1" />
    <endEvent id="end" />
    <sequenceFlow id="f1" sourceRef="task1" targetRef="end" />
""")
        result = validate_bpmn_xml(xml)
        assert result.is_valid is False
        v002 = [e for e in result.errors if e.rule_id == "V002"]
        assert len(v002) == 1


# ---------------------------------------------------------------------------
# 3. test_missing_end_event (V003)
# ---------------------------------------------------------------------------

class TestMissingEndEvent:
    """缺少 endEvent 应报告 V003 错误"""

    def test_missing_end_event(self):
        xml = _wrap_bpmn("""
    <startEvent id="start" />
    <userTask id="task1" />
    <sequenceFlow id="f1" sourceRef="start" targetRef="task1" />
""")
        result = validate_bpmn_xml(xml)
        assert result.is_valid is False
        v003 = [e for e in result.errors if e.rule_id == "V003"]
        assert len(v003) == 1


# ---------------------------------------------------------------------------
# 4. test_duplicate_node_ids (V005)
# ---------------------------------------------------------------------------

class TestDuplicateNodeIds:
    """重复节点 ID 应报告 V005 错误"""

    def test_duplicate_node_ids(self):
        xml = _wrap_bpmn("""
    <startEvent id="start" />
    <userTask id="dup" />
    <userTask id="dup" />
    <endEvent id="end" />
    <sequenceFlow id="f1" sourceRef="start" targetRef="dup" />
    <sequenceFlow id="f2" sourceRef="dup" targetRef="end" />
""")
        result = validate_bpmn_xml(xml)
        assert result.is_valid is False
        v005 = [e for e in result.errors if e.rule_id == "V005"]
        assert len(v005) >= 1


# ---------------------------------------------------------------------------
# 5. test_exclusive_gateway_missing_branches (V008)
# ---------------------------------------------------------------------------

class TestExclusiveGatewayMissingBranches:
    """排他网关只有 1 条出线应报告 V008 错误"""

    def test_exclusive_gateway_missing_branches(self):
        xml = _wrap_bpmn("""
    <startEvent id="start" />
    <exclusiveGateway id="gw" />
    <userTask id="task1" />
    <endEvent id="end" />
    <sequenceFlow id="f1" sourceRef="start" targetRef="gw" />
    <sequenceFlow id="f2" sourceRef="gw" targetRef="task1" />
    <sequenceFlow id="f3" sourceRef="task1" targetRef="end" />
""")
        result = validate_bpmn_xml(xml)
        assert result.is_valid is False
        v008 = [e for e in result.errors if e.rule_id == "V008"]
        assert len(v008) >= 1


# ---------------------------------------------------------------------------
# 6. test_exclusive_gateway_missing_condition (V009)
# ---------------------------------------------------------------------------

class TestExclusiveGatewayMissingCondition:
    """排他网关分支缺少 conditionExpression 应报告 V009 错误"""

    def test_exclusive_gateway_missing_condition(self):
        xml = _wrap_bpmn("""
    <startEvent id="start" />
    <exclusiveGateway id="gw" />
    <userTask id="task1" />
    <userTask id="task2" />
    <endEvent id="end" />
    <sequenceFlow id="f1" sourceRef="start" targetRef="gw" />
    <sequenceFlow id="f2" sourceRef="gw" targetRef="task1">
      <conditionExpression xsi:type="tFormalExpression">${'{'}approved == true{'}'}</conditionExpression>
    </sequenceFlow>
    <sequenceFlow id="f3" sourceRef="gw" targetRef="task2" />
    <sequenceFlow id="f4" sourceRef="task1" targetRef="end" />
    <sequenceFlow id="f5" sourceRef="task2" targetRef="end" />
""")
        result = validate_bpmn_xml(xml)
        assert result.is_valid is False
        v009 = [e for e in result.errors if e.rule_id == "V009"]
        assert len(v009) >= 1


# ---------------------------------------------------------------------------
# 7. test_invalid_source_ref (V006)
# ---------------------------------------------------------------------------

class TestInvalidSourceRef:
    """sequenceFlow sourceRef 引用不存在的节点应报告 V006 错误"""

    def test_invalid_source_ref(self):
        xml = _wrap_bpmn("""
    <startEvent id="start" />
    <userTask id="task1" />
    <endEvent id="end" />
    <sequenceFlow id="f1" sourceRef="start" targetRef="task1" />
    <sequenceFlow id="f2" sourceRef="ghost" targetRef="end" />
    <sequenceFlow id="f3" sourceRef="task1" targetRef="end" />
""")
        result = validate_bpmn_xml(xml)
        assert result.is_valid is False
        v006 = [e for e in result.errors if e.rule_id == "V006"]
        assert len(v006) >= 1


# ---------------------------------------------------------------------------
# 8. test_invalid_target_ref (V007)
# ---------------------------------------------------------------------------

class TestInvalidTargetRef:
    """sequenceFlow targetRef 引用不存在的节点应报告 V007 错误"""

    def test_invalid_target_ref(self):
        xml = _wrap_bpmn("""
    <startEvent id="start" />
    <userTask id="task1" />
    <endEvent id="end" />
    <sequenceFlow id="f1" sourceRef="start" targetRef="task1" />
    <sequenceFlow id="f2" sourceRef="task1" targetRef="ghost" />
    <sequenceFlow id="f3" sourceRef="task1" targetRef="end" />
""")
        result = validate_bpmn_xml(xml)
        assert result.is_valid is False
        v007 = [e for e in result.errors if e.rule_id == "V007"]
        assert len(v007) >= 1


# ---------------------------------------------------------------------------
# 9. test_orphan_node_warning (V010/V011)
# ---------------------------------------------------------------------------

class TestOrphanNodeWarning:
    """孤立节点（不可从 startEvent 到达或无法到达 endEvent）应报告警告"""

    def test_orphan_node_warning(self):
        xml = _wrap_bpmn("""
    <startEvent id="start" />
    <userTask id="task1" />
    <userTask id="orphan" />
    <endEvent id="end" />
    <sequenceFlow id="f1" sourceRef="start" targetRef="task1" />
    <sequenceFlow id="f2" sourceRef="task1" targetRef="end" />
""")
        result = validate_bpmn_xml(xml)
        # 不应有结构错误（V001-V009），但应有连通性警告
        structural_errors = [e for e in result.errors if e.rule_id in {"V001", "V002", "V003", "V005", "V006", "V007", "V008", "V009"}]
        assert len(structural_errors) == 0
        connectivity_warnings = [w for w in result.warnings if w.rule_id in {"V010", "V011"}]
        assert len(connectivity_warnings) >= 1


# ---------------------------------------------------------------------------
# 10. test_malformed_xml (V001)
# ---------------------------------------------------------------------------

class TestMalformedXml:
    """畸形 XML 应报告 V001 错误"""

    def test_malformed_xml(self):
        xml = "<not valid xml <<<>>>"
        result = validate_bpmn_xml(xml)
        assert result.is_valid is False
        v001 = [e for e in result.errors if e.rule_id == "V001"]
        assert len(v001) >= 1


# ---------------------------------------------------------------------------
# 11. test_empty_string (V001)
# ---------------------------------------------------------------------------

class TestEmptyString:
    """空字符串应报告 V001 错误"""

    def test_empty_string(self):
        result = validate_bpmn_xml("")
        assert result.is_valid is False
        v001 = [e for e in result.errors if e.rule_id == "V001"]
        assert len(v001) >= 1
