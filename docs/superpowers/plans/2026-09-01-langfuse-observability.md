# Langfuse 全链路监控实施记录

## 目标

为 AI 服务接入 Langfuse，完整关联设计、对话工作流中的 LangGraph、Agent、LLM 和工具调用，同时保证监控配置缺失或关闭时不影响业务链路。

## 实现

- 新增 `app/infra/observability.py`，集中管理 Langfuse 根观测、属性传播、LangChain 回调和退出刷新。
- `flowmind.design` 覆盖同步设计与 SSE 流式设计，记录输入、最终设计输出、设计类型、模式和流式标识。
- `flowmind.chat` 覆盖普通对话，记录用户输入和最终回复。
- 使用 `session_id=thread_id` 聚合同一会话，使用认证用户 ID 聚合同一用户，并在 metadata 中保留现有 `business_trace_id`，实现业务日志与 Langfuse 互查。
- LangChain CallbackHandler 同时注入顶层 LangGraph 和独立 LLM 调用，使 Workflow、节点、ReAct Agent、模型生成与工具调用形成父子链路。
- 应用关闭时调用 Langfuse `shutdown()`，刷新后台批量队列，减少进程退出时的数据丢失。
- 只有公钥和私钥同时存在且 `LANGFUSE_TRACING_ENABLED` 未关闭时才启用；禁用状态不创建客户端、不发起网络请求。
- 初始化、记录输出或退出刷新异常会记录警告并隔离，监控故障不会中断业务链路。

## 配置

```env
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_BASE_URL=https://cloud.langfuse.com
LANGFUSE_TRACING_ENABLED=true
LANGFUSE_TRACING_ENVIRONMENT=development
```

私有化部署时只需替换 `LANGFUSE_BASE_URL`。密钥只通过环境变量注入，不写入仓库。

设计输入和输出会进入观测数据，生产启用前应按组织的数据分级、保留周期和访问控制要求完成评审；LangChain 子观测同样可能包含 prompt 与模型回复。

## 链路结构

```text
flowmind.design / flowmind.chat
└── LangGraph workflow
    └── graph node
        ├── intent / compression LLM
        ├── ReAct agent
        │   ├── tool call
        │   └── structured-output LLM
        └── chat LLM
```

## 验证状态

- Ruff 格式检查与静态检查：通过。
- 单元测试覆盖禁用降级、属性传播、回调合并、初始化/刷新故障隔离，以及三个实际工作流入口。
- 集成测试：7 项通过。
- 应用模块导入：通过（本地 Redis 认证不匹配时按既有逻辑降级为 MemorySaver）。
- 完整单元与集成测试：71 项通过。
- 依赖声明和锁文件已更新，并补齐现有代码实际使用但此前漏声明的 `langchain-openai`。
