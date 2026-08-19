# AGENTS.md

FlowMind 智能流程审批系统 —— AI 助手的项目级约定。详见 `CLAUDE.md`（代码规范、命令、架构）。

## 私人文档约定（重要）

`private/` 目录存放个人文档，**不进 git**（已在 `.gitignore`）：

- `private/项目介绍.md` —— 项目定位、架构、整体链路、关键技术点
- `private/面试问答.md` —— 口语化、简洁的面试题 + 必须答出的答案

**规则：每次代码变更后，必须同步更新 `private/` 中对应的文档。**

- 架构 / 链路 / 技术点变化 → 更新 `项目介绍.md`
- 新增功能 / 改动（尤其是面试可能问到的）→ 更新 `面试问答.md`
- 文档风格：项目介绍"让人一看就懂"；面试问答"口语化、简洁、真实面试题"
- 本次改动若只是修复 bug 不改变对外行为，可只更新关键设计表格，不必重写

## 快速定位

| 目录 | 内容 |
|---|---|
| `flowmind-ai-flow/ai-service` | Python AI 服务（FastAPI + LangGraph），核心：`app/graph/`（工作流）、`app/agents/`（agent + 校验层 + 压缩） |
| `flowmind-cloud` | Java 微服务（Spring Cloud + Flowable），核心：`ruoyi-modules/ruoyi-flowable` |
| `flowmind-ui` | Vue 3 前端，核心：`src/components/AiDesignDialog`、`src/components/ProcessDesigner` |
| `docs/superpowers/` | 设计规格、实施计划存档（进 git） |
| `private/` | 个人文档（不进 git） |
