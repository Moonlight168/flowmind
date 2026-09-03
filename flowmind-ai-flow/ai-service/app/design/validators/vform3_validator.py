"""Compile and validate the final VForm3 document before returning a preview."""

import json

from app.design.validators.base import (
    ValidationError,
    ValidationResult,
    ValidatorContext,
)
from app.design.vform3_transformer import transform_to_vform3


class VForm3Validator:
    name = "vform3"

    def validate(self, output: dict, context: ValidatorContext) -> ValidationResult:
        try:
            document = transform_to_vform3(output, context.current_form_data)
            json.dumps(document, ensure_ascii=False)
            validate_vform3_document(document)
        except (ValueError, TypeError, KeyError) as exc:
            return ValidationResult.from_errors(
                [ValidationError("VFORM_V001", f"VForm3 生成失败: {exc}")]
            )
        output["vform3"] = document
        return ValidationResult.ok()


def validate_vform3_document(document: dict) -> None:
    if not isinstance(document.get("widgetList"), list):
        raise ValueError("widgetList 必须是数组")
    if not isinstance(document.get("formConfig"), dict):
        raise ValueError("formConfig 必须是对象")
    for widget in _walk_document_widgets(document["widgetList"]):
        if not all(key in widget for key in ("id", "key", "type", "options")):
            if widget.get("internal") and all(
                key in widget for key in ("id", "type", "options")
            ):
                continue
            raise ValueError("组件缺少 VForm3 必需字段")


def _walk_document_widgets(widgets: list[dict]):
    for widget in widgets:
        yield widget
        yield from _walk_document_widgets(widget.get("widgetList") or [])
        yield from _walk_document_widgets(widget.get("cols") or [])
        yield from _walk_document_widgets(widget.get("tabs") or [])
        for row in widget.get("rows") or []:
            yield from _walk_document_widgets(row.get("cols") or [])
