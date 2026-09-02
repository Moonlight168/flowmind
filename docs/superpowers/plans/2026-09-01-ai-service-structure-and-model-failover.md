# AI 服务目录重构与模型链路降级优化方案

> 状态：已实施并完成 review，待推送
> 日期：2026-09-01
> 范围：仅 `flowmind-ai-flow/ai-service`
> 基线：`dev` 分支 `54283cf`

## 1. 目标与边界

本次改造同时解决两个问题：

1. 让 AI 服务目录按业务职责和外部集成归类，减少 `adapters/`、`agents/`、`utils/` 等含义过宽目录造成的定位成本。
2. 将模型选择、运行时故障识别、Provider 切换、重试配置、流式输出安全策略和 Langfuse 尝试记录集中到一个深模块，确保聊天、意图识别、历史压缩和设计 ReAct 使用一致的降级规则。

保持以下对外契约不变：

- FastAPI 现有聊天、设计和健康检查路径。
- 聊天 SSE 仍为 `meta -> delta* -> done|error`。
- 设计 SSE 的事件格式、`thread_id`、checkpoint 和业务兜底文案。
- Prompt Markdown、黄金数据集及 Langfuse 根观测的既有行为。

本次不改前端目录和页面。后端保持 SSE 契约后，已完成流式消费改造的前端无需同步修改。

## 2. 当前问题与证据

### 2.1 模型降级只覆盖部分链路

- `ModelManager.create_llm_with_provider()` 只在构造 `ChatOpenAI` 时遍历候选模型。真实的网络、超时、限流和鉴权错误通常出现在 `invoke()` 或 `stream()`，因此该循环无法处理主要故障。
- 聊天、意图识别和历史压缩均只取一个模型调用一次；失败后进入业务兜底，没有尝试备用 Provider。
- 只有 `run_react_agent()` 自己维护 `failed_providers`，能在运行时故障后切换 Provider，导致策略散落在调用方。
- 最小复现中，首选模型在 `invoke()` 抛错后的调用序列为 `['primary']`，没有执行 `fallback`；现有 ReAct 专用降级单测通过，证明问题边界是“局部实现、整体缺失”。

### 2.2 配置已声明但不生效

- `FallbackSettings.enabled/max_retries/retry_interval` 被传入 `ModelManagerConfig`，但运行路径没有读取这些值。
- ReAct 使用硬编码的三次结构化重试；Provider 降级次数与结构化结果重试混为一谈。
- 当前示例配置只有 `qwen` 声明支持结构化输出，`vllm` 会被能力过滤，所以设计链没有真正的结构化备用模型。

### 2.3 目录和命名掩盖真实职责

- `adapters/` 同时放置 LLM 生命周期策略和后端 HTTP 调用，两者变化原因不同。
- `agents/` 同时包含生成器、意图判别、历史压缩、工具和确定性校验器；其中多数不是 Agent。
- `utils/` 中的 BPMN/VForm3 文件各自承载明确且较深的设计领域逻辑，不是通用工具。
- `graph/workflows/`、`graph/state/` 都只有少量文件，层级收益低。
- `BackendService`、`CategoryService` 等名称实际是 HTTP 客户端，`Service` 容易被误解为业务模块。

### 2.4 模型管理接口包含遗留断链

- `api/model_config.py` 调用 `ModelFactory.get_all_adapters/create_adapter/add_adapter/remove_adapter/update_priority/update_fallback_config`，当前工厂没有这些方法。
- `api/health.py` 调用 `ModelManager.get_available_adapters_info/get_current_adapter`，当前管理器也没有这些方法。
- 仓库内没有 `/models` 动态配置接口调用方；前端 AI 配置页目前只写入浏览器 `localStorage`。

## 3. 设计原则

- `llm` 是深模块：调用方只表达任务、能力和一次模型操作，Provider 选择、缓存、降级、日志和观测都留在模块内部。
- `integrations/backend` 明确表示外部 Java 后端集成；其中对象使用 `Client` 命名，不伪装成业务模块。
- 不新增只有一个实现的 Protocol、Repository 或 Adapter 基类。测试通过注入可调用对象或假模型跨越同一个 seam。
- 先修复运行时行为，再做机械移动；不在同一提交里混合逻辑修改和大规模重命名。
- 业务兜底与模型降级分离：模型模块负责尽量取得结果，节点装饰器只在候选模型耗尽后生成稳定用户输出。

## 4. 目录预览

### 4.1 调整前

