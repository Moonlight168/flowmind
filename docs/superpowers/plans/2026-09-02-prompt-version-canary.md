# 提示词版本管理与灰度发布实施记录

> 状态：已实施并完成 review，待推送
> 日期：2026-09-02
> 范围：`flowmind-ai-flow/ai-service`

## 目标

- 保持 Markdown 为提示词正文唯一来源，版本配置不承载提示词内容。
- 使用 `thread_id` 对提示词版本稳定分流，保证同一会话不跨版本漂移。
- 支持按提示词配置稳定版、多个版本文件和权重。
- 支持环境变量强制版本，作为验证和紧急回滚入口。
- 将实际命中的版本与 stable/canary cohort 写入 Langfuse metadata。

## 实现

- `app/prompts/versions.json` 管理版本、文件与权重；未登记的提示词自动使用原文件并标记 `v1/stable`。
- `prompt_release(thread_id)` 建立请求级上下文，聊天、设计同步和流式入口统一接入。
- `load_prompt/render_prompt/build_prompt` 对调用方保持兼容，内部完成稳定哈希选版和 Markdown 缓存读取。
- ReAct 工具在创建 Agent 时加载当前请求版本的 Markdown 描述，避免模块导入时固定为稳定版。
- `PROMPT_VERSION_OVERRIDES` 的强制版本优先于权重，可立即将指定提示词切回稳定版。
- 灰度文件缺失时自动回退稳定版；配置读取失败不影响稳定版本调用。
- LangChain 调用配置增加 `prompt_versions` metadata，支持在 Langfuse 按实际版本对比链路与评估结果。

## 边界

- 不增加数据库、管理后台、双部署或新依赖。
- 不修改 API/SSE 契约。
- 是否扩大灰度比例由黄金数据集和线上 Langfuse 数据决定，代码不做自动晋级。

## 验证

- Ruff 与格式检查通过。
- AI 服务单元和集成测试合计 112 项通过。
- Standards、Spec 与过度设计审查无阻塞项。
