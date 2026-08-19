# AI 流程设计重构方案（结构化输出 + 增量修改 + 版本管理）

> 状态：已实施 Commit 1-6 + workflow review 修复；Commit 7（删 ReAct/json-repair）待结构化输出真实 LLM 验证稳定后
> 日期：2026-08-19
> 关联：`2026-08-17-validation-and-compression-design.md`（已落地的校验层 + 压缩）

## 0. 目标与核心决策

把「LLM 自由输出 JSON → 解析 → 校验」升级为「结构化输出约束生成」，并补齐增量修改和版本管理。

**核心决策（最终定版）**：

| 决策 | 结论 |
|---|---|
| 生成路径 | **只保留结构化输出**（with_structured_output + Pydantic），删文本路径、降级、json-repair |
| 模型不支持 function calling | failover 跳过（`supports_structured_output` 分流），全不支持 → error |
| JSON 解析 | 只用 Pydantic（`extra="forbid"`），删 json-repair |
| 失败处理 | Pydantic 失败 → 重试(≤3) → error；业务规则失败 → 重试 → 半成品 |
| 增量修改 | prompt 传完整基线 + 基线节点保留校验（依赖 LLM 完整返回，接受局限） |
| 版本管理 | 前端管（sessionStorage），按对话轮次；AI 只识别回退意图返回指令 |
| 意图 | 前端按钮固定 design_type；判别只做 design/clarification/rollback/reset |

## 1. 核心链路

```
用户输入 + 基线（含用户手动修改）
  │
  ▼ 阶段1 意图判别（1 次轻量 LLM，结构化输出）
      kind: design / clarification / rollback / reset
      ├─ clarification → 引导话术，结束（不预取、不生成）
      ├─ rollback → 返回回退指令给前端，结束
      ├─ reset → 清空，结束
      └─ design → 继续
  │
  ▼ 阶段2a 预取轻量摘要（Python 确定性，按 design_type）
  │
  ▼ 阶段2b 结构化生成（1 次 LLM，with_structured_output + Pydantic schema）
  │
  ▼ 校验层（结构规则 + 基线保留）
  │
  ▼ format → 半成品安全化修复 → SSE done
```

## 2. 模型能力分流（取代运行时"降级"）

```
模型配置 supports_structured_output: bool
  ├─ true  → 参与生成（结构化输出）
  └─ false → failover 跳过
```

- vllm 1.5B 标 `false`，qwen/deepseek 标 `true`
- 所有模型都不支持 → error（"当前配置的模型不支持结构化输出"）
- **运行时只有重试，没有降级**——降级是配置层选路，重试是运行时多试，不在一个层面

## 3. DESIGN_SPEC 三份差异配置

```python
DESIGN_SPEC = {
    "flow_design": {
        "prefetch": ["categories", "forms", "roles", "models"],
        "schema": FlowDesign,
        "validators": [NodeValidator, EdgeValidator, BPMNXMLValidator],
        "format": format_flow,          # 生成 bpmn_xml
        "baseline": ["nodes", "edges"],
    },
    "form_design": {
        "prefetch": ["forms"],
        "schema": FormDesign,
        "validators": [FormFieldValidator],
        "format": format_form,          # transform_to_vform3
        "baseline": ["widgetList", "formConfig"],
    },
    "category_design": {
        "prefetch": ["categories"],
        "schema": CategoryDesign,
        "validators": [CategoryValidator],
        "format": format_category,
        "baseline": ["category_name", "code", "remark"],
    },
}
```

主链路一份，读 `spec = DESIGN_SPEC[design_type]` 决定每步行为。

## 4. 意图判别

```python
class Intent(BaseModel):
    kind: Literal["design", "clarification", "rollback", "reset"]
    target: str | None = None   # rollback: "start" / "prev"
```

| 场景 | 处理 |
|---|---|
| 有基线 + 指令（"改成总监"） | design |
| 无基线 + 指令（"设计请假流程"） | design |
| 无意义（"你好"） | clarification |
| "回到一开始/上一步" | rollback（target 由版本列表摘要消歧） |
| "清空重来" | reset |
| 判别失败 | 默认 design |
| 误分类 | prompt 倾向"拿不准就判 design" |

## 5. 预取轻量摘要

| 类别 | 摘要字段 |
|---|---|
| categories | `{categoryId, categoryName, code}` |
| forms | `{formId, formName, formKey}` |
| roles | `{name, key}` |
| models | `{modelId, modelName, modelKey}` |

- 截断 50 条；空列表 prompt 标注"留空"；失败置空 + done 附 warning
- 预取的是"标识字段"，完整对象（VForm3、bpmn_xml）不取

## 6. 结构化生成（唯一路径）

```python
obj = llm.with_structured_output(spec.schema).invoke(prompt)
# 失败 → 重试(≤3，反馈 Pydantic 的具体错误) → 耗尽 → error
```

- schema 用 Pydantic，`extra="forbid"`（= additionalProperties:false）
- with_structured_output 失败 = LLM 没返回合法 function call，抛异常
- 结构化输出是"概率遵守"非"保证"，靠重试 + error 兜底

## 7. 增量修改

- **prompt 传完整基线**（nodes/edges 完整 JSON，不是节点名）
- **完整返回**：LLM 返回完整 nodes+edges，prompt 强调"逐字保留未提及内容"
- **基线保留校验**：基线 id - 输出 id，被删且指令无"删/去掉/移除"关键词 → 拦截重试
- 局限（已接受）：依赖 LLM 完整返回，丢了靠校验兜底 + 前端草稿