```text
app/
├── adapters/
│   ├── factory.py
│   ├── model_manager.py
│   ├── base/errors.py
│   └── backend/{base,category,flow,form,role}.py
├── agents/
│   ├── react_agent.py
│   ├── intent.py
│   ├── compression.py
│   ├── design_spec.py
│   ├── tools.py
│   └── validators/
├── graph/
│   ├── workflows/{chat_workflow,design_workflow}.py
│   ├── state/app_state.py
│   └── nodes/{base,chat_node,react_agent_node,review_node,format_node}.py
├── core/checkpoint/
├── domain/{dto,schemas}/
├── infra/
└── utils/{auth,bpmn_generator,bpmn_validator,vform3_transformer}.py
```

### 4.2 调整后

```text
app/
├── api/                         # FastAPI 路由与认证依赖
├── config/                      # 环境配置和任务参数
├── core/                        # 认证上下文、通用异常
│   ├── auth.py
│   ├── auth_context.py
│   └── exceptions.py
├── domain/
│   ├── dto/
│   └── design_models.py         # 设计结构化输出模型
├── llm/                         # 统一模型运行时深模块
│   ├── __init__.py
│   └── runtime.py
├── integrations/
│   └── backend/                 # Java 后端 HTTP 客户端
│       ├── client.py
│       ├── categories.py
│       ├── flow_models.py
│       ├── forms.py
│       ├── roles.py
│       └── request_cache.py
├── design/                      # 流程设计领域逻辑
│   ├── generation.py
│   ├── intent.py
│   ├── history.py
│   ├── spec.py
│   ├── tools.py
│   ├── bpmn_generator.py
│   ├── bpmn_validator.py
│   ├── vform3_transformer.py
│   └── validators/
├── graph/
│   ├── chat_graph.py
│   ├── design_graph.py
│   ├── state.py
│   └── nodes/{base,chat,generate,review,finalize}.py
├── infra/
│   ├── checkpoint/redis.py
│   ├── logger/
│   ├── nacos.py
│   └── observability.py
├── prompts/
├── evaluation/
└── main.py
```

### 4.3 主要文件映射

| 当前文件 | 目标文件 | 原因 |
|---|---|---|
| `adapters/model_manager.py` | `llm/runtime.py` | 从“创建模型”升级为统一执行与降级模块 |
| `adapters/factory.py` | 合并进 `llm/runtime.py` | 当前工厂只是全局单例包装，删除浅层转发 |
| `adapters/backend/base.py` | `integrations/backend/client.py` | 明确为 HTTP 客户端 |
| `adapters/backend/category.py` | `integrations/backend/categories.py` | 文件名与资源集合一致，类改为 `CategoryClient` |
| `adapters/backend/flow.py` | `integrations/backend/flow_models.py` | 避免与 LangGraph flow 混淆 |
| `adapters/backend/form.py` | `integrations/backend/forms.py` | 类改为 `FormClient` |
| `adapters/backend/role.py` | `integrations/backend/roles.py` | 类改为 `RoleClient` |
| `agents/react_agent.py` | `design/generation.py` | 它负责设计生成，不是通用 Agent 容器 |
| `agents/compression.py` | `design/history.py` | 明确为设计对话历史处理 |
| `agents/design_spec.py` | `design/spec.py` | 去除重复名称 |
| `agents/validators/` | `design/validators/` | 校验属于设计领域 |
| `utils/bpmn_*` | `design/bpmn_*` | 深领域逻辑移出通用工具目录 |
| `utils/vform3_transformer.py` | `design/vform3_transformer.py` | 深领域逻辑移出通用工具目录 |
| `core/checkpoint/redis_checkpoint.py` | `infra/checkpoint/redis.py` | Redis checkpoint 是基础设施实现 |
| `graph/nodes/react_agent_node.py` | `graph/nodes/generate.py` | 按节点实际职责命名 |
| `graph/nodes/format_node.py` | `graph/nodes/finalize.py` | 该节点负责安全化、转换和最终输出，不只是格式化 |

`adapters/` 在架构术语中本应表示“在 seam 上满足某个 interface 的具体实现”。当前目录没有对应的统一 interface，而且混放两类职责，因此直接改为具体的 `llm/` 与 `integrations/`，比继续扩充 `adapters/` 更容易理解。

## 5. 统一模型运行时

### 5.1 外部 interface

建议 `ModelRuntime` 只暴露三个入口：

```python
runtime.execute(task_name, operation, *, structured=False)
runtime.stream(task_name, messages, *, config=None)
runtime.describe_providers()
```

- `execute`：调用方提供一次基于模型的操作；适用于普通聊天、意图、压缩和需要按 Provider 重建的 ReAct Agent。
- `stream`：显式管理聊天 token 流，保证流式降级不会重复输出。
- `describe_providers`：为健康检查提供脱敏后的配置与能力信息，不再维护跨请求共享的“当前 Provider”。

