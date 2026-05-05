"""
FlowMind 智能流程设计服务 - 流程表单设计任务

使用vform3根据流程分类和节点角色生成表单JSON
"""

# 任务指令
TASK = """根据流程分类和节点角色使用vform3生成对应的表单结构。

直接返回扁平 JSON，包含以下顶层字段：
- form_name: 表单名称
- node_role: 节点角色（applicant/approver/cc）
- widgetList: 字段数组
- formConfig: 表单配置

**重要：顶层字段平铺，不要嵌套！不要用 node_role 作为 key 包裹！**

## 输出格式说明

本系统采用**简化格式输出 + 后端自动补全**的架构：
- AI 只需生成核心业务字段（type、name、label 等）
- 后端自动补全 key、id、icon、columnWidth 等元数据
- 前端收到的是完整 VForm3 格式，可直接渲染

## widgetList 每个字段格式（简化版）

```json
{
  "type": "input|textarea|number|radio|select|checkbox|switch|date|time-range|...",
  "formItemFlag": true,
  "options": {
    "name": "字段绑定名（英文，唯一）",
    "label": "字段标签",
    "defaultValue": "默认值（可选）",
    "placeholder": "占位文本（可选）",
    "disabled": false,
    "hidden": false,
    "required": false,
    "readonly": false,
    "optionItems": [
      {"label": "选项1", "value": "1"},
      {"label": "选项2", "value": "2"}
    ]
  }
}
```

**formItemFlag**：字段组件固定为 `true`，容器组件为 `false`。

## 组件类型（type 值）

| 分类 | type 值 | 说明 |
|------|---------|------|
| 文本输入 | input | 单行输入框 |
| 文本输入 | textarea | 多行文本框 |
| 文本输入 | rich-editor | 富文本编辑器 |
| 数值输入 | number | 计数器 |
| 数值输入 | slider | 滑块 |
| 选择输入 | radio | 单选项 |
| 选择输入 | checkbox | 多选项 |
| 选择输入 | select | 下拉选择 |
| 选择输入 | cascader | 级联选择 |
| 日期时间 | time | 时间 |
| 日期时间 | time-range | 时间范围 |
| 日期时间 | date | 日期 |
| 日期时间 | date-range | 日期范围 |
| 开关/评分 | switch | 开关 |
| 开关/评分 | rate | 评分 |
| 颜色 | color | 颜色选择器 |
| 上传 | picture-upload | 图片上传 |
| 上传 | file-upload | 文件上传 |
| 展示 | static-text | 静态文字 |
| 展示 | html-text | HTML 文本 |
| 展示 | divider | 分隔线 |
| 展示 | button | 按钮 |

## 字段 options 核心字段说明

| 字段 | 适用组件 | 说明 |
|------|---------|------|
| name | 所有 | 字段绑定名（英文，唯一） |
| label | 所有 | 字段标签 |
| defaultValue | 所有 | 默认值 |
| placeholder | input/textarea/select/date/time | 占位文本 |
| required | 所有 | 是否必填 |
| disabled | 所有 | 是否禁用 |
| hidden | 所有 | 是否隐藏 |
| readonly | input/textarea/date/time | 是否只读 |
| optionItems | radio/checkbox/select/cascader | 选项列表 [{label, value}] |
| format | date/time/date-range/time-range | 显示格式，如 YYYY-MM-DD |
| valueFormat | date/time/date-range/time-range | 值格式，如 YYYY-MM-DD |
| min/max | number/slider | 最小/最大值 |
| step | number/slider | 步长 |
| rows | textarea | 文本域行数 |
| multiple | select/cascader | 是否多选 |
| filterable | select/cascader | 是否可搜索 |
| switchWidth | switch | 开关宽度 |
| activeText/inactiveText | switch | 开关文本 |
| rows | textarea | 行数 |
| limit | upload | 上传数量限制 |
| fileMaxSize | upload | 单文件最大大小（MB） |
| fileTypes | upload | 允许文件类型，如 ["jpg","png"] |

## 容器组件格式

容器组件（如 grid、card）与字段格式相同，但 formItemFlag 为 false：
```json
{
  "type": "card",
  "formItemFlag": false,
  "options": {
    "name": "cardName",
    "label": "卡片标题",
    "hidden": false,
    "folded": false,
    "cardWidth": "100%",
    "shadow": "never"
  }
}
```

## grid 容器（包含列）

grid 需要嵌套 cols：
```json
{
  "type": "grid",
  "formItemFlag": false,
  "options": {"name": "grid1", "gutter": 12},
  "cols": [
    {
      "type": "grid-col",
      "formItemFlag": false,
      "options": {"name": "col1", "span": 12},
      "fieldWidgets": []
    }
  ]
}
```

## formConfig 格式（简化版）

```json
{
  "modelName": "form",
  "refName": "formRef",
  "labelWidth": 100,
  "labelPosition": "right"
}
```

后端会自动补充 jsonVersion: 3 和 layoutType: "PC"。

## 节点角色说明

- applicant（申请人）：生成业务流程字段（日期、类型、事由、附件等）
- approver（审批人）：生成审批意见字段（同意/拒绝、审批备注等）
- cc（抄送人）：生成空表单或仅含基本信息
"""
