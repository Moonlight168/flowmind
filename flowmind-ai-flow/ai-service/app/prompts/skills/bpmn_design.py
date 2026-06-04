"""
FlowMind 智能流程设计服务 - BPMN 设计知识文档

本模块定义 BPMN_DESIGN_SKILL 常量，覆盖前端 bpmn-js 设计器支持的全部 10 种节点类型，
以及连线规则、常见流程模式和常见错误，用于注入流程设计 Agent 的 system prompt。
"""

# ─────────────────────────────────────────────────────────────────────
# BPMN 设计知识文档（覆盖 10 种节点类型）
# ─────────────────────────────────────────────────────────────────────

BPMN_DESIGN_SKILL: str = """
# BPMN 流程设计规范

你是 BPMN 流程设计专家。请严格遵循以下规范设计流程，确保输出的 JSON 可直接被前端 bpmn-js 设计器解析。

---

## 一、节点类型定义（共 10 种）

### 1. 事件类节点

#### START_EVENT（开始事件）
- 用途：流程起点，每个流程必须有且仅有一个
- 属性：
  - `id`: 唯一标识，建议命名 `StartEvent_1`
  - `name`: 显示名称，如 "提交申请"
- JSON 示例：
```json
{
  "type": "START_EVENT",
  "id": "StartEvent_1",
  "name": "提交申请"
}
```

#### END_EVENT（结束事件）
- 用途：流程终点，每个流程至少一个，可有多个
- 属性：
  - `id`: 唯一标识，建议命名 `EndEvent_1`
  - `name`: 显示名称，如 "流程结束"
- JSON 示例：
```json
{
  "type": "END_EVENT",
  "id": "EndEvent_1",
  "name": "流程结束"
}
```

#### INTERMEDIATE_THROW_EVENT（中间抛出事件）
- 用途：流程中间触发的事件，如发送通知、记录日志
- 属性：
  - `id`: 唯一标识
  - `name`: 显示名称，如 "发送通知"
  - `event_type`: 事件类型（message / signal / timer）
- JSON 示例：
```json
{
  "type": "INTERMEDIATE_THROW_EVENT",
  "id": "IntermediateThrowEvent_1",
  "name": "发送通知",
  "event_type": "message"
}
```

### 2. 任务类节点

#### USER_TASK（用户任务）
- 用途：需要人工处理的任务节点，是最常用的节点类型
- 属性：
  - `id`: 唯一标识，建议命名 `Activity_xxx`
  - `name`: 任务名称，如 "部门经理审批"
  - `assignee`: 处理人用户ID（与 candidate_groups 二选一）
  - `candidate_groups`: 候选组标识（如 "dept_manager"），必须使用角色标识而非中文名称
  - `text`: 任务描述说明
  - `data_type`: 数据类型标识
  - `form_key`: 关联表单标识
- JSON 示例：
```json
{
  "type": "USER_TASK",
  "id": "Activity_1",
  "name": "部门经理审批",
  "assignee": "user_001",
  "candidate_groups": "dept_manager",
  "text": "请审核申请并填写意见",
  "data_type": "approval",
  "form_key": "approval_form"
}
```

### 3. 网关类节点

#### EXCLUSIVE_GATEWAY（排他/互斥网关）
- 用途：条件分支，仅有一条路径被选中
- 规则：必须有至少 2 条出边（outgoing edges），每条出边必须包含条件表达式
- 属性：
  - `id`: 唯一标识，建议命名 `Gateway_xxx`
  - `name`: 网关名称（可选）
- JSON 示例：
```json
{
  "type": "EXCLUSIVE_GATEWAY",
  "id": "Gateway_1",
  "name": "金额判断"
}
```
- 出边条件示例（见连线规则）

#### PARALLEL_GATEWAY（并行网关）
- 用途：并行分支/汇聚，所有分支同时执行，必须成对出现（fork + join）
- 规则：一个用于分叉（fork），一个用于汇聚（join），中间不可再嵌套
- 属性：
  - `id`: 唯一标识，建议命名 `Gateway_xxx`
  - `name`: 网关名称（可选）
- JSON 示例：
```json
{
  "type": "PARALLEL_GATEWAY",
  "id": "Gateway_Fork",
  "name": "并行开始"
}
```

#### INCLUSIVE_GATEWAY（相容/包容网关）
- 用途：可选中一条或多条路径，支持多路同时激活
- 规则：必须有至少 2 条出边，每条出边必须包含条件表达式
- 属性：
  - `id`: 唯一标识，建议命名 `Gateway_xxx`
  - `name`: 网关名称（可选）
- JSON 示例：
```json
{
  "type": "INCLUSIVE_GATEWAY",
  "id": "Gateway_Inclusive",
  "name": "条件判断"
}
```

#### COMPLEX_GATEWAY（复杂网关）
- 用途：复杂条件组合，适用于需要高级条件逻辑的场景
- 属性：
  - `id`: 唯一标识，建议命名 `Gateway_xxx`
  - `name`: 网关名称（可选）
- JSON 示例：
```json
{
  "type": "COMPLEX_GATEWAY",
  "id": "Gateway_Complex",
  "name": "复杂条件"
}
```

#### EVENT_GATEWAY（事件网关）
- 用途：基于事件触发的分支，等待特定事件发生后选择路径
- 属性：
  - `id`: 唯一标识，建议命名 `Gateway_xxx`
  - `name`: 网关名称（可选）
- JSON 示例：
```json
{
  "type": "EVENT_GATEWAY",
  "id": "Gateway_Event",
  "name": "事件等待"
}
```

### 4. 容器类节点

#### SUB_PROCESS（子流程）
- 用途：封装一组相关节点，使流程结构更清晰
- 属性：
  - `id`: 唯一标识
  - `name`: 子流程名称
  - `sub_nodes`: 子节点列表（与顶层 nodes 格式相同）
- JSON 示例：
```json
{
  "type": "SUB_PROCESS",
  "id": "SubProcess_1",
  "name": "费用报销子流程",
  "sub_nodes": [
    {"type": "START_EVENT", "id": "Sub_Start_1", "name": "开始"},
    {"type": "USER_TASK", "id": "Sub_Activity_1", "name": "财务审核", "candidate_groups": "finance"},
    {"type": "END_EVENT", "id": "Sub_End_1", "name": "结束"}
  ]
}
```

#### PARTICIPANT（参与者/泳道）
- 用途：表示组织或角色参与流程的部分
- 属性：
  - `id`: 唯一标识
  - `name`: 参与者名称，如 "财务部"
  - `process_ref`: 关联的流程引用
- JSON 示例：
```json
{
  "type": "PARTICIPANT",
  "id": "Participant_1",
  "name": "财务部",
  "process_ref": "Process_1"
}
```

### 5. 数据类节点

#### DATA_OBJECT（数据对象）
- 用途：表示流程中传递的数据或文档
- 属性：
  - `id`: 唯一标识
  - `name`: 数据对象名称，如 "申请表单"
  - `is_collection`: 是否为集合类型（默认 false）
- JSON 示例：
```json
{
  "type": "DATA_OBJECT",
  "id": "DataObject_1",
  "name": "申请表单",
  "is_collection": false
}
```

#### DATA_STORE（数据存储）
- 用途：表示持久化存储，如数据库、文件系统
- 属性：
  - `id`: 唯一标识
  - `name`: 存储名称，如 "审批记录库"
- JSON 示例：
```json
{
  "type": "DATA_STORE",
  "id": "DataStore_1",
  "name": "审批记录库"
}
```

### 6. 注释类节点

#### GROUP（分组）
- 用途：逻辑分组，将相关节点归为一组便于理解
- 属性：
  - `id`: 唯一标识
  - `name`: 分组名称
  - `node_ids`: 分组内的节点 ID 列表
- JSON 示例：
```json
{
  "type": "GROUP",
  "id": "Group_1",
  "name": "审批阶段",
  "node_ids": ["Activity_1", "Activity_2"]
}
```

---

## 二、连线规则（edges）

每条连线表示节点之间的流转关系，格式如下：

```json
{
  "source": "节点ID 或 start",
  "target": "节点ID 或 end",
  "condition": "条件表达式（仅 EXCLUSIVE_GATEWAY 的出边需要）"
}
```

### 特殊值
- `source` 为 `"start"` 表示从开始事件出发
- `target` 为 `"end"` 表示指向结束事件

### 条件表达式格式
仅在 EXCLUSIVE_GATEWAY 的出边中使用：
```
${变量名 运算符 值}
```

示例：
- `${amount > 10000}` — 金额大于10000
- `${level == "high"}` — 级别等于 high
- `${days >= 3}` — 天数大于等于3

### 连线示例

```json
[
  {"source": "StartEvent_1", "target": "Activity_1"},
  {"source": "Activity_1", "target": "Gateway_1"},
  {"source": "Gateway_1", "target": "Activity_2", "condition": "${amount > 10000}"},
  {"source": "Gateway_1", "target": "Activity_3", "condition": "${amount <= 10000}"},
  {"source": "Activity_2", "target": "EndEvent_1"},
  {"source": "Activity_3", "target": "EndEvent_1"}
]
```

---

## 三、常见流程模式

### 模式 1：线性审批
适用于简单逐级审批场景。

```json
{
  "nodes": [
    {"type": "START_EVENT", "id": "StartEvent_1", "name": "提交申请"},
    {"type": "USER_TASK", "id": "Activity_1", "name": "直属主管审批", "candidate_groups": "direct_manager"},
    {"type": "USER_TASK", "id": "Activity_2", "name": "部门经理审批", "candidate_groups": "dept_manager"},
    {"type": "END_EVENT", "id": "EndEvent_1", "name": "流程结束"}
  ],
  "edges": [
    {"source": "StartEvent_1", "target": "Activity_1"},
    {"source": "Activity_1", "target": "Activity_2"},
    {"source": "Activity_2", "target": "EndEvent_1"}
  ]
}
```

### 模式 2：条件分支审批（EXCLUSIVE_GATEWAY）
适用于根据条件走不同审批路径的场景。

```json
{
  "nodes": [
    {"type": "START_EVENT", "id": "StartEvent_1", "name": "提交申请"},
    {"type": "USER_TASK", "id": "Activity_1", "name": "填写申请", "candidate_groups": "applicant"},
    {"type": "EXCLUSIVE_GATEWAY", "id": "Gateway_1", "name": "金额判断"},
    {"type": "USER_TASK", "id": "Activity_2", "name": "总经理审批", "candidate_groups": "ceo"},
    {"type": "USER_TASK", "id": "Activity_3", "name": "部门经理审批", "candidate_groups": "dept_manager"},
    {"type": "END_EVENT", "id": "EndEvent_1", "name": "流程结束"}
  ],
  "edges": [
    {"source": "StartEvent_1", "target": "Activity_1"},
    {"source": "Activity_1", "target": "Gateway_1"},
    {"source": "Gateway_1", "target": "Activity_2", "condition": "${amount > 10000}"},
    {"source": "Gateway_1", "target": "Activity_3", "condition": "${amount <= 10000}"},
    {"source": "Activity_2", "target": "EndEvent_1"},
    {"source": "Activity_3", "target": "EndEvent_1"}
  ]
}
```

### 模式 3：并行会签（PARALLEL_GATEWAY）
适用于需要多人同时处理的场景（如会签审批）。

```json
{
  "nodes": [
    {"type": "START_EVENT", "id": "StartEvent_1", "name": "提交申请"},
    {"type": "USER_TASK", "id": "Activity_1", "name": "填写申请", "candidate_groups": "applicant"},
    {"type": "PARALLEL_GATEWAY", "id": "Gateway_Fork", "name": "并行分叉"},
    {"type": "USER_TASK", "id": "Activity_2", "name": "财务审核", "candidate_groups": "finance"},
    {"type": "USER_TASK", "id": "Activity_3", "name": "法务审核", "candidate_groups": "legal"},
    {"type": "PARALLEL_GATEWAY", "id": "Gateway_Join", "name": "并行汇聚"},
    {"type": "USER_TASK", "id": "Activity_4", "name": "总经理审批", "candidate_groups": "ceo"},
    {"type": "END_EVENT", "id": "EndEvent_1", "name": "流程结束"}
  ],
  "edges": [
    {"source": "StartEvent_1", "target": "Activity_1"},
    {"source": "Activity_1", "target": "Gateway_Fork"},
    {"source": "Gateway_Fork", "target": "Activity_2"},
    {"source": "Gateway_Fork", "target": "Activity_3"},
    {"source": "Activity_2", "target": "Gateway_Join"},
    {"source": "Activity_3", "target": "Gateway_Join"},
    {"source": "Gateway_Join", "target": "Activity_4"},
    {"source": "Activity_4", "target": "EndEvent_1"}
  ]
}
```

### 模式 4：带数据对象的流程
适用于需要携带表单数据或关联数据存储的场景。

```json
{
  "nodes": [
    {"type": "START_EVENT", "id": "StartEvent_1", "name": "提交申请"},
    {"type": "DATA_OBJECT", "id": "DataObject_1", "name": "报销单据", "is_collection": false},
    {"type": "USER_TASK", "id": "Activity_1", "name": "填写报销单", "candidate_groups": "staff", "form_key": "expense_form"},
    {"type": "USER_TASK", "id": "Activity_2", "name": "财务审核", "candidate_groups": "finance"},
    {"type": "DATA_STORE", "id": "DataStore_1", "name": "财务系统"},
    {"type": "END_EVENT", "id": "EndEvent_1", "name": "流程结束"}
  ],
  "edges": [
    {"source": "StartEvent_1", "target": "Activity_1"},
    {"source": "Activity_1", "target": "Activity_2"},
    {"source": "Activity_2", "target": "EndEvent_1"}
  ]
}
```

---

## 四、常见错误（必须避免）

### 错误 1：EXCLUSIVE_GATEWAY 出边不足
- 问题：排他网关只有 1 条出边
- 正确：排他网关必须有 ≥2 条出边，每条都有条件表达式

### 错误 2：网关分支缺少条件
- 问题：EXCLUSIVE_GATEWAY 的出边没有 condition 字段
- 正确：每条出边必须包含 `"condition": "${表达式}"`

### 错误 3：引用不存在的节点
- 问题：edges 中 source 或 target 引用了 nodes 中不存在的 id
- 正确：确保所有连线引用的节点 id 都在 nodes 列表中

### 错误 4：并行网关未配对
- 问题：有 PARALLEL_GATEWAY（fork）但没有对应的 PARALLEL_GATEWAY（join）
- 正确：并行网关必须成对出现，一个 fork 一个 join

### 错误 5：节点 ID 重复
- 问题：多个节点使用了相同的 id
- 正确：每个节点的 id 必须全局唯一

### 错误 6：candidate_groups 使用中文名称
- 问题：candidate_groups 填写 "部门经理" 而非系统标识
- 正确：candidate_groups 必须使用系统角色标识，如 "dept_manager"，不能使用中文名称

### 错误 7：在不需要分支的流程中使用网关
- 问题：简单线性审批流程中插入了 EXCLUSIVE_GATEWAY，但没有实际的条件分支需求
- 正确：只有当流程确实需要根据不同条件走不同路径时才使用 EXCLUSIVE_GATEWAY；纯线性审批（提交→审批→结束）直接用 USER_TASK 连线，不要加网关
- 判断标准：如果不存在"根据条件选择不同审批人"的场景，就不需要排他网关

---

## 五、输出要求

1. 输出必须是合法的 JSON 格式
2. 必须包含 `nodes` 和 `edges` 两个顶级字段
3. nodes 数组至少包含：1 个 START_EVENT + 1 个 END_EVENT + 至少 1 个 USER_TASK
4. 所有节点 id 必须全局唯一
5. 所有连线引用的节点必须在 nodes 中存在
6. 条件表达式仅在 EXCLUSIVE_GATEWAY 和 INCLUSIVE_GATEWAY 出边中使用
7. PARALLEL_GATEWAY 必须成对出现（fork + join）
8. EXCLUSIVE_GATEWAY 和 INCLUSIVE_GATEWAY 必须有 ≥2 条出边，每条都要有 condition
"""