`ModelExhaustedError` 可直接定义在 `runtime.py`，暂不为一个异常新增单独文件。

### 5.2 候选选择

1. 按 `MODEL_PRIORITY` 排序。
2. 过滤不存在或配置无效的 Provider。
3. 结构化任务过滤 `supports_structured_output=false` 的 Provider。
4. `fallback.enabled=false` 时只保留第一个候选。
5. 每个 Provider 在一次业务调用中最多执行一次基础设施尝试；失败后进入下一个 Provider。
6. `fallback.max_retries` 明确定义为“首选模型之外允许的额外 Provider 尝试数”，并受候选数量上限约束。
7. `fallback.retry_interval` 在 Provider 切换前生效；建议生产默认值根据延迟目标评估，测试中设为 `0`。

不在首期增加熔断器、后台健康探测或自动恢复状态。只有 Langfuse 数据证明故障 Provider 持续拖慢大量请求时再增加。

### 5.3 错误分类

| 错误类型 | 处理 |
|---|---|
| 连接失败、超时、OpenAI SDK 网络错误、HTTP 429/5xx | 标记本次 Provider 失败并切换下一个 |
| HTTP 401/403、配置缺失 | 当前 Provider 不可用并切换；日志不得包含密钥 |
| Pydantic/结构化内容不合法 | 不视为 Provider 宕机，交给设计生成语义重试 |
| 业务校验不通过 | 继续现有 review 反馈重试，不切换 Provider |
| 所有候选耗尽 | 抛 `ModelExhaustedError`，由节点业务兜底处理 |
| `GraphInterrupt` | 原样传播，任何层都不得吞掉 |

Provider 降级预算与结构化内容重试预算必须分开命名、分开计数、分别写入 Langfuse。

### 5.4 各链路最终行为

| 链路 | Provider 降级 | 候选耗尽后的业务兜底 |
|---|---|---|
| 同步聊天 | 运行时失败后切换备用模型 | 返回现有聊天友好文案 |
| 流式聊天 | 首个 token 之前失败可切换；首个 token 之后失败禁止重放 | 发送 `error` 终止事件，已输出内容不重复 |
| 意图识别 | 运行时失败后切换支持结构化输出的模型 | 默认 `design` |
| 历史压缩 | 运行时失败后切换备用模型 | 回退确定性裁剪 |
| ReAct 设计 | 运行时失败后按能力过滤切换，并为每个 Provider 重建 Agent | 返回现有设计错误契约 |
| review 业务校验 | 不切 Provider，按具体校验反馈重试 | 安全半成品或现有错误出口 |

### 5.5 流式输出策略

聊天流式链路应改为显式调用 `ModelRuntime.stream()`，由节点累积最终文本并写入 checkpoint，通过 LangGraph `custom + updates` 模式向 SSE 层发送 token：

```text
Provider A 建连失败、尚未输出 token
  -> Provider B -> delta* -> done

Provider A 已输出 delta 后中断
  -> 不切换、不重放 -> error
```

这条规则避免用户看到 Provider A 的半段内容后又收到 Provider B 从头生成的重复文本。对外 SSE 事件名和前端处理保持不变。

## 6. Langfuse 与黄金数据集

每次模型尝试应处在现有 Workflow 根 observation 下，并记录：

- `task_name`
- `provider`
- `attempt_index`
- `fallback_enabled`
- `structured_required`
- `failure_category`
- `token_started`（流式链路）
- 最终是否由备用 Provider 成功

禁止记录 API Key；异常信息需要脱敏。Langfuse 自身失败继续按现有策略隔离，不影响模型调用。

黄金数据集继续评估稳定业务契约：成功设计、意图、结构、业务兜底文案。Provider 切换属于确定性基础设施行为，主要由 fake Provider 单元/集成测试覆盖，不依赖真实模型制造故障。候选耗尽场景继续通过 `fallback_contract` 分数写入 Langfuse。

## 7. 遗留模型接口处理

推荐删除未被调用且已经失效的 `api/model_config.py` 以及 `main.py` 中对应 router 注册，不补回一套仅存在内存、重启即丢失的动态配置功能。

保留并修复 `GET /health/models`：改用 `runtime.describe_providers()`，只报告已配置 Provider、优先级和能力，不把“配置存在”冒充为真实在线状态。如果后续确实需要后台动态配置，应单独设计持久化、密钥加密、权限、审计和多进程同步，不在本次重构中临时恢复。

## 8. 分阶段实施

### Phase 1：先建立行为安全网

