"""
FlowMind 智能流程设计服务 - 流程设计相关 JSON Schema

本模块定义流程设计相关的 JSON Schema，用于大模型原生结构化输出。

设计原则：
- AI 只生成节点名称和流程结构
- 审批人属性（assignees、strategy）不生成，由用户在前端编辑器中设置
"""

# 流程基本信息 Schema（basic 模式）
# 仅生成流程名称、分类、描述，不涉及 BPMN 流程编排
FLOW_DESIGN_BASIC_SCHEMA = {
    "type": "object",
    "properties": {
        "flow_name": {
            "type": "string",
            "description": "流程名称（如\"请假审批流程\"、\"报销审批流程\"等）",
        },
        "code": {
            "type": "string",
            "description": "流程分类编码，从可用分类中选择最匹配的 code，若无匹配则留空",
        },
        "description": {
            "type": "string",
            "description": "流程描述（可选）",
        },
    },
    "required": ["flow_name", "code"],
    "additionalProperties": False,
}

# 流程编排设计 Schema（design 模式）
# 仅生成节点和连线，流程基本信息从 current_form_data 读取
FLOW_DESIGN_NODES_SCHEMA = {
    "type": "object",
    "properties": {
        "nodes": {
            "type": "array",
            "description": "流程节点列表",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": [
                            "START_EVENT",
                            "END_EVENT",
                            "USER_TASK",
                            "EXCLUSIVE_GATEWAY",
                            "PARALLEL_GATEWAY",
                            "INCLUSIVE_GATEWAY",
                            "COMPLEX_GATEWAY",
                            "EVENT_GATEWAY",
                            "INTERMEDIATE_THROW_EVENT",
                        ],
                        "description": "节点类型",
                    },
                    "id": {
                        "type": "string",
                        "description": "节点唯一标识",
                    },
                    "name": {
                        "type": "string",
                        "description": "节点名称",
                    },
                    "assignee": {
                        "type": "string",
                        "description": "审批人表达式，如 ${initiator}",
                    },
                    "candidate_groups": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "候选角色组 key 列表",
                    },
                    "text": {
                        "type": "string",
                        "description": "审批人显示名称",
                    },
                    "data_type": {
                        "type": "string",
                        "enum": ["INITIATOR", "ROLES", "USERS", "EXPRESSION"],
                        "description": "审批人类型",
                    },
                    "form_key": {
                        "type": "string",
                        "description": "关联表单标识",
                    },
                },
                "required": ["type", "name"],
                "additionalProperties": False,
            },
        },
        "edges": {
            "type": "array",
            "description": "节点连线列表。定义节点间的连接关系。source/target 使用节点 id，特殊值 'start' 表示开始事件，'end' 表示结束事件",
            "items": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "源节点 ID，或 'start' 表示从开始事件出发"},
                    "target": {"type": "string", "description": "目标节点 ID，或 'end' 表示到达结束事件"},
                    "condition": {"type": "string", "description": "条件表达式（仅排他网关出线需要），如 ${amount > 10000}"},
                },
                "required": ["source", "target"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["nodes"],
    "additionalProperties": False,
}

# 流程分类生成 Schema
CATEGORY_GENERATION_SCHEMA = {
    "type": "object",
    "properties": {
        "category_name": {
            "type": "string",
            "description": '分类名称（如"请假审批"、"报销审批"等）',
        },
        "code": {
            "type": "string",
            "description": '分类编码（如"leave_approval"、"expense_approval"等）',
        },
        "remark": {"type": "string", "description": "分类备注"},
    },
    "required": ["category_name", "code"],
    "additionalProperties": False,
}

# 分类决策 Schema（用于多分类匹配时的智能选择）
CATEGORY_DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["reuse", "create_new"],
            "description": "决策操作：reuse（复用已存在的分类）或 create_new（新建分类）",
        },
        "selected_category_id": {
            "type": "integer",
            "description": "复用时的分类 ID（action 为 reuse 时必填）",
        },
        "reasoning": {
            "type": "string",
            "description": "决策原因（如\"用户提到'财务部'，选择财务部请假审批\"）",
        },
        "suggested_category_name": {
            "type": "string",
            "description": "新建时建议的分类名称（action 为 create_new 时可选）",
        },
    },
    "required": ["action", "reasoning"],
    "additionalProperties": False,
}

# 流程决策 Schema（用于多流程匹配时的智能选择）
FLOW_DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["reuse", "create_new"],
            "description": "决策操作：reuse（复用已存在的流程）或 create_new（新建流程）",
        },
        "selected_flow_id": {
            "type": "string",
            "description": "复用时的流程 ID（action 为 reuse 时必填）",
        },
        "reasoning": {
            "type": "string",
            "description": "决策原因（如\"用户提到'请假审批'，选择请假审批流程\"）",
        },
        "suggested_flow_name": {
            "type": "string",
            "description": "新建时建议的流程名称（action 为 create_new 时可选）",
        },
    },
    "required": ["action", "reasoning"],
    "additionalProperties": False,
}

