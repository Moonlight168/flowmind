"""
FlowMind 智能流程设计服务 - VForm3 格式转换器

将 AI 生成的简化格式自动补全为完整的 VForm3 JSON 格式。
- AI 生成：简化字段（type、formItemFlag、options 核心业务字段）
- 转换后：完整 VForm3 格式（包含 key、id、icon、元数据等）
"""

import random
import time
from typing import Any


def generate_id(prefix: str = "") -> str:
    """生成唯一 ID"""
    timestamp = int(time.time() * 1000) % 100000
    rand = random.randint(10000, 99999)
    return f"{prefix}{timestamp}{rand}" if prefix else f"{timestamp}{rand}"


def generate_key() -> int:
    """生成随机数字 key"""
    return random.randint(10000, 99999)


# 组件类型到图标名称的映射
ICON_MAP = {
    "input": "text-field",
    "textarea": "textarea-field",
    "rich-editor": "rich-editor-field",
    "number": "number-field",
    "slider": "slider-field",
    "radio": "radio-field",
    "checkbox": "checkbox-field",
    "select": "select-field",
    "cascader": "cascader-field",
    "time": "time-field",
    "time-range": "time-range-field",
    "date": "date-field",
    "date-range": "date-range-field",
    "switch": "switch-field",
    "rate": "rate-field",
    "color": "color-field",
    "picture-upload": "picture-upload-field",
    "file-upload": "file-upload-field",
    "static-text": "static-text",
    "html-text": "html-text",
    "button": "button",
    "divider": "divider",
    "grid": "grid",
    "table": "table",
    "tab": "tab",
    "card": "card",
    "grid-col": "grid-col",
    "alert": "alert",
}

# 字段组件（formItemFlag=True）
FIELD_TYPES = {
    "input", "textarea", "rich-editor", "number", "slider",
    "radio", "checkbox", "select", "cascader",
    "time", "time-range", "date", "date-range",
    "switch", "rate", "color",
    "picture-upload", "file-upload",
}

# 容器组件（formItemFlag=False）
CONTAINER_TYPES = {"grid", "table", "tab", "card", "grid-col"}


