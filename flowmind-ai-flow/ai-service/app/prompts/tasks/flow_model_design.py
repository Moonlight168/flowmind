"""
FlowMind 智能流程设计服务 - 流程模型设计任务

使用bpmnio.js根据用户描述设计完整审批流程模型
"""

# 任务指令
TASK = """使用bpmnio.js设计完整审批流程模型，包含节点、审批人、条件分支。

## 输出要求

请以JSON格式输出，必须包含以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| flow_name | string | 是 | 流程名称，如"请假审批流程" |
| category_id | string | 是 | 流程分类编码，必须从【可用分类】中选择 code 值，无匹配则留空 "" |
| description | string | 否 | 流程简要描述 |
| nodes | array | 是 | 流程节点列表 |
| edges | array | 否 | 节点连线列表。省略时按 nodes 顺序自动生成线性流程 |

## 支持的节点类型

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| USER_TASK | 用户任务（审批节点） | 审批、填写、确认 |
| EXCLUSIVE_GATEWAY | 排他网关（XOR） | 条件分支，如金额分级审批 |
| PARALLEL_GATEWAY | 并行网关（AND） | 并行审批，多部门同时审核 |
| INTERMEDIATE_THROW_EVENT | 中间抛出事件 | 里程碑、通知触发点 |

## USER_TASK 节点属性

| 属性 | 必填 | 说明 |
|------|------|------|
| type | 是 | 固定为 "USER_TASK" |
| name | 是 | 节点名称，中文（如"部门经理审批"） |
| assignee | 否 | 审批人表达式，如 "${initiator}" 表示发起人 |
| candidate_groups | 是 | 候选角色组，必须从【可用角色】中选择 key 值 |
| text | 是 | 审批人显示名称，对应 candidate_groups 的角色中文名 |
| data_type | 是 | 审批人类型：INITIATOR/ROLES/USERS/EXPRESSION |
| form_key | 是 | 关联表单标识，必须从【可用表单】中选择 id 值 |

## edges 连线规则

- source: 源节点 ID 或 "start"（开始事件）
- target: 目标节点 ID 或 "end"（结束事件）
- condition: 条件表达式（仅排他网关出线需要），如 "${amount > 10000}"
- 简单线性流程可省略 edges，按 nodes 顺序自动生成

## 重要约束

- 所有字段值（category_id、candidate_groups、form_key）必须从提供的可用列表中选择，禁止自行编造
- 如果对应的可用列表为空或未提供，则该字段留空 ""
- 简单审批流程使用 USER_TASK 即可，需要条件分支时再使用 EXCLUSIVE_GATEWAY

## 示例1：简单线性流程

用户输入"请假审批"：
{
  "flow_name": "请假审批流程",
  "category_id": "HR",
  "description": "用于处理员工请假申请",
  "nodes": [
    {"type": "USER_TASK", "name": "部门经理审批", "candidate_groups": "ROLE1", "text": "超级管理员", "data_type": "ROLES", "form_key": "1"},
    {"type": "USER_TASK", "name": "HR备案", "candidate_groups": "ROLE2", "text": "普通角色", "data_type": "ROLES", "form_key": "1"}
  ]
}

## 示例2：条件分支流程

用户输入"报销审批，5000以下部门经理批，5000以上总经理批"：
{
  "flow_name": "报销审批流程",
  "category_id": "FINANCE",
  "description": "根据金额分级审批",
  "nodes": [
    {"id": "Task_1", "type": "USER_TASK", "name": "填写报销单", "assignee": "${initiator}", "data_type": "INITIATOR", "form_key": "2"},
    {"id": "Gw_1", "type": "EXCLUSIVE_GATEWAY", "name": "金额判断"},
    {"id": "Task_2", "type": "USER_TASK", "name": "部门经理审批", "candidate_groups": "ROLE1", "text": "超级管理员", "data_type": "ROLES", "form_key": "2"},
    {"id": "Task_3", "type": "USER_TASK", "name": "总经理审批", "candidate_groups": "ROLE1", "text": "超级管理员", "data_type": "ROLES", "form_key": "2"},
    {"id": "Gw_2", "type": "EXCLUSIVE_GATEWAY", "name": "合并"}
  ],
  "edges": [
    {"source": "start", "target": "Task_1"},
    {"source": "Task_1", "target": "Gw_1"},
    {"source": "Gw_1", "target": "Task_2", "condition": "${amount <= 5000}"},
    {"source": "Gw_1", "target": "Task_3", "condition": "${amount > 5000}"},
    {"source": "Task_2", "target": "Gw_2"},
    {"source": "Task_3", "target": "Gw_2"},
    {"source": "Gw_2", "target": "end"}
  ]
}"""
