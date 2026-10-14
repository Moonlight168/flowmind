# FlowMind：让业务描述直接变成可运行的审批流程

FlowMind 是一个开源的智能流程审批平台，基于 RuoYi-Cloud、Flowable 与 Vue 3 构建，并通过独立的 FastAPI + LangGraph 服务提供 AI 辅助设计能力。

它解决的不只是“画一张流程图”：从流程分类、基本信息、业务表单到 BPMN 节点配置，用户都可以先用自然语言描述需求，再审阅 AI 给出的结构化变更，确认后应用到可视化设计器中继续调整。

<p align="center">
  <img src="./assets/demos/ai-flow-design.png" alt="FlowMind AI 流程设计" width="960" />
</p>

## 为什么做 FlowMind

传统工作流平台通常要求使用者同时理解 BPMN、表单模型、审批人规则和引擎扩展属性。业务人员表达需求不难，把需求完整翻译成可执行模型才是最耗时的部分。

FlowMind 将 AI 放在设计器旁边，而不是取代设计器：

- 用户负责描述业务目标和确认结果。
- AI 查询现有分类、表单、角色与流程模型，生成结构化操作。
- 系统先展示变更预览，确认后才更新画布。
- 生成结果仍可在 BPMN-JS 和 VForm 3 中手动编辑。

这种方式兼顾生成效率与可控性，也避免 AI 直接覆盖当前设计。

## 四类 AI 设计能力

### 1. 流程分类

根据业务用途生成分类名称、标识和说明，为后续流程模型建立清晰的归属。

![AI 流程分类设计](assets/demos/ai-category-design.png)

### 2. 基本信息

从自然语言中整理流程名称、模型标识、所属分类与业务描述，减少重复录入。

![AI 流程基本信息生成](assets/demos/ai-basic-info-design.png)

### 3. 表单设计

生成可编辑的表单字段、选项、校验规则和布局配置；已有相似表单可以复用，需要独立表单时也能作为新设计继续完善。

![AI 表单设计](assets/demos/ai-form-design.png)

### 4. 流程设计

生成或修改 BPMN 节点、连线、审批人、表单绑定、监听器和扩展属性。变更按节点归纳展示，用户确认后再应用到画布。

![AI 流程设计](assets/demos/ai-flow-design.png)

## 不止是流程生成

FlowMind 覆盖从设计到执行的完整链路：

- 可视化 BPMN 建模、流程定义与部署。
- 可视化表单设计与业务表单绑定。
- 待办、已办、候选任务和我发起的流程。
- 流程详情、运行轨迹与审批记录。
- 流程申请草稿的保存、恢复与提交。
- 用户、角色、部门、菜单和操作日志等后台管理能力。
- Langfuse 链路观测与黄金测试集回归。

## 技术架构

![FlowMind 系统架构](assets/diagrams/flowmind-architecture.png)

| 模块 | 主要技术 | 职责 |
| --- | --- | --- |
| [flowmind-ui](flowmind-ui/README.md) | Vue 3、Element Plus、BPMN-JS、VForm 3 | 管理后台、审批工作台、流程与表单设计器 |
| [flowmind-cloud](flowmind-cloud/README.md) | Spring Boot、Spring Cloud、Flowable | 网关、认证、系统数据与流程执行 |
| [flowmind-ai-flow](flowmind-ai-flow/README.md) | FastAPI、LangGraph、LangChain | ReAct 生成、操作校验、会话状态与评测 |

典型请求链路如下：

```text
浏览器 → Gateway → Java 微服务
              └→ AI 服务 → 模型提供商
                         └→ Langfuse（可选）
```

Gateway 统一校验用户身份。AI 服务接收可信用户上下文，并通过后端接口查询实际分类、表单、角色和模型数据，不在提示词中维护业务白名单。

## 快速启动

### 完整服务

先在项目根目录构建 Java 服务和前端产物：

```bat
bin\build.bat
```

再启动完整 Docker 服务：

```bash
cd docker/flowmind
docker compose -f docker-compose.prod.yml up -d --build
```

访问 <http://localhost:18088>。

### 开发环境

开发编排默认启动前端、AI 服务及 AI 设计链路所需的 Java 服务，并支持 Vue 与 FastAPI 源码热更新：

```bash
cd docker/flowmind
docker compose up -d --remove-orphans
```

File、Gen、Job 和 Monitor 等非必要 Java 服务使用可选 profile：

```bash
docker compose --profile optional up -d
```

Langfuse 作为独立基础设施按需启动：

```bash
docker compose -f docker-compose.langfuse.yml up -d
```

## 本地服务入口

| 服务 | 地址 |
| --- | --- |
| FlowMind | <http://localhost:18088> |
| Gateway | <http://localhost:9001> |
| Nacos | <http://localhost:19090/nacos> |
| MySQL | `localhost:13306` |
| Redis | `localhost:16379` |
| Langfuse | <http://localhost:13001> |

生产编排不会把 AI 容器端口直接暴露到宿主机。前端统一通过 Gateway 的 `/flowmind-ai/**` 路径访问 AI 服务。

## 适用场景

- 请假、报销、采购、合同等企业审批流程。
- 需要嵌入现有系统的流程与表单设计能力。
- 工作流、微服务与 AI Agent 的学习和二次开发。
- 需要通过黄金测试集持续验证生成质量的 AI 应用。

## 继续了解

- [中文 README](README.md)：功能总览、截图与完整启动说明。
- [English README](README_EN.md)：English overview and setup guide.
- [GitHub 仓库](https://github.com/Moonlight168/flowmind)
- [Gitee 仓库](https://gitee.com/wish168/flowmind)

欢迎通过 Issue 反馈问题或提出建议。提交代码前请确保密钥、本地 `.env` 和未脱敏业务数据不会进入版本库。

## 开源协议

FlowMind 基于 [MIT License](LICENSE) 开源，并在 [RuoYi-Cloud](https://gitee.com/y_project/RuoYi-Cloud) 的基础上扩展开发。
