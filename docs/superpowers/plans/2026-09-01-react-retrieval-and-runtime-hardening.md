# ReAct 检索与运行链路加固

> 状态：已实施并完成 review
> 日期：2026-09-01
> 基线：`v2.0.0` 之后的 `dev` 分支
> 取代：`2026-08-19-structured-output-redesign.md` 中“确定性全量预取、删除 ReAct”的生成决策

## 目标

- 设计阶段通过 ReAct 按需查询分类、表单、角色和已有流程，避免把最多 50 条全量摘要塞入 prompt。
- ReAct 最终仍使用 Pydantic `response_format`，不恢复自由文本 JSON 或 json-repair。
- 修复模型运行时故障不 failover、对话清理 thread_id 不一致、请求缓存串请求、锁误删和不安全半成品等链路问题。

## 最终链路

```
intent → ReAct(search_* 按需检索) → structured_response
       → review(共享请求缓存) → format → SSE done
```

- `DESIGN_SPEC` 为每种设计声明 schema 与可调用工具。
- 同一次请求内，工具和 review 复用相同后端查询缓存；调用结束显式清理 `ContextVar`。
- provider 运行时连接/超时错误会加入排除集，下一次重试选择下一个支持结构化输出的 provider。
- 同一 thread 使用带随机 ownership token 的 Redis 锁；释放时通过 compare-and-delete，避免旧请求删除新锁。
- 半成品仅做删除式修复：移除坏引用、自环、条件语义冲突连线和不可达节点；重新生成 BPMN 并通过校验后才标为可导入。
- 前端创建与删除会话统一传同一个 `flowKey` 作为 `thread_id`。

## 验证

- AI 服务：Ruff、unit、integration 测试。
- 前端：生产构建。
- 新增回归覆盖：provider failover、请求缓存隔离、半成品安全化、正确 thread_id 清理。
