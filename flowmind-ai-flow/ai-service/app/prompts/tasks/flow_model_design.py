"""
FlowMind 智能流程设计服务 - 流程模型设计任务

使用bpmnio.js根据用户描述设计完整审批流程模型
"""

# 任务指令
TASK = """设计审批流程编排。AI 只需生成节点和连线。

## 当前流程基本信息

{flow_basic_info}

**重要**：
- 上述流程基本信息已确定，**直接复用，不要重新生成**
- 如果提示"已有流程编排"，表示用户在**修改现有流程**，**必须保留原有节点，只根据用户需求增量修改**

## 输出格式（JSON）

**design 模式**（生成流程编排）：
- 必填：nodes（节点列表）
- 可选：edges（节点连线，省略时按 nodes 顺序自动生成线性流程）

**注意**：不要输出 flow_name、code、description，它们已在上方【当前流程基本信息】中！

## 节点类型

**START_EVENT（开始事件）**
- type：固定 "START_EVENT"
- id：固定 "startEvent" 或自定义
- name：节点名称，如"开始"
- form_key：关联表单（**必须先调用 search_forms("") 获取表单列表，输出 id 值，无匹配则留空 ""**）

**END_EVENT（结束事件）**
- type：固定 "END_EVENT"
- id：固定 "endEvent" 或自定义
- name：节点名称，如"结束"

**USER_TASK（审批节点）**
- type：固定 "USER_TASK"
- id：唯一标识，如 "node_approve"
- name：节点名称，如"部门经理审批"
- assignee：审批人表达式，填写人用 ${initiator}
- candidate_groups：审批角色（**必须先调用 search_roles() 获取角色列表，输出 key 值如 ROLE1，禁止输出中文名**）
- text：审批人显示名称（**对应 candidate_groups 的角色中文名，如"超级管理员"**）
- data_type：审批人类型，填写人用 INITIATOR，审批人用 ROLES
- form_key：关联表单（**必须先调用 search_forms("") 获取表单列表，输出 id 值，无匹配则留空 ""**）

**EXCLUSIVE_GATEWAY（排他/互斥网关）**：条件分支，仅选中一条路径
- type：固定 "EXCLUSIVE_GATEWAY"
- id：唯一标识，如 "gateway_condition"
- name：节点名称，如"金额判断"
- **关键约束**：排他网关必须有 ≥2 条出边，每条出边必须有 condition 字段
- **示例**：见下方 edges 示例

**PARALLEL_GATEWAY（并行网关）**：所有分支同时执行
- type：固定 "PARALLEL_GATEWAY"
- id：唯一标识，如 "gateway_parallel"
- **关键约束**：并行网关必须成对出现（fork + join）

**INCLUSIVE_GATEWAY（相容/包容网关）**：可选中一条或多条路径
- type：固定 "INCLUSIVE_GATEWAY"
- id：唯一标识，如 "gateway_inclusive"
- name：节点名称，如"条件判断"
- **关键约束**：相容网关必须有 ≥2 条出边，每条出边必须有 condition 字段

**COMPLEX_GATEWAY（复杂网关）**：复杂条件组合
- type：固定 "COMPLEX_GATEWAY"
- id：唯一标识，如 "gateway_complex"
- name：节点名称，如"复杂条件"

**EVENT_GATEWAY（事件网关）**：基于事件触发的分支
- type：固定 "EVENT_GATEWAY"
- id：唯一标识，如 "gateway_event"
- name：节点名称，如"事件等待"

## Edges 连线格式

edges 定义节点之间的连线关系：

```json
{
  "source": "源节点ID",
  "target": "目标节点ID",
  "condition": "条件表达式（仅排他网关需要）"
}
```

**特殊值**：
- `"start"` 表示从开始事件出发
- `"end"` 表示到达结束事件

**示例**：
```json
{
  "edges": [
    {"source": "start", "target": "node_submit"},
    {"source": "node_submit", "target": "gateway_amount"},
    {"source": "gateway_amount", "target": "node_manager", "condition": "${amount > 10000}"},
    {"source": "gateway_amount", "target": "node_director", "condition": "${amount <= 10000}"},
    {"source": "node_manager", "target": "end"},
    {"source": "node_director", "target": "end"}
  ]
}
```

**重要**：排他网关必须有多个 outgoing edges，每个 edge 必须有 condition！

## 约束

- **code 必须先调用 search_categories("") 获取分类列表，搜索结果格式：`[{"categoryId": 7, "categoryName": "人事管理", "code": "1", "remark": "..."}]`，从结果中选择相关分类，输出该分类的 code 字段值（如 "1"），禁止自行猜测或编造**
- **candidate_groups 必须先调用 search_roles() 获取角色列表，输出 key 值（如 ROLE1），禁止输出中文名**
- **text 对应 candidate_groups 的角色中文名，必须从 search_roles() 返回的 name 字段获取**
- **form_key 必须先调用 search_forms("") 获取表单列表，输出 id 值，无匹配则留空 ""**
- **已存在于【当前流程基本信息】的数据优先复用，只有用户明确修改才变更**

## 空结果处理

**每个工具最多调用 2 次**，如果结果为空则按以下方式处理：
- **search_categories 返回空列表**：系统中还没有分类，code 留空 ""
- **search_roles 返回空列表**：无可用角色，nodes 中不要添加审批节点或询问用户
- **search_forms 返回空列表**：系统中还没有表单，form_key 留空 ""

## 输出格式

**重要**：直接输出 JSON 文本作为 AI 消息内容，不要尝试调用任何工具！
**禁止**：不要在 JSON 前后添加任何解释、总结或额外文本！只输出纯 JSON！

- 需要追问时，输出：`{"intent": "clarification", "message": "您的追问内容"}`
- design 模式：`{"nodes": [...], "edges": [...]}`
"""
