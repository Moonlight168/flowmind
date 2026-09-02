# 校验层 + 前置压缩 实现方案（定稿）

> 状态：已实施完成（校验层 + 前置压缩随后续方案落地；本文为实施前设计快照，正文 `app/agents/*` 为重构前旧路径，已由 `80d4563` 迁移为 `app/design/*`、`app/graph/nodes/*`）
> 后续修订：§0「砍掉 with_structured_output」已被 `2026-08-19` 方案否决——结构化输出成为唯一生成路径，最终形态为 ReAct 按需检索 + `response_format` 结构化收尾。详见 `plans/2026-08-19-structured-output-redesign.md`、`plans/2026-09-01-react-retrieval-and-runtime-hardening.md`

## 0. 结论

- dsh 替换 ReAct Agent：**暂缓**（preview + 双运行时，不换）
- 压缩：前置压缩（trim_messages 裁剪 + 可选 LLM 摘要），替换半废的压缩工具
- 校验：JSON 层结构校验器（Node/Edge/Form/Category/BPMN），在生成 BPMN 前早失败
- 砍掉：FieldLockValidator、Node/FormEnricher（与 format_node 的 transform_to_vform3/bpmn_generator 职责重复）、DeployValidator（与"前端确认后保存"架构冲突）、staged_state（无消费者 YAGNI）；with_structured_output（与 tool-calling 冲突）——❌ 此项已被 2026-08-19 方案否决，结构化输出成为主路径

## 1. 职责边界（review vs format）

- **review 节点 = 质检**：校验 LLM 扁平输出是否结构合法；不合法 → 注入反馈 → 重跑 design；死循环 → error
- **format 节点 = 总装**：把合法骨架 + 前端上下文组装成最终 form_data 返回（合并 modelId/modelName/modelKey/category/description、transform_to_vform3、生成 message 文案）

A 方案：flow_design 的 bpmn_xml 在 review 的 BPMNXMLValidator 生成（因为 `validate_bpmn_xml` 验的是 XML 字符串，必须先有 XML）+ 缓存，format 复用缓存（1 次生成）。

## 2. 提交 1：前置压缩

- 删 `app/agents/tools/compress_tools.py`
- `react_tools.py` 删 `_make_compress_tool`；`tools/__init__.py` 删 compress 导入/注册/导出
- 新增 `app/agents/compression.py`：`compress_history`（system + 最近 keep_recent 条；中间段 enable_llm_summary ? LLM 摘要 : 裁剪）
- `settings.py` 加 `CompressConfig`（max_messages=12 / keep_recent=4 / enable_llm_summary=True / summary_max_tokens=300）
- `model_manager.py` TASK_TEMPERATURE_CONFIG 加 `"compress": {"temperature": 0.0, "max_tokens": 300}`
- `react_agent_node.py` 调 run_react_agent 前先 compress_history

## 3. 提交 2：校验层

- 新增 `app/agents/validators/`：base / pipeline / node_validator / edge_validator / form_field_validator / category_validator / bpmn_xml_validator
- `review_node.py` 改造：按 design_type+mode 选 Pipeline 跑校验，死循环检测，失败反馈重试
- `format_node.py`：flow_design 复用 `design_output["bpmn_xml"]` 缓存
- `reviewer.py` 删 `_validate_business_rules`（迁入 NODE_N005）
- `app_state.py` 加 `review_error_history`
- `settings.py` 加 `ValidationConfig`（review_max_retry_count=3）

## 4. 校验规则

- NodeValidator NODE_N001-N008；EdgeValidator EDGE_E001-E007；FormFieldValidator FORM_FF001-FF008；CategoryValidator CAT_C001-C005
- BPMNXMLValidator：包装 `validate_bpmn_xml`，规则 ID `V→BPMN_V` 重映射，新增 BPMN_V012（生成失败），缓存 bpmn_xml
- 死循环：连续 2 次错误 rule_id 集合相同 → intent=error

## 5. 不改的部分

LLM 输出形态（扁平骨架 + 审批人 LLM 查询填充）、prompt、format 层次化逻辑、部署/保存流程。
