# scripts

黄金数据集与提示词的 Langfuse 同步脚本，以及从 Langfuse 触发评估实验的 webhook。

## 前置条件

- 在 `ai-service` 目录执行，依赖已由 Poetry 安装。
- `.env` 配置好 Langfuse 密钥（`LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_BASE_URL`）。
- 跑评估还需 `FLOWMIND_AUTH_TOKEN`（测试账号 Bearer Token）。
- Langfuse 与所需后端服务已启动。

## 使用

1. 上传/更新数据集（用例变更后执行，幂等 upsert）

```bash
# 默认：源文件 evals/golden_dataset.jsonl → Langfuse 数据集 flowmind-design-golden-v1
poetry run python -m scripts.upload_golden_to_langfuse
# 如需换数据集名/源文件，显式传参
poetry run python -m scripts.upload_golden_to_langfuse --dataset-path evals/golden_dataset.jsonl --dataset-name flowmind-design-golden-v1
```

2. 上传/更新提示词（提示词变更后执行，幂等：内容一致则只补标签）

```bash
# 提示词目录下每个 .md → 一个 Langfuse Prompt（名称=相对路径去掉 .md）
# 稳定版打 production 标签，其余打 canary 标签
poetry run python -m scripts.upload_prompts_to_langfuse
```

3. 上传/更新契约评估器（评估器变更后执行，幂等：源码一致则跳过）

```bash
# 源文件 evals/evaluators/design_contract.ts → Langfuse code evaluator
poetry run python -m scripts.upload_evaluator_to_langfuse
```

> 自托管 Langfuse 的 code evaluator 需要配置 code evaluator dispatcher 才会真正执行；
> 未配置时评估器仍会创建成功，但不会自动运行。

4. 从 Langfuse 拉取用例跑实验并上报评分

```bash
poetry run python -m scripts.run_golden_eval
poetry run python -m scripts.run_golden_eval --case-id flow-linear-leave
poetry run python -m scripts.run_golden_eval --run-name my-run --max-concurrency 2
```

执行完整链路是：先上传（步骤 1、2、3），再跑评估（步骤 4）。评估只从 Langfuse 拉取，不会触发上传。

## UI 触发实验（可选）

除命令行外，可在 Langfuse 控制台一键触发同一个实验：

1. 进入 `Datasets` → `flowmind-design-golden-v1` → `Start Experiment`。
2. 选 `Custom Experiment`，点 `⚡` 打开 webhook 配置。
3. 填写 URL：`http://flowmind-nginx/webhooks/experiment`（经 nginx 标准 80 端口转发，容器网络内服务名）。
   Default config 可留空，或填 `{"run_name": "ui-trigger", "max_concurrency": 2}`。
4. 点 `Run` 触发，AI 服务异步执行并把评分写回为新的 Dataset Run。

## 参数

| 脚本   | 参数                  | 说明                                                 |
| ------ | --------------------- | ---------------------------------------------------- |
| upload | `--dataset-path`    | 本地 JSONL 路径，默认`evals/golden_dataset.jsonl`  |
| upload | `--dataset-name`    | Langfuse 数据集名，默认`flowmind-design-golden-v1` |
| prompt | 无                    | 目录/标签在脚本常量中配置                            |
| evaluator | `--evaluator-path` | 本地评估器源码路径，默认`evals/evaluators/design_contract.ts` |
| evaluator | `--name`       | Langfuse 评估器名，默认`flowmind-design-contract` |
| eval   | `--case-id`         | 只跑指定用例 ID，缺省跑全部                          |
| eval   | `--dataset-name`    | 要拉取的数据集名，需与上传一致                       |
| eval   | `--run-name`        | Dataset Run 名称，缺省按时间生成                     |
| eval   | `--max-concurrency` | 并发用例数，默认 1（串行）                           |

## 结果

日志末尾会打印评分汇总和 Langfuse Dataset Run 链接，可在 Langfuse 控制台查看每条用例的输入、输出与分数。
