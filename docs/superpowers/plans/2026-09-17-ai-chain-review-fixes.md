# AI 链路全栈审查修复实施计划

> 状态：已完成（2026-09-17），含第二轮结构优化

## 2026-09-17 第二轮：通读后的修复与结构优化

### 通读发现并修复的 5 个问题

- 聊天流式端点 `/chat/stream` 的白名单异常同样会静默截断（与设计端点 3b 同型），改为 `except Exception` 兜底转 error 事件。
- 评测用例 thread_id 从 `uuid4` 随机改为 `uuid5(case_id)` 确定性命名：灰度开启时同一用例每次运行命中同一提示词版本，评测可复现、可归因。
- 删除 `discriminate_intent` 的死参数 `version_count`（调用方从不传）及 intent 提示词中的对应行。
- `_save_chat_thread`/`save_preview` 的 fail-soft `except Exception` 在类 docstring 中声明为规范例外（列表预览是优化而非正确性）。
- 删除 `forms.py`/`flow_models.py` 中无调用方的 create/update/get_* 死方法，客户端只保留设计链实际使用的只读查询。

### 结构优化（可读性/简洁/优雅）

- **设计端点合并**：三个近重复的 SSE 端点收敛为 `_run_design_stream(design_type, payload, user, mode)` 共享执行体，各路由只剩一行声明（-60 行）。
- **BPMN 生成器边路径统一**：删除 85 行 `_create_auto_edges`，自动线性边列表与自定义边走同一条 `_create_custom_edges` 路径；自动/自定义两条路径实测均生成有效 XML。
- **widget 树遍历统一**：新增 `design/widget_tree.py`（`iter_widgets`/`iter_child_lists`，兼容 AI 简化形态与 VForm3 文档形态），替换 operations/基线校验器/表单字段校验器/VForm3 校验器/评测共五处略有差异的递归实现；新增 3 条专项单测。
- **node_handler 兜底统一**：13 类白名单改为 `except Exception`（GraphInterrupt 仍上抛），与流式边界同一模式，文件头声明规范例外。
- **死代码清理**：删除 `log_node_execution` 装饰器（无调用方）、`DatabaseSettings`（无引用）、`TaskConfig.schema/description` 与 `TASK_PROMPT_*` 常量间接层、`pyproject` 中未用的 sqlalchemy/pymysql 直接依赖（poetry 重解 lock）。

### 验证

- AI 服务 ruff 全过，204 条单元测试全过（新增 widget_tree 3 条）。
- BPMN 自动边/自定义边两条路径生成-校验冒烟通过。
- 前端生产构建、vitest 均通过（第二轮未改前端）。

## 背景

对前端、网关、AI 服务做全链路只读审查（重点 AI 服务），输出 37 条问题并经用户逐条确认后修复。审查发现的三大主题：流式链路（SSE）层层叠加缺陷、增量设计合并回归、鉴权/权限边界随网关令牌透传扩大。

## 修复清单

### AI 服务（flowmind-ai-flow/ai-service）

- **增量删除节点回归**：`bpmn_merge` 不再把生成结果中不存在的 sequenceFlow 从原 XML 搬回（被删节点的连线随节点丢弃），删除场景不再产生悬空引用并触发校验死循环。实测删除节点合并后校验通过。
- **SSE 桥接兜底**：`_sse.py` 源异常捕获从白名单改为全量 `Exception` 转交；`lxml.XMLSyntaxError` 实测可从静默截断变为正常 error 事件。设计端点 `except STREAM_ERRORS` 同步改为 `except Exception` 并记日志，保证任何异常都有 error 事件 + 服务端日志。
- **SSE 线程泄漏**：消费端 `queue.get` 加 1 秒超时循环 + 收尾无条件 `put_nowait` 结束信号。实测断开 14 次后线程池仅 2 个存活线程（修复前 12 次即占满挂死）。
- **process id 撞 key**：`generate_bpmn_xml` 新增 `process_key` 参数（finalize 传 `modelKey`/`flow_key`，非法字符清洗），不再用分类编码（空分类为字面 `Process_`）。
- **条件字段校验**：`EDGE_E009` 对字符串形态条件（`${field > x}`）同样提取字段做白名单校验。
- **基线防改**：`BASE_B004` 拦截基线节点 type 变化与 form_key 解绑。
- **Redis 必连**：checkpoint 初始化失败默认拒绝启动，仅 `APP_ALLOW_MEMORY_FALLBACK=true`（测试 conftest 已设）允许内存降级。
- **就绪判定**：`describe_readiness` 改为"≥1 个已配置且支持结构化输出的 Provider 即 ready"，删除"必须 2 个/必须开降级"两个理由；`/health/ready` 503 文案改为"无可用结构化模型"。
- **降级候选**：`_candidates` 先按 `_provider_is_configured` 过滤，占位配置不再吃重试预算。
- **角色查询**：改调 `/role/optionselect`（登录可用、全量不分页），解决非管理员 403 与分页截断误判。
- **删除会话**：`delete_thread` 追加 SCAN 清理 `writes:*` 键；`list_threads` 对过期会话做惰性 srem。
- **Misc**：`/chat/state` 404 参数顺序修复；`/chat/history` 改同步 def 走线程池；评测空产物/缺产物判无效；灰度分桶种子只用 release_key（整请求同侧）；死循环报错改为 `validation_failed` + 明确文案 + 不可重试；分类创建失败改为抛 `BackendLookupError`；设计会话隔离键改 `user_id`（重新登录不失忆）；thread_id 加长度上限；`/health` 路由去尾斜杠（修网关 307 丢前缀 404）；docs 仅 debug 开启；basic 模式 `flow_key` 基线兜底 `modelKey`；删除节点重连边继承入边元数据；`.env.example` CORS 示例改显式域名；`adapters/`、`utils/` 残留 `__pycache__` 清理。
- 单元测试同步更新（health/runtime/design_api/finalize 断言），新增占位 Provider 跳过、重登会话稳定、单 Provider 就绪等用例。