# 流程表单生成 Schema（简化格式）
# AI 生成简化字段，前端/后端自动补全完整 VForm3 格式
# 简化格式：{ type, formItemFlag, options: { name, label, ... } }
FORM_GENERATION_SCHEMA = {
    "type": "object",
    "properties": {
        "form_name": {
            "type": "string",
            "description": "表单名称",
        },
        "node_role": {
            "type": "string",
            "enum": ["applicant", "approver", "cc"],
            "description": "节点角色：applicant（申请人）/ approver（审批人）/ cc（抄送人）",
        },
        "widgetList": {
            "type": "array",
            "description": "字段列表数组（简化格式，自动补全为完整 VForm3 JSON）",
            "items": {
                "type": "object",
                "description": "单个字段（简化格式）",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": [
                            "input", "textarea", "rich-editor",
                            "number", "slider",
                            "radio", "checkbox", "select", "cascader",
                            "time", "time-range", "date", "date-range",
                            "switch", "rate", "color",
                            "picture-upload", "file-upload",
                            "static-text", "html-text", "divider", "button",
                            # 容器
                            "grid", "table", "tab", "card",
                        ],
                        "description": "VForm3 组件类型",
                    },
                    "formItemFlag": {
                        "type": "boolean",
                        "description": "是否为表单项，字段组件固定为 true，容器为 false",
                    },
                    "options": {
                        "type": "object",
                        "description": "组件配置选项（简化版）",
                        "properties": {
                            # 通用
                            "name": {"type": "string", "description": "字段绑定名（英文，唯一）"},
                            "label": {"type": "string", "description": "字段标签"},
                            "defaultValue": {"type": ["string", "number", "boolean", "null"], "description": "默认值"},
                            "placeholder": {"type": "string", "description": "占位文本"},
                            "disabled": {"type": "boolean", "description": "是否禁用"},
                            "hidden": {"type": "boolean", "description": "是否隐藏"},
                            "required": {"type": "boolean", "description": "是否必填"},
                            "readonly": {"type": "boolean", "description": "是否只读"},
                            # 容器特有
                            "gutter": {"type": "number", "description": "栅格间距（grid）"},
                            "span": {"type": "number", "description": "栅格列宽（grid-col）"},
                            "folded": {"type": "boolean", "description": "是否折叠（card）"},
                            "cardWidth": {"type": "string", "description": "卡片宽度（card）"},
                            "shadow": {"type": "string", "description": "阴影样式（card）"},
                            # radio/checkbox/select/cascader 特有
                            "optionItems": {
                                "type": "array",
                                "description": "选项列表（用于 radio/checkbox/select/cascader）",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "label": {"type": "string", "description": "显示文本"},
                                        "value": {"type": ["string", "number"], "description": "绑定值"},
                                        "children": {
                                            "type": "array",
                                            "description": "子选项（仅 cascader）",
                                            "items": {"type": "object", "properties": {"label": {"type": "string"}, "value": {"type": ["string", "number"]}}}
                                        }
                                    },
                                    "required": ["label", "value"],
                                },
                            },
                            # select 特有
                            "multiple": {"type": "boolean", "description": "是否多选（select/cascader）"},
                            "filterable": {"type": "boolean", "description": "是否可搜索（select/cascader）"},
                            "clearable": {"type": "boolean", "description": "是否显示清除按钮"},
                            # number 特有
                            "min": {"type": "number", "description": "最小值（number/slider）"},
                            "max": {"type": "number", "description": "最大值（number/slider）"},
                            "step": {"type": "number", "description": "步长（number/slider）"},
                            "precision": {"type": "number", "description": "精度（number）"},
                            # date/time 特有
                            "format": {"type": "string", "description": "显示格式，如 YYYY-MM-DD"},
                            "valueFormat": {"type": "string", "description": "值格式，如 YYYY-MM-DD"},
                            "startPlaceholder": {"type": "string", "description": "开始占位文本（范围类）"},
                            "endPlaceholder": {"type": "string", "description": "结束占位文本（范围类）"},
                            # switch 特有
                            "switchWidth": {"type": "number", "description": "开关宽度"},
                            "activeText": {"type": "string", "description": "开启文本"},
                            "inactiveText": {"type": "string", "description": "关闭文本"},
                            # textarea 特有
                            "rows": {"type": "number", "description": "文本域行数"},
                            # upload 特有
                            "limit": {"type": "number", "description": "上传文件数量限制"},
                            "fileMaxSize": {"type": "number", "description": "单文件最大大小（MB）"},
                            "fileTypes": {"type": "array", "items": {"type": "string"}, "description": "允许的文件类型"},
                            "multipleSelect": {"type": "boolean", "description": "是否多选文件"},
                            "showFileList": {"type": "boolean", "description": "是否显示文件列表"},
                            # slider 特有
                            "range": {"type": "boolean", "description": "是否为范围选择"},
                            "showStops": {"type": "boolean", "description": "是否显示间断点"},
                            # button 特有
                            "displayStyle": {"type": "string", "enum": ["block", "inline"], "description": "显示样式"},
                            "buttonType": {"type": "string", "description": "按钮类型 primary/success/warning/danger/info/text"},
                            # static-text/html-text 特有
                            "textContent": {"type": "string", "description": "静态文字内容"},
                            "htmlContent": {"type": "string", "description": "HTML 内容"},
                            # divider 特有
                            "direction": {"type": "string", "enum": ["horizontal", "vertical"], "description": "方向"},
                            "contentPosition": {"type": "string", "enum": ["left", "center", "right"], "description": "内容位置"},
                            # cascader 特有
                            "checkStrictly": {"type": "boolean", "description": "是否严格选中（cascader）"},
                            "showAllLevels": {"type": "boolean", "description": "是否显示完整路径（cascader）"},
                        },
                        "required": ["name", "label"],
                    },
                },
                "required": ["type", "formItemFlag", "options"],
                "additionalProperties": False,
            },
        },
        "formConfig": {
            "type": "object",
            "description": "表单全局配置（简化版）",
            "properties": {
                "modelName": {"type": "string", "description": "数据模型名称"},
                "refName": {"type": "string", "description": "表单引用名称"},
                "labelWidth": {"type": "number", "description": "标签宽度"},
                "labelPosition": {"type": "string", "enum": ["left", "right", "top"], "description": "标签位置"},
            },
        },
    },
    "required": ["form_name", "widgetList"],
    "additionalProperties": False,
}
