"""
FlowMind 智能流程设计服务 - 流程表单设计任务

使用vform3根据流程分类和节点角色生成表单JSON
"""

# 任务指令
TASK = """使用vform3生成表单JSON。AI只需生成type+options核心字段，其他由前端自动补全。

## 当前表单基本信息

{flow_basic_info}

**重要**：对用户"增加字段"、"修改表单名称"等操作，直接更新对应字段，不要重复询问已有信息。

## 输出格式（JSON）

顶层字段：form_name、node_role（applicant/approver/cc）、widgetList、formConfig
**平铺输出，不要嵌套！不要用node_role作为key包裹！**

## 字段组件（widgetList）

每个字段：{"type": "组件类型", "options": {"name": "字段名", "label": "标签", ...}}

### 常用组件类型

| 分类 | type |
|------|------|
| 文本输入 | input、textarea |
| 数值输入 | number、slider |
| 选择输入 | radio、checkbox、select、cascader |
| 日期时间 | date、time、date-range、time-range |
| 开关/评分 | switch、rate |
| 上传 | picture-upload、file-upload |
| 展示 | static-text、divider、button |

### options 核心字段

- name、label：必填
- defaultValue、placeholder、disabled、hidden、required：可选
- optionItems：选项列表，用于radio/checkbox/select，格式 [{"label": "标签", "value": "值"}]
- format/valueFormat：日期格式，如 YYYY-MM-DD

## 容器组件

grid/card/tab 等容器：formItemFlag=false
grid 嵌套 cols：{"type": "grid", "cols": [{"type": "grid-col", "options": {"name": "col1", "span": 12}}]}

## 节点角色

- applicant：业务流程字段（日期、事由、附件等）
- approver：审批意见字段（同意/拒绝、审批备注）
- cc：空表单或基本信息

## 约束

- **已存在于【当前表单基本信息】的数据优先复用，只有用户明确修改才变更**

## 输出

**重要**：直接输出 JSON 文本作为 AI 消息内容，不要尝试调用任何工具！
**禁止**：不要在 JSON 前后添加任何解释、总结或额外文本！只输出纯 JSON！

- 需要追问时，输出：`{"intent": "clarification", "message": "追问内容"}`
- 信息充足：`{"form_name": "...", "node_role": "...", "widgetList": [...], "formConfig": {...}}`
"""
