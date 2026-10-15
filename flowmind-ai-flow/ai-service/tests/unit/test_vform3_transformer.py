"""VForm3 transformation and validation regression tests."""

import pytest

from app.design.validators import FormFieldValidator, ValidatorContext
from app.design.vform3_transformer import transform_to_vform3


def test_existing_widget_identity_and_options_are_preserved():
    existing = {
        "id": "input-existing",
        "key": 12345,
        "type": "input",
        "formItemFlag": True,
        "options": {"name": "reason", "label": "原因", "customClass": "wide"},
    }
    result = transform_to_vform3(
        {"form_name": "请假", "widgetList": [existing], "formConfig": {}},
        {"formId": 9, "widgetList": [existing], "formConfig": {}},
    )
    assert result["widgetList"][0] == existing
    assert result["formId"] == 9


def test_display_widget_is_not_a_form_item():
    result = transform_to_vform3(
        {
            "form_name": "说明",
            "widgetList": [
                {
                    "type": "static-text",
                    "formItemFlag": False,
                    "options": {
                        "name": "notice",
                        "label": "说明",
                        "textContent": "请填写",
                    },
                }
            ],
        }
    )
    assert result["widgetList"][0]["formItemFlag"] is False


def test_unknown_widget_type_is_rejected_by_business_validation():
    result = FormFieldValidator().validate(
        {
            "widgetList": [
                {
                    "type": "invented-widget",
                    "formItemFlag": True,
                    "options": {"name": "invented", "label": "未知"},
                }
            ]
        },
        ValidatorContext(design_type="form_design"),
    )
    assert any(error.rule_id == "FORM_FF009" for error in result.errors)


def test_transformer_refuses_unknown_widget_type():
    with pytest.raises(ValueError, match="不支持的 VForm3 组件"):
        transform_to_vform3(
            {
                "form_name": "错误",
                "widgetList": [
                    {
                        "type": "invented-widget",
                        "formItemFlag": True,
                        "options": {"name": "invented", "label": "未知"},
                    }
                ],
            }
        )


def test_tab_nested_widgets_are_preserved():
    nested = {
        "type": "input",
        "formItemFlag": True,
        "options": {"name": "reason", "label": "原因"},
    }
    result = transform_to_vform3(
        {
            "form_name": "请假",
            "widgetList": [
                {
                    "type": "tab",
                    "formItemFlag": False,
                    "options": {},
                    "tabs": [{"options": {"label": "申请"}, "widgetList": [nested]}],
                }
            ],
        }
    )

    assert (
        result["widgetList"][0]["tabs"][0]["widgetList"][0]["options"]["name"]
        == "reason"
    )
