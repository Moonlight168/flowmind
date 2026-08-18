"""
FlowMind 智能流程设计服务 - BPMN XML 校验器

包装既有 validate_bpmn_xml，规则 ID 重映射 V→BPMN_V，新增 BPMN_V012（生成失败），
并把生成的 bpmn_xml 与统一后的 category 缓存进 design_output，供 format_node 复用。
"""

from app.agents.validators.base import (
    ValidationError,
    ValidationResult,
    ValidationSeverity,
    Validator,
    ValidatorContext,
)
from app.utils.bpmn_generator import generate_bpmn_xml
from app.utils.bpmn_validator import validate_bpmn_xml


def build_category(output: dict, current_form_data: dict) -> dict:
    """统一构造 category（review 与 format 共用同一逻辑，避免 process id/name 不一致）"""
    code = (
        output.get("code")
        or current_form_data.get("code")
        or current_form_data.get("category", "")
    )
    name = (
        output.get("flow_name")
        or current_form_data.get("flow_name")
        or current_form_data.get("modelName")
        or ""
    )
    return {"category_name": name, "code": code}


class BPMNXMLValidator:
    name = "bpmn_xml"

    def validate(self, output: dict, context: ValidatorContext) -> ValidationResult:
        if context.design_type != "flow_design" or context.mode == "basic":
            return ValidationResult.ok()

        category = build_category(output, context.current_form_data)
        try:
            bpmn_xml = generate_bpmn_xml(
                {"nodes": output.get("nodes", []) or [], "edges": output.get("edges", []) or []},
                category,
            )
            result = validate_bpmn_xml(bpmn_xml)
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # 生成失败（如非法节点类型导致 XML 构造异常）
            return ValidationResult.from_errors([
                ValidationError("BPMN_V012", f"BPMN XML 生成失败: {e}")
            ])

        # 缓存供 format_node 复用，避免二次生成
        output["bpmn_xml"] = bpmn_xml
        output["_category"] = category

        errors = [
            ValidationError(f"BPMN_{e.rule_id}", e.message, element_id=e.element_id)
            for e in result.errors
        ]
        warnings = [
            ValidationError(
                f"BPMN_{e.rule_id}", e.message, severity=ValidationSeverity.WARNING, element_id=e.element_id,
            )
            for e in result.warnings
        ]
        return ValidationResult(is_valid=not errors, errors=errors, warnings=warnings)