def _build_field_options(widget_type: str, ai_options: dict[str, Any]) -> dict[str, Any]:
    """构建完整的 field options"""
    name = ai_options.get("name", "")
    label = ai_options.get("label", "")

    options = {
        # 通用
        "name": name,
        "label": label,
        "labelAlign": "",
        "columnWidth": "200px",
        "labelWidth": None,
        "labelHidden": False,
        "labelIconClass": None,
        "labelIconPosition": "rear",
        "labelTooltip": None,
        "hidden": ai_options.get("hidden", False),
        "customClass": "",
        # 事件回调默认空
        "onCreated": "",
        "onMounted": "",
        "onChange": "",
        "onFocus": "",
        "onBlur": "",
        "onValidate": "",
    }

    # 通用业务字段
    if ai_options.get("defaultValue") is not None:
        options["defaultValue"] = ai_options["defaultValue"]
    else:
        options["defaultValue"] = _get_default_value(widget_type)

    if ai_options.get("placeholder"):
        options["placeholder"] = ai_options["placeholder"]
    if ai_options.get("disabled") is not None:
        options["disabled"] = ai_options["disabled"]
    if ai_options.get("required") is not None:
        options["required"] = ai_options["required"]
    if ai_options.get("readonly") is not None:
        options["readonly"] = ai_options["readonly"]
    if ai_options.get("clearable") is not None:
        options["clearable"] = ai_options["clearable"]

    # 按类型补充特定选项
    if widget_type == "input":
        options["type"] = ai_options.get("type", "text")
        options["showPassword"] = False
        options["minLength"] = None
        options["maxLength"] = None
        options["showWordLimit"] = False
        options["prefixIcon"] = ""
        options["suffixIcon"] = ""
        options["appendButton"] = False
        options["appendButtonDisabled"] = False
        options["buttonIcon"] = ""
        options["onInput"] = ""
        options["onAppendButtonClick"] = ""
        if "minLength" in ai_options:
            options["minLength"] = ai_options["minLength"]
        if "maxLength" in ai_options:
            options["maxLength"] = ai_options["maxLength"]
        if "showWordLimit" in ai_options:
            options["showWordLimit"] = ai_options["showWordLimit"]

    elif widget_type == "textarea":
        options["rows"] = ai_options.get("rows", 3)
        options["minLength"] = None
        options["maxLength"] = None
        options["showWordLimit"] = False
        options["onInput"] = ""

    elif widget_type == "number":
        options["min"] = ai_options.get("min", -100000000000)
        options["max"] = ai_options.get("max", 100000000000)
        options["precision"] = ai_options.get("precision", 0)
        options["step"] = ai_options.get("step", 1)
        options["controlsPosition"] = ai_options.get("controlsPosition", "right")
        options["onInput"] = ""

    elif widget_type == "radio":
        options["displayStyle"] = ai_options.get("displayStyle", "inline")
        options["buttonStyle"] = False
        options["border"] = False
        options["optionItems"] = ai_options.get("optionItems", [])

    elif widget_type == "checkbox":
        options["displayStyle"] = ai_options.get("displayStyle", "inline")
        options["buttonStyle"] = False
        options["border"] = False
        options["defaultValue"] = ai_options.get("defaultValue", [])
        options["optionItems"] = ai_options.get("optionItems", [])
        if not options["defaultValue"]:
            options["defaultValue"] = []

    elif widget_type == "select":
        options["multiple"] = ai_options.get("multiple", False)
        options["multipleLimit"] = 0
        options["filterable"] = ai_options.get("filterable", False)
        options["allowCreate"] = False
        options["remote"] = False
        options["automaticDropdown"] = False
        options["optionItems"] = ai_options.get("optionItems", [])
        options["onRemoteQuery"] = ""

    elif widget_type == "cascader":
        options["multiple"] = ai_options.get("multiple", False)
        options["checkStrictly"] = ai_options.get("checkStrictly", False)
        options["showAllLevels"] = ai_options.get("showAllLevels", True)
        options["filterable"] = ai_options.get("filterable", False)
        options["optionItems"] = ai_options.get("optionItems", [])

    elif widget_type == "time":
        options["defaultValue"] = None
        options["autoFullWidth"] = True
        options["editable"] = False
        options["format"] = ai_options.get("format", "HH:mm:ss")
        options["valueFormat"] = ai_options.get("valueFormat", "HH:mm:ss")

    elif widget_type == "time-range":
        options["defaultValue"] = None
        options["startPlaceholder"] = ai_options.get("startPlaceholder", "")
        options["endPlaceholder"] = ai_options.get("endPlaceholder", "")
        options["autoFullWidth"] = True
        options["editable"] = False
        options["format"] = ai_options.get("format", "HH:mm:ss")
        options["valueFormat"] = ai_options.get("valueFormat", "HH:mm:ss")

    elif widget_type == "date":
        options["defaultValue"] = None
        options["type"] = "date"
        options["autoFullWidth"] = True
        options["editable"] = False
        options["format"] = ai_options.get("format", "YYYY-MM-DD")
        options["valueFormat"] = ai_options.get("valueFormat", "YYYY-MM-DD")

    elif widget_type == "date-range":
        options["defaultValue"] = None
        options["type"] = "daterange"
        options["startPlaceholder"] = ai_options.get("startPlaceholder", "")
        options["endPlaceholder"] = ai_options.get("endPlaceholder", "")
        options["autoFullWidth"] = True
        options["editable"] = False
        options["format"] = ai_options.get("format", "YYYY-MM-DD")
        options["valueFormat"] = ai_options.get("valueFormat", "YYYY-MM-DD")

    elif widget_type == "switch":
        options["defaultValue"] = ai_options.get("defaultValue", False)
        options["switchWidth"] = ai_options.get("switchWidth", 40)
        options["activeText"] = ai_options.get("activeText", "")
        options["inactiveText"] = ai_options.get("inactiveText", "")
        options["activeColor"] = None
        options["inactiveColor"] = None

    elif widget_type == "rate":
        options["max"] = ai_options.get("max", 5)
        options["lowThreshold"] = 2
        options["highThreshold"] = 4
        options["allowHalf"] = False
        options["showText"] = False
        options["showScore"] = False

    elif widget_type == "color":
        options["defaultValue"] = None

    elif widget_type == "slider":
        options["min"] = ai_options.get("min", 0)
        options["max"] = ai_options.get("max", 100)
        options["step"] = ai_options.get("step", 10)
        options["range"] = ai_options.get("range", False)
        options["showStops"] = ai_options.get("showStops", False)
        options["height"] = None

    elif widget_type == "picture-upload":
        options["labelWidth"] = None
        options["customRule"] = ""
        options["customRuleHint"] = ""
        options["uploadURL"] = ""
        options["uploadTip"] = ""
        options["withCredentials"] = False
        options["multipleSelect"] = ai_options.get("multipleSelect", False)
        options["showFileList"] = ai_options.get("showFileList", True)
        options["limit"] = ai_options.get("limit", 3)
        options["fileMaxSize"] = ai_options.get("fileMaxSize", 5)
        options["fileTypes"] = ai_options.get("fileTypes", ["jpg", "jpeg", "png"])
        options["onBeforeUpload"] = ""
        options["onUploadSuccess"] = ""
        options["onUploadError"] = ""
        options["onFileRemove"] = ""

    elif widget_type == "file-upload":
        options["labelWidth"] = None
        options["customRule"] = ""
        options["customRuleHint"] = ""
        options["uploadURL"] = ""
        options["uploadTip"] = ""
        options["withCredentials"] = False
        options["multipleSelect"] = ai_options.get("multipleSelect", False)
        options["showFileList"] = ai_options.get("showFileList", True)
        options["limit"] = ai_options.get("limit", 3)
        options["fileMaxSize"] = ai_options.get("fileMaxSize", 5)
        options["fileTypes"] = ai_options.get("fileTypes", ["doc", "docx", "xls", "xlsx"])
        options["onBeforeUpload"] = ""
        options["onUploadSuccess"] = ""
        options["onUploadError"] = ""
        options["onFileRemove"] = ""

    elif widget_type == "rich-editor":
        options["placeholder"] = ""
        options["contentHeight"] = "200px"
        options["minLength"] = None
        options["maxLength"] = None
        options["showWordLimit"] = False
        options["customRule"] = ""
        options["customRuleHint"] = ""

    elif widget_type == "static-text":
        options["textContent"] = ai_options.get("textContent", "")
        options["formItemFlag"] = False

    elif widget_type == "html-text":
        options["htmlContent"] = ai_options.get("htmlContent", "<b>html text</b>")
        options["formItemFlag"] = False

    elif widget_type == "button":
        options["displayStyle"] = ai_options.get("displayStyle", "block")
        options["type"] = ai_options.get("buttonType", "")
        options["plain"] = False
        options["round"] = False
        options["circle"] = False
        options["icon"] = None
        options["formItemFlag"] = False
        options["onClick"] = ""

    elif widget_type == "divider":
        options["direction"] = ai_options.get("direction", "horizontal")
        options["contentPosition"] = ai_options.get("contentPosition", "center")
        options["formItemFlag"] = False

    return options