### Java 后端（flowmind-cloud）

- 网关 AI 路由加 `metadata.response-timeout: 600000`（对齐 AI 侧会话锁 TTL）+ CircuitBreaker 过滤器（新增 `spring-cloud-circuitbreaker-sentinel` 依赖，Nacos 新增 degrade 规则 dataId）。
- `security.xss.excludeUrls` 增加 `/flowmind-ai/**`（AntPathMatcher 通配，dev/prod 两段）。
- `/role/optionselect` 权限放宽为 `@RequiresLogin`。
- `AuthFilter` 令牌透传保持全局（下游 HeaderInterceptor 依赖 Authorization 头解析登录用户），补充注释说明。

### 前端（flowmind-ui）

- AI 设计浮窗每轮发送前经 `getCurrentBaseline` 从宿主取最新画布/表单刷新基线；应用前若画布在生成期间被改过则弹确认。
- 新增「回退/前进」按钮（版本栈 + 前进栈），修复快照驼峰/蛇形字段错位导致的空回退；三个宿主页面 fill 兼容两种字段。
- 全局助手浮球隐藏路径修正为 `/workflow/*`；AI 预览 XML 渲染失败经 `import-error` 事件提示并回退上一次有效设计；sse.js 401 走重新登录引导（动态 import 保持单测模块图轻量）并读取响应体错误信息；basic 模式 `flow_key` 真值判断；管理端 AI 配置页按真实响应结构取字段；删除 design.js 三个无调用方接口与 `open-ai-assistant` 死代码。

### 部署配置

- prod compose 不发布 AI 服务 `8000:8000`（只经网关访问）；开发环境由宿主机直接运行 AI 服务并监听 8000。

### 2026-09-30 全栈 Docker 启动验证

- 网关保留 Sentinel Gateway 与 Nacos 降级规则，移除与当前 Spring Cloud 组合不兼容且重复的 route `CircuitBreaker` 过滤器；Java 镜像不再把 JAR 目录声明为匿名卷，避免重建容器后继续运行旧产物。
- AI 镜像的 Debian 系统包源切换为阿里云镜像并增加 APT 重试，避免国内网络下构建中断。
- 生产 Compose 的前端静态文件、Java JAR 和 AI Python 源码均在构建时复制进镜像，不挂载业务源码，也未启用 Uvicorn reload，因此代码修改不会自动热更新，需重新构建对应产物和镜像并重建容器。
- Compose 按职责拆分：`docker-compose.yml` 默认启动 AI 功能所需的开发链路，以 Vite 和 Uvicorn 提供热更新，File、Gen、Job、Monitor 通过 `optional` profile 按需启动；`docker-compose.prod.yml` 独立启动包含 Nginx、全部 Java 微服务、AI 服务和基础设施的完整生产栈；`docker-compose.langfuse.yml` 独立管理 Langfuse。开发启动使用 `--remove-orphans` 清理生产栈遗留的 Nginx，避免它与 Vite 同时占用 18088。
- FlowMind Langfuse 使用独立 PostgreSQL、ClickHouse、Redis、MinIO 和命名卷，首次启动自动初始化 `flowmind` 项目；UI 默认发布到 13001，避免与其他项目的常用端口冲突。
- 生产 AI 容器通过 `http://flowmind-langfuse-web:3000` 走 Compose 内部网络，本机开发 AI 通过 `http://localhost:13001` 访问；真实密钥和基础设施密码仅放在被 Git 忽略的 `docker/flowmind/.env`。
- Nginx 入口通过 `FLOWMIND_HTTP_PORT` 配置，默认 `18088:80`，不再需要额外的本机覆盖 Compose。
- MySQL 与 Nacos 凭据均改为 Compose 必填环境变量；Nacos 数据源密码从容器环境解析，受版本控制的示例只保留占位符。
- 开发启动脚本为 AI 的 Uvicorn 启用 `--reload`；前端继续使用 Vite 热更新，Java 未引入额外 DevTools，修改后仍按现有流程重启。

## 验证结果

- AI 服务 ruff 全过，201 条单元测试全过；删除节点合并、SSE 线程泄漏、XMLSyntaxError 转交三条关键修复均实测复现验证。
- Java 网关与 system 模块编译通过。
- 前端 vitest 3 条全过，`npm run build:stage` 生产构建成功。

## 遗留与未做

- `selected_model` 按请求指定 Provider 未实现（需贯穿 chat_graph→runtime 的覆盖通道，属功能开发，未纳入本轮）；管理端 AI 配置页已改为如实说明"模型配置以 .env 为准"。
- `docs/superpowers/` 只记录本轮实施；`private/` 项目介绍与面试问答中涉及会话隔离、版本管理、多模型降级的关键表格已同步更新。
