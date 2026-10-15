# scripts

FlowMind 的提示词、评测数据集和 Langfuse 状态评估器同步脚本。

## 前置条件

- 在 `ai-service` 目录执行，依赖由 Poetry 安装。
- `.env` 配置 Langfuse 密钥。
- 执行真实评测还需要 `FLOWMIND_AUTH_TOKEN`。
- Langfuse、AI 服务和评测所需后端服务已经启动。

## 评测数据集

| 参数 | 设计窗口 | 本地文件 | Langfuse Dataset |
|---|---|---|---|
| `category` | 流程分类 | `evals/datasets/category_design.jsonl` | `flowmind-category-design-v1` |
| `basic` | 流程基本信息 | `evals/datasets/basic_info_design.jsonl` | `flowmind-basic-info-design-v1` |
| `form` | 表单设计 | `evals/datasets/form_design.jsonl` | `flowmind-form-design-v1` |
| `flow` | 流程模型 | `evals/datasets/flow_model_design.jsonl` | `flowmind-flow-model-design-v1` |

`all` 会依次处理四个数据集。

## 使用

上传数据集：

```bash
poetry run python -m scripts.upload_dataset flow
poetry run python -m scripts.upload_dataset all
```

上传提示词：

```bash
poetry run python -m scripts.upload_prompts
poetry run python -m scripts.upload_prompts --dry-run
```

上传唯一的 TypeScript 状态评估器：

```bash
poetry run python -m scripts.upload_evaluator
poetry run python -m scripts.upload_evaluator --dry-run
```

运行真实评测：

```bash
poetry run python -m scripts.run_evaluation flow
poetry run python -m scripts.run_evaluation flow --case-id flow-linear-leave
poetry run python -m scripts.run_evaluation all --max-concurrency 2
```

状态评估器只检查每一轮是否有有效输出，以及状态是否为 `ready` 或 `needs_input`。`error` 和空输出均视为失败。自托管 Langfuse 必须启动 Code Evaluator Dispatcher，才能生成 `case_pass` 分数。