def _build_container_options(widget_type: str, ai_options: dict[str, Any]) -> dict[str, Any]:
    """构建容器组件的 options"""
    options = {
        "name": ai_options.get("name", ""),
        "hidden": ai_options.get("hidden", False),
        "customClass": "",
    }

    if widget_type == "grid":
        options["gutter"] = ai_options.get("gutter", 12)
        options["colHeight"] = None

    elif widget_type == "card":
        options["label"] = ai_options.get("label", "")
        options["folded"] = ai_options.get("folded", False)
        options["showFold"] = True
        options["cardWidth"] = ai_options.get("cardWidth", "100%")
        options["shadow"] = ai_options.get("shadow", "never")

    elif widget_type == "tab":
        options["displayType"] = "border-card"

    elif widget_type == "table":
        pass

    return options


def _transform_widget(widget: dict[str, Any]) -> dict[str, Any]:
    """转换单个 widget 为完整 VForm3 格式"""
    widget_type = widget.get("type", "")
    ai_options = widget.get("options", {})
    form_item_flag = widget.get("formItemFlag", widget_type in FIELD_TYPES)

    icon = ICON_MAP.get(widget_type, f"{widget_type}-field")

    if widget_type in FIELD_TYPES:
        # 字段组件
        options = _build_field_options(widget_type, ai_options)
        result = {
            "key": generate_key(),
            "type": widget_type,
            "icon": icon,
            "formItemFlag": True,
            "options": options,
            "id": generate_id(widget_type),
        }
        # 处理 optionItems（字段可能有）
        if "optionItems" in ai_options:
            result["options"]["optionItems"] = ai_options["optionItems"]
        return result

    elif widget_type == "grid-col":
        # grid 列
        return {
            "key": generate_key(),
            "type": "grid-col",
            "category": "container",
            "icon": "grid-col",
            "internal": True,
            "widgetList": [],
            "options": {
                "name": ai_options.get("name", ""),
                "hidden": ai_options.get("hidden", False),
                "span": ai_options.get("span", 12),
                "offset": 0,
                "push": 0,
                "pull": 0,
                "responsive": False,
                "md": ai_options.get("span", 12),
                "sm": ai_options.get("span", 12),
                "xs": ai_options.get("span", 12),
                "customClass": "",
            },
            "id": generate_id("grid-col-"),
        }

    elif widget_type in CONTAINER_TYPES:
        # 容器组件
        options = _build_container_options(widget_type, ai_options)
        result = {
            "key": generate_key(),
            "type": widget_type,
            "category": "container",
            "icon": icon,
            "options": options,
            "id": generate_id(widget_type),
        }

        if widget_type == "grid":
            # 处理 grid 的 cols
            cols = widget.get("cols", [])
            result["cols"] = [_transform_widget(col) for col in cols]

        elif widget_type == "card":
            result["widgetList"] = []
            result["options"]["folded"] = ai_options.get("folded", False)
            result["options"]["showFold"] = True
            result["options"]["cardWidth"] = ai_options.get("cardWidth", "100%")
            result["options"]["shadow"] = ai_options.get("shadow", "never")

        elif widget_type == "tab":
            # 处理 tab 的 tabs
            tabs = widget.get("tabs", [])
            default_tabs = [{
                "type": "tab-pane",
                "category": "container",
                "icon": "tab-pane",
                "internal": True,
                "widgetList": [],
                "options": {
                    "name": f"tab{i+1}",
                    "label": f"tab {i+1}",
                    "hidden": False,
                    "active": i == 0,
                    "disabled": False,
                    "customClass": "",
                },
                "id": generate_id("tab-pane-"),
            } for i in range(len(tabs) if tabs else 1)]
            result["tabs"] = default_tabs

        elif widget_type == "table":
            # 处理 table 的 rows
            result["rows"] = [{
                "cols": [{
                    "type": "table-cell",
                    "category": "container",
                    "icon": "table-cell",
                    "internal": True,
                    "widgetList": [],
                    "merged": False,
                    "options": {
                        "name": generate_id("table-cell-"),
                        "cellWidth": "",
                        "cellHeight": "",
                        "colspan": 1,
                        "rowspan": 1,
                        "customClass": "",
                    },
                    "id": generate_id("table-cell-"),
                }],
                "id": generate_id("table-row-"),
                "merged": False,
            }]

        return result

    else:
        # 未知类型，作为字段处理
        options = _build_field_options(widget_type, ai_options)
        return {
            "key": generate_key(),
            "type": widget_type,
            "icon": icon,
            "formItemFlag": True,
            "options": options,
            "id": generate_id(widget_type),
        }


