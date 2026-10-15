# FlowMind AI 服务

基于 FastAPI + LangGraph 的智能流程设计服务，支持 AI 自动生成 Flowable 流程分类、流程和表单。


## 核心功能

| 功能                  | 说明                               |
| --------------------- | ---------------------------------- |
| **AI 设计分类** | 自然语言描述自动生成流程分类       |
| **AI 基本信息** | 自动生成流程名称、分类与业务描述   |
| **AI 设计流程** | 自动生成 BPMN 2.0 流程结构         |
| **AI 设计表单** | 自动生成 v-form-designer 表单 JSON |
| **多轮对话**    | LangGraph 工作流持续优化设计       |
| **SSE 流式**    | 设计接口以 SSE 推送节点级进度，done 事件带最终结果 |
| **逐 token 输出** | 对话 `/chat/stream` 逐 token 流式返回并保留 LangGraph 状态 |
| **多模型支持**  | OpenAI 兼容接口 + 运行时降级      |
| **黄金集评估**  | 全量/单条执行并上报 Langfuse     |
| **提示词灰度**  | Markdown 版本管理、同会话稳定分流与快速回滚 |

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端层 (flowmind-ui)                      │
│                    Vue 3 + Element Plus                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP
┌─────────────────────────────────────────────────────────────────┐
│                     API 层 (FastAPI)                             │
│              /design/*, /chat 等端点                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph 工作流层 (graph/)                    │
│  design → review → format                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 设计领域与模型运行时                             │
│  design/: 生成、意图、压缩、校验、BPMN/VForm3                   │
│  llm/: Provider 能力过滤、运行时降级、流式安全策略               │
│  integrations/backend/: Java 后端 HTTP Client                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    基础设施层 (Redis / 日志)                      │
└─────────────────────────────────────────────────────────────────┘
```

## 技术栈

| 技术        | 说明                   |
| ----------- | ---------------------- |
| FastAPI     | 高性能 Python Web 框架 |
| LangChain   | LLM 应用开发框架       |
| LangGraph   | 基于图的工作流引擎     |
| Redis       | 会话状态持久化         |
| Python 3.12 | 编程语言               |

## 目录结构

```
flowmind-ai-flow/
└── ai-service/
    ├── app/
    │   ├── main.py               # FastAPI 入口
    │   ├── api/                  # API 路由：design/chat/health（SSE 流式）
    │   ├── graph/                # chat_graph、design_graph、节点与状态
    │   ├── design/               # ReAct 生成、意图、压缩、校验器和 BPMN/VForm3 结果转换
    │   ├── llm/                  # 统一模型运行时与 Provider 降级
    │   ├── integrations/backend/ # Java 后端 HTTP Client
    │   ├── domain/               # DTO 与结构化设计模型
    │   ├── core/                 # 网关用户上下文与异常基类
    │   ├── evaluation/           # 黄金数据集加载与确定性契约评分
    │   ├── infra/                # checkpoint、日志、observability（Langfuse）、Nacos
    │   ├── prompts/              # Markdown 提示词与 versions.json 灰度配置
    │   └── config/               # settings.py 类型化配置
    ├── scripts/run_evaluation.py # 数据集评测入口
    ├── evals/datasets/           # 分类、基本信息、表单、流程模型数据集
    ├── .env.example
    └── pyproject.toml
```

> 开发基础设施（含 FlowMind 独立 Langfuse）位于 `docker/flowmind/docker-compose.yml`；完整 Docker 环境位于同目录的 `docker-compose.prod.yml`。

> AI 服务自身不重复校验 JWT。生产环境仅允许经 Gateway 的 `/flowmind-ai/**` 路径访问，由网关校验令牌并注入用户身份；AI 容器端口不直接发布到宿主机。

## 核心 API

| 端点                 | 方法 | 说明            |
| -------------------- | ---- | --------------- |
| `/design/category` | POST | AI 设计流程分类（SSE 流式） |
| `/design/flow`     | POST | AI 设计流程（SSE 流式）     |
| `/design/form`     | POST | AI 设计表单（SSE 流式）     |
| `/design/state/{type}` | DELETE | 删除设计会话（含后端 checkpoint） |
| `/design/state/{type}/rollback` | POST | 把会话历史裁剪到指定条数（版本覆盖时丢弃旧分支） |
| `/chat`            | POST | 对话接口（一次性返回）      |
| `/chat/stream`     | POST | 对话接口（SSE 逐 token 流式） |
| `/chat/history`    | GET  | 对话历史                    |
| `/health`          | GET  | 健康检查                    |
| `/health/models`   | GET  | 当前可用模型列表            |

> 设计三接口均以 SSE（`text/event-stream`）先推送节点级进度（生成 → 校验 → 组装），`done` 事件携带最终结果；若校验重试/失败会推送对应进度文案。

## 响应格式

设计接口以 SSE 流返回，下面 JSON 为最终 `done` 事件的载荷：

```json
{
  "status": "ready",
  "form_data": {
    "flow_name": "请假审批流程",
    "category_id": "leave_approval",
    "bpmn_xml": "<?xml version='1.0'...?>",
    "description": "..."
  },
  "message": "流程「请假审批流程」：新增 1 个节点",
  "change_details": [
    {"action": "add", "label": "新增 1 个节点", "detail": "财务审批"}
  ],
  "operations": [{"op": "add_node", "node": {"id": "manager_approve"}}],
  "operation_count": 1,
  "validation": {"passed": true, "errors": []},
  "trace_id": "..."
}
```

`message` 与 `change_details` 由 `app/design/change_report.py` 统一生成，前端直接渲染：`message` 是给人看的一句话摘要（实体 + 名称 + 变更量）；`change_details` 按动作分组，每项拆成 `label`（动作标题，如“新增 6 个字段”）与 `detail`（字段/节点列表），前端分行展示——挤在一行时，长列表折行后很难扫读。`action` 取值 `add` / `update` / `remove` / `move` / `replace`，用于着色。分类设计与流程基本信息只改几个文本字段，仍由前端渲染字段对照，不下发 `change_details`。

`ready` 只表示候选结果已通过语法和业务校验，前端仍需用户点击“应用变更”。整体替换（`replace_form` / `replace_graph`）与增量修改一样走预览确认，没有单独的授权标志；覆盖风险由预览、放弃、版本回退三层兜住。`needs_input` 和 `error` 均不携带可覆盖当前设计的草稿。

## 黄金数据集评估

在 `ai-service` 目录配置 Langfuse 密钥和专用测试账号的 `FLOWMIND_AUTH_TOKEN`，然后执行：

```bash
# 上传全部数据集并执行评测
python -m scripts.upload_dataset all
python -m scripts.run_evaluation all

# 精确执行流程模型数据集中的一条用例
python -m scripts.run_evaluation flow --case-id flow-linear-leave
```

评测按分类、基本信息、表单和流程模型四类设计窗口拆分数据集。每条用例以 `turns` 表示单轮或多轮真实对话；Langfuse 中的 TypeScript 状态评估器检查每轮是否有输出，以及状态是否为 `ready` 或 `needs_input`。单条运行失败会转为可观测的错误结果，不中断其余用例。

## 提示词版本与灰度发布

提示词正文仍统一保存在 `app/prompts/**/*.md`，`app/prompts/versions.json` 只维护稳定版本、版本文件和流量权重。分流使用 `thread_id + 提示词路径` 的稳定哈希，同一会话始终命中同一版本。

新增版本时复制 Markdown 文件并配置权重，例如：

```json
{
  "stable": "v1",
  "versions": {
    "v1": {"file": "agents/chat.md", "weight": 95},
    "v2": {"file": "agents/chat.v2.md", "weight": 5}
  }
}
```

实际命中的 `version/cohort` 会写入 Langfuse 的 `prompt_versions` metadata。所有功能开关统一由 `.env` 管理；开启灰度或强制回滚后重启 AI 服务即可生效：

```bash
PROMPT_ROLLOUT_ENABLED=true
PROMPT_VERSION_OVERRIDES={"agents/chat.md":"v1"}
```

其他功能同样通过 `.env` 控制，包括 `LANGFUSE_TRACING_ENABLED`、`FALLBACK_ENABLED`、`COMPRESS_ENABLE_LLM_SUMMARY` 和 `NACOS_ENABLED`。业务模块只读取 `app/config/settings.py` 的类型化配置，不直接读取环境变量。

---

**文档更新日期**: 2026-10-14