## 8. 基线 vs 版本管理

### 基线
- 增量修改的**输入** = 当前设计产物状态（含用户手动修改）
- 谁管：前端（设计器是唯一真相）
- 每轮对话：前端传 current_form_data → 后端拼 prompt → LLM 增量 → 新状态成为新基线

### 版本历史
- 基线的**时间序列**，用于回退
- 谁管：前端 sessionStorage，最近 20 个
- 粒度：**对话轮次**（每轮结束存一个版本）

### 关系与分叉

| 时刻 | 基线变吗 | 版本历史变吗 |
|---|---|---|
| AI 生成 done | ✅ 变 | ✅ append |
| 用户手动改 | ✅ 变 | ❌ 不变 |
| 回退 | ✅ 变（恢复目标版本） | ❌ 不变 |

- 版本历史只存"AI 生成结果"，用户手动修改合并进下一轮基线
- 回退语义：回到"AI 的某个生成版本"（v0/v1），不含手动修改中间态
- 回退执行：AI 下指令，前端恢复；checkpoint（对话历史）不回

## 9. 校验层 + 半成品

- 校验层：现有 30+ 条结构规则 + 基线保留校验
- 半成品安全化修复：**只删不补**（删非法连线/自环/孤立节点），修复后**再跑一遍校验**确认合法
- 半成品 = "结构合法能导入的草稿"，业务细节（审批人/表单/条件）用户补

## 10. 失败处理（四个出口）

```
结构化输出失败   → 重试(≤3) → 耗尽 → 【error】       （无可用产物，系统问题）
业务规则失败     → 重试(≤3) → 耗尽/死循环 → 【半成品】  （有产物，给草稿）
模型全挂         → failover → 全挂 → 【error】
需求不明         → 【clarification】                  （用户问题）
通过             → 【成功】
```

- 格式失败不甩锅用户（error，不是 clarification）
- 重试反馈 Pydantic 的**具体错误**（"type 字段输出 ROBOT_TASK 不在枚举"），非笼统

## 11. 细粒度提交划分（7 个 commit）

### Phase 1：增量修改（低风险，独立）

**Commit 1** — `feat: prompt 传完整基线 + 基线节点保留校验`
- builder.py 改完整基线；新增 baseline_validator；加测试

**Commit 2** — `feat: 前端版本历史 + 回退指令`
- AiDesignDialog 维护版本历史；后端判别 rollback 后前端恢复

### Phase 2：结构化输出（主路径）

**Commit 3** — `feat: 定义 Pydantic 设计 schema`
- pydantic_models.py（Flow/Form/Category）；加测试

**Commit 4** — `feat: 意图判别（design/clarification/rollback/reset）`
- 判别 schema + discriminate_intent()；加测试

**Commit 5** — `feat: DESIGN_SPEC + 预取摘要 + 模型能力分流`
- DESIGN_SPEC；预取摘要函数；ModelManager 加 supports_structured_output；加测试

**Commit 6** — `feat: 结构化生成主路径（with_structured_output）`
- run_react_agent 改用 with_structured_output；现状 ReAct 暂留；加测试

**Commit 7** — `refactor: 删 ReAct + json-repair`
- 删 create_react_agent、_parse_json_response、_fix_json_string_quotes、json-repair 依赖

### 依赖关系

```
Commit 1 ─┐
Commit 2 ─┼─ Phase 1 独立
Commit 3 ─┤
Commit 4 ─┼─ Phase 2 独立基础
Commit 5 ─┘（依赖 3）
Commit 6 ─── 依赖 3/4/5
Commit 7 ─── 依赖 6
```

## 12. 明确不做

- ❌ 文本降级路径、json-repair（只保留结构化）
- ❌ 部署闭环（生成的是模型，不是部署）
- ❌ 审批意见生成
- ❌ AI 意图识别（前端按钮固定 design_type）
- ❌ 改动集 + 前端 merge（依赖 LLM 完整返回 + 校验兜底，接受局限）
- ❌ 字段级 diff 校验（误报高，靠 prompt + 前端草稿）

## 13. 实施进度

| Commit | 内容 | 状态 |
|---|---|---|
| 1 | prompt 完整基线 + 基线节点保留校验 | ✅ 已实施（含 review 修复：nodes 分支优先于 bpmn_xml） |
| 2 | 前端版本历史 + 回退指令 | ✅ 已实施（含 reset 处理 + clearMessages 清版本） |
| 3 | Pydantic 设计 schema | ✅ 已实施 |
| 4 | 意图判别 | ✅ 已实施（含 review 修复：接入 react_agent_node） |
| 5 | DESIGN_SPEC + 预取摘要 + 模型能力分流 | ✅ 已实施 |
| 6 | 结构化生成主路径 | ✅ 已实施（含 review 修复：basic 模式走 legacy、异常元组加宽） |
| 7 | 删 ReAct + json-repair | ⏳ 待结构化输出真实 LLM 验证稳定后 |

**review 发现的遗留问题（未修，记录在案）**：
- BaselineValidator 只校验 flow_design 的 nodes 删除，form/category 基线保留未覆盖，edges 删除未校验
- 前端 versionKey 不含流程标识（sessionId 为空时不同流程共用版本库）
- rollbackTo('prev') 无游标，连续回退不会逐级回退
- 预取失败与结构化失败在同一 try 块（预取失败会误降级 ReAct）
