# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

After any task progress or plan change, always update docs/superpowers/ directory with the latest statuses, notes and documentation.

---

## 项目概述

FlowMind 是一个**智能流程审批系统**，采用微服务架构，包含三个主要子项目：

| 项目 | 技术栈 | 端口 | 职责 |
|------|--------|------|------|
| **flowmind-ai-flow**（`ai-service`） | FastAPI + LangChain + LangGraph | 8000 | AI 意图识别、流程设计、表单设计、审批意见生成 |
| **flowmind-cloud** | Spring Cloud + Flowable | 9001/9002/9003/9007（网关/认证/系统/Flowable） | 业务逻辑、Flowable 流程引擎、权限管理 |
| **flowmind-ui** | Vue 3 + TypeScript + Element Plus | 88（dev）/80（prod） | 用户界面、Flowable 流程设计器 |

### 服务通信架构

```
flowmind-ui (dev 88) → flowmind-cloud（网关 9001）→ Flowable 流程引擎
     │                        │
     └────────────────────────┴──→ flowmind-ai-flow (8000，SSE 流式推送进度/token)
```

---

## 常用命令

### AI 服务 (flowmind-ai-flow/ai-service)

```bash
cd flowmind-ai-flow/ai-service

# 安装依赖
poetry install

# 代码格式化 + Lint
ruff check --fix && ruff format

# 运行测试（注意：pyproject 默认 testpaths 指向不存在的 tests/system，请显式传目录）
pytest tests/unit/ tests/integration/

# 单个测试文件（示例）
pytest tests/unit/test_model_runtime.py -v

# Docker 环境（AI 服务 compose 位于仓库根 docker/ai-service）
cd docker/ai-service
docker-compose up -d --build
docker-compose logs -f ai-service
```

### Java 后端 (flowmind-cloud)

```bash
cd flowmind-cloud

# 构建（根目录构建所有模块）
mvn clean package -DskipTests

# 运行（单个模块）
mvn spring-boot:run -pl ruoyi-modules/ruoyi-system

# 运行测试
mvn test -pl ruoyi-modules/ruoyi-flowable
```

### 前端 (flowmind-ui)

```bash
cd flowmind-ui

# 安装依赖
yarn --registry=https://registry.npmmirror.com

# 开发
yarn dev          # 启动开发服务器
yarn build:stage  # 构建测试环境
yarn build:prod   # 构建生产环境

# 测试
yarn test              # Vitest 测试
yarn test:run          # 单次运行
yarn test:coverage     # 覆盖率报告
yarn test:e2e          # E2E 测试
```

---

## 架构设计

### AI 服务 (flowmind-ai-flow/ai-service)

**核心层级**：`api/` → `graph/` → `design/` → `llm/` / `integrations/` → `infra/`

- **graph/**: LangGraph 聊天和设计编排、节点与状态
- **design/**: ReAct 生成、意图、历史压缩、校验器和 BPMN/VForm3 确定性逻辑
- **llm/**: 统一模型运行时，处理 Provider 能力过滤、运行时降级和流式安全策略
- **prompts/**: Markdown 提示词、版本注册表与基于 thread_id 的稳定灰度分流；命中版本写入 Langfuse metadata
- **config/**（`app/config/settings.py`）: `.env` 配置唯一入口，统一承载模型降级、提示词灰度、Langfuse、压缩、校验、Nacos 与评估参数
- **core/**: JWT 认证解析与异常基类（`auth.py`/`auth_context.py`/`exceptions.py`）
- **integrations/backend/**: Java 后端分类、表单、角色和流程模型 HTTP 客户端
- **domain/**: `domain/dto/` 数据传输对象；`domain/design_models.py` 为结构化设计模型
- **evaluation/**: 黄金数据集加载、真实链路执行与确定性契约评分（入口 `scripts/run_golden_eval.py`）
- **infra/**: Redis checkpoint、日志、observability（Langfuse）与 Nacos 封装

**设计模式**：LangGraph 显式编排、统一模型运行时、外部 HTTP Client、确定性校验 Pipeline

### Java 后端 (flowmind-cloud)

**三层架构**：`Controller` → `Service` → `Mapper`

- `ruoyi-modules/ruoyi-flowable/`: Flowable 流程引擎封装（核心）
- `ruoyi-common/`: 公共模块（R、T、异常、日志）
- `ruoyi-gateway/`: Spring Cloud Gateway

**统一响应格式**：`R<T>` `{ code, msg, data }`

### 前端 (flowmind-ui)

- `src/api/workflow/`: 流程相关 API
- `src/views/workflow/`: 流程管理页面
- `src/components/`: 通用组件（含 Flowable 流程设计器）
- `src/package/`: BPMN-JS 流程设计器面板

---

## 代码规范

### Python (flowmind-ai-flow/ai-service)

#### 导入规范
- **禁止使用延迟导入（lazy import）**，所有 import 必须放在文件顶部
- 异常情况：使用 `__getattr__` 或 property getter 的特殊懒加载除外（如 `settings.debug`、`prompts` 模块导出）
- 循环依赖解决方案：创建子模块的 `__init__.py` 导出，打破导入链

- 命名：模块 snake_case，类 PascalCase，函数 snake_case，常量 SNAKE_CASE
- **类型注解强制**，函数 ≤30 行，类 ≤500 行
- 日志用 `from app.infra.logger import logger`，禁止 print
- 异常处理：捕获具体异常，**禁止 `except Exception`**
- 文件头注释块（必须）

### Java (flowmind-cloud)

- 类 PascalCase，方法/变量 camelCase，常量 SNAKE_CASE
- 文件头注释块
- 统一响应 `R.ok()` / `R.fail()`
- 异常处理：抛出 ServiceException，**禁止捕获通用 Exception**
- 日志 `log.info/warn/error`

### TypeScript/Vue (flowmind-ui)

- 组件 PascalCase，组合式函数 use 前缀，类型/接口 PascalCase
- 组件结构：`template` → `script setup` → `style`
- API 响应处理：检查 code === 200，抛出 Error

---

## Git 提交规范

**提交信息必须使用中文**，格式：

```
<类型>: <中文描述>

<可选正文>
```

类型：feat、fix、refactor、docs、test、chore、perf、ci

禁止添加 `Co-Authored-By` 署名。

---

## 环境配置

### 启动顺序

1. Docker Compose 基础环境（MySQL、Redis、Nacos）：`cd docker/cloud && docker-compose up -d`（或直接 `bin/start.bat`）
2. AI 服务：`cd docker/ai-service && docker-compose up -d`
3. Java 后端（本地开发）：`cd flowmind-cloud && bin/run-all.bat`，按 9001（Gateway）→9002（Auth）→9003（System）→9007（Flowable）启动
4. 前端：`cd flowmind-ui && yarn dev`（端口 88）

### 密钥管理

- 禁止硬编码，使用环境变量
- AI 服务配置：`flowmind-ai-flow/ai-service/.env`（从 `.env.example` 复制）

---

## Superpowers 文档位置

`docs/superpowers/` 目录下：
- `plans/`: YYYY-MM-DD-*-implementation.md 实施计划（含状态、决策与 commit 记录）
- `specs/`: YYYY-MM-DD-*-design.md 设计规格