def _get_default_value(widget_type: str) -> Any:
    """获取各组件类型的默认值"""
    defaults = {
        "input": "",
        "textarea": "",
        "rich-editor": "",
        "number": 0,
        "slider": 0,
        "radio": None,
        "checkbox": [],
        "select": None,
        "cascader": None,
        "time": None,
        "time-range": None,
        "date": None,
        "date-range": None,
        "switch": False,
        "rate": None,
        "color": None,
        "picture-upload": "",
        "file-upload": "",
    }
    return defaults.get(widget_type)


def transform_to_vform3(ai_result: dict[str, Any]) -> dict[str, Any]:
    """将 AI 生成的简化格式转换为完整的 VForm3 JSON

    Args:
        ai_result: AI 生成的简化格式表单数据

    Returns:
        完整的 VForm3 表单 JSON，可直接用于 VFormRender
    """
    # 转换 widgetList
    ai_widgets = ai_result.get("widgetList", [])
    transformed_widgets = [_transform_widget(w) for w in ai_widgets]

    # 构建 formConfig
    ai_form_config = ai_result.get("formConfig", {}) or {}
    form_config = {
        "modelName": ai_form_config.get("modelName", "formData"),
        "refName": ai_form_config.get("refName", "vForm"),
        "rulesName": "rules",
        "labelWidth": ai_form_config.get("labelWidth", 80),
        "labelPosition": ai_form_config.get("labelPosition", "left"),
        "size": "",
        "labelAlign": "label-left-align",
        "cssCode": "",
        "customClass": "",
        "functions": "",
        "layoutType": "PC",
        "jsonVersion": 3,
        "onFormCreated": "",
        "onFormMounted": "",
        "onFormDataChange": "",
        "onFormValidate": "",
    }

    return {
        "form_name": ai_result.get("form_name", ""),
        "widgetList": transformed_widgets,
        "formConfig": form_config,
    }
