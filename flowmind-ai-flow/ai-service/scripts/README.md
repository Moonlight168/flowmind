# scripts

黄金数据集评估脚本，用于把本地用例同步到 Langfuse 并跑实验。

## 前置条件

- 在 `ai-service` 目录执行，依赖已由 Poetry 安装。
- `.env` 配置好 Langfuse 密钥（`LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_BASE_URL`）。
- 跑评估还需 `FLOWMIND_AUTH_TOKEN`（测试账号 Bearer Token）。
- Langfuse 与所需后端服务已启动。

## 使用

1. 上传/更新数据集（用例变更后执行，幂等 upsert）

```bash
# 默认：源文件 evals/golden_dataset.jsonl → Langfuse 数据集 flowmind-design-golden-v1
poetry run python scripts/upload_golden_to_langfuse.py
# 如需换数据集名/源文件，显式传参
poetry run python scripts/upload_golden_to_langfuse.py --dataset-path evals/golden_dataset.jsonl --dataset-name flowmind-design-golden-v1
```

2. 从 Langfuse 拉取用例跑实验并上报评分

```bash
poetry run python scripts/run_golden_eval.py
poetry run python scripts/run_golden_eval.py --case-id flow-linear-leave
poetry run python scripts/run_golden_eval.py --run-name my-run --max-concurrency 2
```

执行完整链路是：先上传（步骤 1），再跑评估（步骤 2）。评估只从 Langfuse 拉取，不会触发上传。

## 参数

| 脚本   | 参数                  | 说明                                                 |
| ------ | --------------------- | ---------------------------------------------------- |
| upload | `--dataset-path`    | 本地 JSONL 路径，默认`evals/golden_dataset.jsonl`  |
| upload | `--dataset-name`    | Langfuse 数据集名，默认`flowmind-design-golden-v1` |
| eval   | `--case-id`         | 只跑指定用例 ID，缺省跑全部                          |
| eval   | `--dataset-name`    | 要拉取的数据集名，需与上传一致                       |
| eval   | `--run-name`        | Dataset Run 名称，缺省按时间生成                     |
| eval   | `--max-concurrency` | 并发用例数，默认 1（串行）                           |

## 结果

日志末尾会打印评分汇总和 Langfuse Dataset Run 链接，可在 Langfuse 控制台查看每条用例的输入、输出与分数。
