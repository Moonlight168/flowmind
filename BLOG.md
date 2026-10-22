# 🎨 FlowMind 开源｜AI 自动生成审批流程：Spring Cloud + Vue3 + LangGraph 全栈毕设项目

> 关键词：计算机毕业设计、软件工程毕业设计、Java 毕设、AI 工作流、Flowable、BPMN、LangGraph、Spring Cloud、Vue3、智能审批、开源项目

每年毕设季，同一批项目准时还魂：图书管理系统、学生选课系统、宿舍分配系统。不是它们不好，而是答辩老师闭着眼都知道你下一页 PPT 要放什么。

FlowMind 是我给自己交的答案：一个 AI 真的会参与设计流程的审批系统。你只需要描述需求——"请假三天以上要部门经理和 HR 连续审批"——它就能帮你生成流程分类、基本信息、业务表单，甚至 BPMN 流程图。

但整个项目里我最得意的设计决策是：**AI 说得再好听，也必须你亲手点确认才生效。**

- GitHub：[https://github.com/Moonlight168/flowmind](https://github.com/Moonlight168/flowmind)
- Gitee：[https://gitee.com/wish168/flowmind](https://gitee.com/wish168/flowmind)
- 开源协议：MIT License

如果它能为你的选题、学习或二次开发提供思路，欢迎点一个 **Star** 收藏。请根据自己的课题要求完成需求分析、功能扩展和论文撰写，不建议原样作为成果提交。

## 👋 先自报家门：FlowMind 到底是个啥

一句话：基于 RuoYi-Cloud、Flowable 和 Vue 3 的智能流程审批平台，AI 辅助能力由 FastAPI + LangGraph 提供。

但"审批系统"这四个字太朴素了，直接看它覆盖的完整链路：

- 流程分类与模型管理
- BPMN 2.0 可视化设计
- 业务表单设计与绑定
- 流程部署、发起与审批
- 待办、已办、待签收和我发起的流程
- 申请草稿、运行轨迹与审批记录
- AI 分类、基本信息、表单和流程设计
- Langfuse 可观测与黄金测试集回归

注意最后两条——这才是它和"管理系统 + 一个聊天框"的本质区别。FlowMind 的定位不是让 AI 抢走设计器，而是让 AI 坐在设计器旁边当搭档：它负责理解需求、生成候选方案，用户永远握着最终决定权。

## 🤖 把 AI 塞进工作流引擎，一共分四步

传统做法是依次创建分类、填写模型信息、设计表单、手绘 BPMN、配置审批人，最后还得检查每个节点是否满足 Flowable 的运行要求。一条链走完，头发已经薄了。

FlowMind 把这条链拆成了四类 AI 设计能力。

### 🗂️ 第一步：流程分类设计

输入分类用途，AI 生成名称、标识和说明，写入前先展示字段变化。

![FlowMind AI 流程分类设计](assets/demos/ai-category-design.png)

### 📝 第二步：流程基本信息生成

AI 从业务描述里整理出流程名称、模型标识、所属分类和说明。复制粘贴的活，就该机器干。

![FlowMind AI 流程基本信息生成](assets/demos/ai-basic-info-design.png)

### 🧾 第三步：可编辑表单生成

AI 不只起字段名，还会考虑字段类型、选项、必填校验和布局配置。生成完还能拖进 VForm 3 设计器继续调——AI 起草，你签字。

![FlowMind AI 表单设计](assets/demos/ai-form-design.png)

### 🧩 第四步：BPMN 流程生成与修改

描述完整审批路径，或者要求"把这个节点的审批人改成财务角色""在审批后加一个抄送"。AI 会先查询系统里真实存在的分类、角色、表单和模型，再生成结构化操作，最后等你确认是否应用。

![FlowMind AI 流程设计](assets/demos/ai-flow-design.png)

## ✋ 为什么 AI 生成完还要我再点一次确认？

问得好。让大模型直接重写 BPMN XML 当然"看起来很快"，但在真实系统里约等于让实习生直接改生产数据库：

- 节点 ID 可能失效
- 已有配置可能被悄悄覆盖
- 引用的表单、角色可能压根不存在

所以 FlowMind 走的是一条更稳的路：**生成操作 → 校验操作 → 展示预览 → 用户确认 → 更新画布**。

```text
自然语言需求
    ↓
ReAct Agent 查询真实业务数据
    ↓
生成结构化设计操作
    ↓
后端校验节点、字段和引用
    ↓
前端按字段或节点展示变更
    ↓
用户确认后应用到设计器
```

这样 AI 的效率一点没浪费，但每次修改都可见、可确认、可继续编辑。🤖 AI 负责"我想这么改"，🛡️ 系统负责"你这么改会不会出事"，✅ 你负责"准了"。

## 🧱 技术栈：一套很"毕设"但很能打的组合

![FlowMind 系统架构](assets/diagrams/flowmind-architecture-current.png)

三个子项目，各司其职：

| 子项目 | 技术栈 | 主要职责 |
| --- | --- | --- |
| [flowmind-ui](flowmind-ui/README.md) | Vue 3、Element Plus、BPMN-JS、VForm 3 | 管理后台、审批工作台、流程与表单设计器 |
| [flowmind-cloud](flowmind-cloud/README.md) | Spring Boot、Spring Cloud、Flowable | 网关、认证、系统数据和流程执行 |
| [flowmind-ai-flow](flowmind-ai-flow/README.md) | FastAPI、LangGraph、LangChain | ReAct 推理、操作校验、会话状态和评测 |

典型调用链路：

```text
浏览器 → Gateway → Java 微服务 → Flowable / MySQL / Redis
              └→ AI 服务 → 大模型提供商
                         └→ Langfuse（可选）
```

Gateway 统一做身份校验，把可信用户上下文传给 AI 服务。还有一个反直觉的设计：AI Agent 不在提示词里维护角色、表单或节点的白名单——那种东西刚写完就过期了。它需要什么数据，就直接调后端接口查真实业务数据，永远鲜活。

## 🛠️ 别被 AI 抢戏：日常审批也样样齐全

AI 是亮点，但一个审批系统的基本功才是它能跑起来的底气。

### 📥 审批工作台

- 发起流程并填写业务表单
- 统一处理待办、已办和待签收任务
- 查看我发起的流程及运行状态
- 查看审批意见、流程轨迹和历史节点
- 保存并恢复未提交的申请草稿

### ⚙️ 后台流程管理

- 流程分类管理
- 流程模型设计
- 表单设计与维护
- 流程定义部署和版本管理
- 用户、角色、部门、菜单和日志管理

### 🔬 AI 工程化能力

- ReAct 工具调用与多轮会话
- 结构化输出与操作级校验
- Langfuse Trace 和 Prompt 观测
- 黄金测试集与回归评测
- 会话版本、草稿状态和未应用变更管理

## 🐳 五分钟跑起来（Docker 走起）

### 🚀 方式一：完整服务

项目根目录构建 Java 服务和前端产物：

```bat
bin\build.bat
```

启动完整 Docker 编排：

```bash
cd docker/flowmind
docker compose -f docker-compose.prod.yml up -d --build
```

浏览器访问：<http://localhost:18088>

### 🔧 方式二：开发环境

开发编排默认启动前端、AI 服务和 AI 设计链路所需的 Java 服务，支持 Vue 与 FastAPI 源码热更新——改代码不用重建容器，适合边看边折腾：

```bash
cd docker/flowmind
docker compose up -d --remove-orphans
```

Langfuse 是独立编排，想要可观测就再拉一个：

```bash
docker compose -f docker-compose.langfuse.yml up -d
```

### 🌐 常用访问地址

| 服务 | 地址 |
| --- | --- |
| FlowMind Web | <http://localhost:18088> |
| Gateway | <http://localhost:9001> |
| Nacos | <http://localhost:19090/nacos> |
| MySQL | `localhost:13306` |
| Redis | `localhost:16379` |
| Langfuse | <http://localhost:13001> |

顺带一提：生产编排不会直接暴露 AI 容器端口，前端统一走 Gateway 的 `/flowmind-ai/**` 路径访问 AI 服务。少开一个口子，少一分风险。

## 🎯 这项目适合谁

- 计算机科学与技术、软件工程、信息管理等专业，正在为毕设选题发愁的学生
- 想在 Java 管理系统里加 AI 创新点、又怕加成"聊天框贴皮"的开发者
- 想看 Flowable 和 BPMN 2.0 真实落地姿势的同学
- 想实践 Vue 3 + Spring Cloud 微服务全栈的开发者
- 想研究 LangGraph ReAct Agent、结构化输出和评测体系的 AI 应用开发者

一个小建议：别贪多，挑一个方向扎进去。偏 Java 的研究流程引擎和微服务；偏前端的打磨 BPMN 与表单设计体验；偏 AI 的扩展工具调用、提示词评测和生成结果校验。这样才容易长出属于自己的工作量和论文贡献，而不是"什么都沾了一点"。

## 🎓 如果你拿它做毕设

| 毕设考察维度 | FlowMind 可展示的内容 |
| --- | --- |
| 业务完整性 | 流程建模、表单设计、部署、发起、审批、草稿和历史记录 |
| 系统架构 | 前后端分离、Spring Cloud 微服务、统一网关和服务注册发现 |
| 专业深度 | BPMN 2.0、Flowable 流程引擎、审批人规则和流程版本管理 |
| AI 创新点 | LangGraph ReAct Agent、结构化输出、变更预览和多轮设计 |
| 工程能力 | Docker Compose、配置隔离、接口鉴权、日志与 Langfuse 可观测 |
| 质量保障 | 单元测试、黄金测试集、生成结果校验和回归评测 |

它能拆出不止一个题目方向：

- 基于 Flowable 的企业智能审批系统设计与实现
- 基于大语言模型的 BPMN 流程自动生成方法研究
- 基于 LangGraph 的流程设计 Agent 设计与实现
- 面向企业审批场景的动态表单与工作流协同平台
- 大模型生成工作流的校验、评测与可观测系统

答辩时有三条主线可以讲：为什么选工作流引擎而不是自己造表、AI 如何把自然语言变成结构化操作、系统怎么用校验加人工确认兜住大模型的误操作。这三条线任何一条展开，都比"我调了个 ChatGPT 接口"有内容得多。

## 🔭 接下来想做什么

FlowMind 还在迭代，这些方向在路上：

- 提升复杂条件分支和多实例任务的生成质量
- 完善表单与流程节点之间的语义匹配
- 扩充黄金测试集和自动化回归场景
- 改进 AI 变更预览的可读性
- 优化 Docker 开发体验与部署文档
- 增加消息通知、超时提醒和流程数据统计
- 接入知识库，为不同行业提供流程设计规范
- 研究模型对比、提示词实验和生成质量量化指标

## 💬 最后聊两句

工作流系统真正难的，从来不是把节点画出来，而是让流程、表单、人员规则和运行配置长期协同演进不散架。

FlowMind 想证明一件事：把 AI 引入流程设计，可以不靠玄学——不隐藏变更、不伪造成功、不剥夺用户对最终模型的控制权。

如果你也在研究 **Flowable、BPMN、LangGraph 或 AI 工作流设计**，欢迎来体验、来提 Issue：

- GitHub：[https://github.com/Moonlight168/flowmind](https://github.com/Moonlight168/flowmind)
- Gitee：[https://gitee.com/wish168/flowmind](https://gitee.com/wish168/flowmind)

如果它帮你省下了选题纠结的时间，欢迎 **Star、Fork 或转给同样在准备毕设的同学**。也欢迎把你的课题方向和想要的功能写在 Issue 里——真实的反馈，是这个项目继续迭代下去的理由。

## 📄 开源协议

FlowMind 基于 [MIT License](LICENSE) 开源，并在 [RuoYi-Cloud](https://gitee.com/y_project/RuoYi-Cloud) 的基础上扩展开发。