- 新增 `ModelRuntime` interface 测试，复现聊天运行时失败不切换的问题。
- 覆盖 fallback 关闭、候选能力过滤、最大额外尝试数、候选耗尽和错误分类。
- 补齐流式“首 token 前切换、首 token 后不重放”测试。
- 保留现有 ReAct 降级测试作为迁移基线。

### Phase 2：实现统一运行时并迁移调用方

- 在原目录结构下先实现 `ModelRuntime.execute/stream`。
- 依次迁移聊天、意图、压缩、ReAct；删除调用方自己的 Provider 排除集。
- 让 fallback 配置真正生效并区分 Provider 尝试与结构化语义重试。
- 给每次尝试补齐 Langfuse 元数据。

### Phase 3：收口流式链路

- 聊天节点改用显式 `runtime.stream()`。
- LangGraph 改用 `custom + updates` 输出 token 和最终状态。
- 验证断流、客户端取消、checkpoint、Langfuse output 和 SSE 精确一次语义。

### Phase 4：机械目录重构

- 按映射表移动/重命名文件并更新 import。
- 删除空的 `adapters/`、`agents/`、`utils/` 和无收益的单文件子目录。
- 只做命名和移动，不夹带业务逻辑调整。

### Phase 5：清理遗留接口和文档

- 删除失效且无调用方的动态模型配置 router。
- 修复 `/health/models`。
- 更新 `.env.example`、README、`private/项目介绍.md`、`private/面试问答.md` 和本方案状态。
- 明确生产环境至少配置两个支持结构化输出的 Provider，否则设计链只能重试、不能降级。

## 9. 验收标准

- 首选模型在运行时连接失败时，聊天、意图、压缩、设计均按能力切换到备用 Provider。
- `FALLBACK_ENABLED=false` 时不会调用第二个 Provider。
- `FALLBACK_MAX_RETRIES` 和 `FALLBACK_RETRY_INTERVAL` 有可重复测试证明生效。
- 结构化任务永远不会选择明确声明不支持结构化输出的模型。
- 流式首 token 前故障可无感切换，首 token 后故障不会产生重复内容。
- 候选耗尽后仍返回既有业务兜底契约，`GraphInterrupt` 不被捕获。
- Langfuse 能在同一根链路看到每次 Provider 尝试、失败分类和最终选中 Provider。
- 黄金数据集全量执行通过，兜底契约分数成功写入 Langfuse。
- `/health/models` 正常响应且不暴露密钥；失效 `/models` router 已移除。
- Ruff、AI 服务 unit/integration 测试通过；前端 SSE 定向测试和生产构建通过，以确认契约未破坏。
- 重构后 `app/adapters`、`app/agents`、`app/utils` 不再存在，仓库中没有旧 import。

## 10. 建议提交拆分

1. `test: 补充模型运行时降级回归测试`
2. `refactor: 统一模型执行与降级策略`
3. `fix: 完善聊天流式模型降级`
4. `refactor: 调整 AI 服务目录与文件命名`
5. `refactor: 清理失效模型配置接口`
6. `docs: 更新 AI 服务架构与模型降级说明`

每个提交单独通过定向测试；全部完成后再运行完整测试、黄金数据集、前端流式测试和生产构建。未经用户再次明确要求，不提交或推送本方案及后续实现。

## 11. 明确不做

- 不引入新的第三方重试库，使用现有 Python/LangChain 能力即可。
- 不新增形式化 ports/repositories 层或只有一个生产实现的抽象。
- 不在本次实现动态密钥管理后台。
- 不伪造第二个结构化模型能力；部署配置必须反映 Provider 的真实能力。
- 不在已输出 token 后自动从备用模型重放内容。
- 不改 Java 服务和前端业务目录。

## 12. 实施结果（2026-09-02）

- 已新增 `app/llm/runtime.py`，统一 `execute/stream/describe_providers`，聊天、意图、压缩和 ReAct 均迁移完成。
- fallback 开关、额外 Provider 尝试数、切换间隔和结构化能力过滤均已生效并有测试覆盖。
- 流式聊天改为 `custom + updates`：首 token 前可切换，首 token 后用 `PartialStreamError` 终止，SSE 契约不变。
- Langfuse 为每次 Provider 尝试记录任务、Provider、序号、结构化/流式标记、成功状态、失败分类和 token_started。
- 已完成 `design/`、`llm/`、`integrations/backend/`、扁平 `graph/`、`infra/checkpoint/` 等目录迁移，删除旧 `adapters/agents/utils` 源文件。
- 已删除失效且无调用方的动态 `/models` router，`/health/models` 改为输出脱敏 Provider 配置和能力。
- 验证：Ruff 通过；单元与集成测试合计 107 项通过。黄金数据集真实执行仍需要环境提供认证令牌和 Langfuse 密钥。
