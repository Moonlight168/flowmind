# AI 聊天消息流式输出实施记录

## 目标

将全局 AI 助手从“等待完整回复后一次展示”改为 token 级流式输出，同时保留原有 JSON 接口兼容后台模型检测和控制类调用。

## 实现

- 新增 `POST /chat/stream` SSE 接口，事件顺序为 `meta → delta* → done`。
- 聊天 Workflow 使用 LangGraph `messages` 模式获取模型 token，并结合 `updates` 模式取得最终状态，继续由现有 checkpoint 保存完整对话。
- 仅转发 `chat` 节点产生的 `AIMessageChunk`，避免节点最终写入状态的完整 `AIMessage` 被重复输出。
- SSE 响应关闭代理缓冲并禁用缓存；异常通过 `error` 事件返回。
- 前端在首个 token 到达时插入 AI 消息，后续原位追加并自动滚动；`done` 事件用最终文本校准展示内容。
- 提取通用 `postSse` 解析器，聊天和已有设计流共用，支持网络分片、CRLF 分隔、reader 释放和缺失 `done/error` 终止事件的断流检测。

## 兼容性

- 原 `POST /chat` JSON 接口保持不变。
- 后台模型检测、确认/修改/取消调用继续使用原接口。
- 会话 `thread_id`、历史恢复、Langfuse 观测和 Redis checkpoint 行为保持不变。

## 验证

- 后端真实 LangGraph + FakeListChatModel 测试验证 token 确实逐段产生且不会重复。
- SSE API 测试验证 meta、delta、done 顺序及防缓冲响应头。
- 前端 SSE 解析测试覆盖跨网络分片、CRLF 和缺失 `done` 的中断处理。
- AI 服务 Ruff 检查通过，单元与集成测试共 75 项通过。
- 前端 SSE 测试 3 项通过，生产构建通过。
- Standards / Spec 双轴复审均无 blocker 或 warning。
