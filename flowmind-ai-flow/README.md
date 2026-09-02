# FlowMind AI 服务

基于 FastAPI + LangGraph 的智能流程设计服务，支持 AI 自动生成 Flowable 流程分类、流程和表单。

## 核心功能

| 功能                  | 说明                               |
| --------------------- | ---------------------------------- |
| **AI 设计分类** | 自然语言描述自动生成流程分类       |
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
    │   ├── core/                 # JWT 认证解析与异常基类
    │   ├── evaluation/           # 黄金数据集加载与确定性契约评分
    │   ├── infra/                # checkpoint、日志、observability（Langfuse）、Nacos
    │   ├── prompts/              # Markdown 提示词与 versions.json 灰度配置
    │   └── config/               # settings.py 类型化配置
    ├── scripts/run_golden_eval.py # 黄金集评估入口
    ├── evals/                    # golden_dataset.jsonl 用例
    ├── .env.example
    └── pyproject.toml
```

> AI 服务的 Docker Compose 在仓库根目录 `docker/ai-service/docker-compose.yml`（含 vllm + ai-service）。

## 核心 API

| 端点                 | 方法 | 说明            |
| -------------------- | ---- | --------------- |
| `/design/category` | POST | AI 设计流程分类（SSE 流式） |
| `/design/flow`     | POST | AI 设计流程（SSE 流式）     |
| `/design/form`     | POST | AI 设计表单（SSE 流式）     |
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
  "form_data": {
    "flow_name": "请假审批流程",
    "category_id": "leave_approval",
    "bpmn_xml": "<?xml version='1.0'...?>",
    "description": "..."
  },
  "message": "已为您生成【请假审批流程】流程",
  "design_type": "flow",
  "review_passed": true
}
```

## 黄金数据集评估

在 `ai-service` 目录配置 Langfuse 密钥和专用测试账号的 `FLOWMIND_AUTH_TOKEN`，然后执行：

```bash
# 执行全部用例
python -m scripts.run_golden_eval

# 精确执行某一条用例
python -m scripts.run_golden_eval --case-id flow-linear-leave
```

脚本会幂等同步 `evals/golden_dataset.jsonl`，并在 Langfuse Dataset Run 中记录真实工作流链路、输出和契约评分。单条运行失败会转换为可评分的兜底结果，不中断同批其他用例。

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

**文档更新日期**: 2026-09-02
