# 节点日志与兜底返回统一装饰器实施记录

## 目标

统一 LangGraph 节点的执行日志和异常兜底返回，移除聊天节点内重复的异常处理，避免设计节点失败后原样返回旧状态导致错误路由。

## 实现

- 扩展现有 `node_handler`，统一记录节点执行耗时、成功和失败日志。
- 仅捕获模型、网络、Redis、校验及常见数据处理异常；`GraphInterrupt` 原样抛给 LangGraph，不破坏暂停语义。
- 设计节点异常统一写入 `intent=error` 和稳定 `design_output`，由现有路由进入格式化节点。
- 聊天节点异常统一写入稳定 `chat_response`，并追加 AI 消息以保持 checkpoint 对话历史完整。
- `design`、`review`、`format` 和 `chat` 四个节点全部使用统一装饰器；删除节点内重复的完成日志和聊天 try/except。

## 验证

- 单元测试覆盖设计兜底、聊天兜底、成功透传、失败日志和 `GraphInterrupt` 透传。
- Ruff、AI 服务单元与集成测试全部通过后提交。
