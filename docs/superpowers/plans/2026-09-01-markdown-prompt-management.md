# Markdown 提示词统一管理实施记录

## 目标

将散落在 Python 常量和业务节点中的提示词正文统一迁移到 Markdown 文档，使提示词可独立阅读、审查和修改，同时保持现有 Agent 调用链行为不变。

## 实现

- `app/prompts/` 按 `roles`、`tasks`、`skills`、`agents`、`tools`、`shared` 分层保存 Markdown 提示词。
- 新增统一加载器 `load_prompt` 和 `render_prompt`；读取结果缓存于进程内，避免每次模型调用重复访问磁盘。
- 模板只替换显式命名变量，不使用 Python `format`，确保 JSON 示例和 `${initiator}` 等 BPMN 表达式原样保留。
- 任务配置直接声明 Markdown 路径，移除通过 Python 模块动态导入 `TASK` 常量的链路。
- 意图识别、对话、历史压缩、校验纠错、ReAct 工具描述、角色、任务和 BPMN 领域知识均通过同一加载器读取。

## 验证

- 单元测试覆盖全部任务文档可读、变量替换安全和四层设计提示词组装。
- 扫描 AI 服务 Python 源码，确认不再包含业务提示词正文。
- Ruff、AI 服务单元与集成测试全部通过后提交。
