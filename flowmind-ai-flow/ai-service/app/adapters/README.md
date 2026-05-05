# Adapters 模块

统一模型适配层，封装 LLM 调用和后端 API 交互。

## 目录结构

```
adapters/
├── base/
│   ├── adapter.py          # 抽象基类（ModelAdapter, ModelConfig, ModelResponse）
│   ├── http_adapter.py     # HTTP 适配器基类 + 工具函数
│   └── errors.py           # 错误类型（ModelError, ModelErrorCode, classify_error）
├── factory.py              # 工厂（ModelFactory）
├── model_manager.py       # 模型管理器（ModelManager）
│
├── llm/
│   ├── openai_adapter.py  # OpenAI 兼容格式适配器
│   └── core/
│       └── llm_client.py  # LLM 业务封装
│
└── backend/
    ├── base.py            # 后端 REST API 基类
    ├── category.py        # 流程分类服务
    ├── flow.py           # 流程模型服务
    ├── form.py           # 表单服务
    └── role.py           # 角色服务
```

## 核心类型

### ModelConfig

模型配置数据类，包含 `model_name`, `base_url`, `api_key`, `temperature`, `max_tokens`, `top_p`, `timeout`。

### ModelResponse

模型响应数据类，包含 `content`, `model_name`, `usage`, `raw_response`, `success`。

### ModelError

模型调用异常，支持错误分类和可恢复性判断。

## 架构设计

### 继承链（代码组织）

```
ModelAdapter
└── HttpModelAdapter
    └── StandardHttpAdapter
        └── OpenAICompatibleAdapter  ← 具体业务适配器
```

- **ModelAdapter**：定义抽象接口 `generate` / `generate_with_messages`
- **HttpModelAdapter**：实现 HTTP 请求逻辑（请求构建、错误处理、响应解析）
- **StandardHttpAdapter**：可配置的 HTTP 适配器，通过注入 `payload_builder` / `response_parser` 支持不同 API 格式
- **OpenAICompatibleAdapter**：OpenAI 兼容格式的具体实现

**扩展新适配器**（如 Anthropic）：继承 `StandardHttpAdapter`，注入对应的 builder/parser 即可。

```python
class AnthropicAdapter(StandardHttpAdapter):
    def __init__(self, name: str, config: ModelConfig):
        adapter_config = HttpAdapterConfig(
            name=name,
            api_url="",
            payload_builder=build_anthropic_payload,
            response_parser=parse_anthropic_response,
        )
        super().__init__(config, adapter_config)
```

### 运行时调用链

```
LLMClient.generate(prompt)
    └── ModelManager.generate(prompt)
            └── _generate_with_fallback()  → 按优先级遍历适配器
                    └── OpenAICompatibleAdapter.generate(prompt)
                            └── StandardHttpAdapter.generate()
                                    └── HttpModelAdapter._generate_core()
                                            └── requests.post()
```

### 工厂初始化链

```
ModelFactory.initialize()
    └── 读取 settings 配置
            └── 按优先级创建 OpenAICompatibleAdapter
                    └── 注册到 ModelManager
```

## 使用方式

### LLM 调用

```python
from app.adapters.llm.core import get_llm_client

client = get_llm_client()

# 单轮对话
text = client.generate("你好")

# 多轮对话
text = client.generate_messages([
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好，我是AI"},
])

# 结构化输出
data = client.generate_json(
    prompt="返回一个JSON对象",
    schema_name="MySchema",
)

# 指定适配器
text = client.generate("你好", adapter_name="qwen")

# 关闭降级
text = client.generate("你好", use_fallback=False)
```

### 后端服务调用

```python
from app.adapters.backend.category import CategoryService

service = CategoryService(auth_token="user_token")
category = service.ensure_category("分类名称", "CODE001")
```

### 模型工厂

```python
from app.adapters.factory import ModelFactory

ModelFactory.initialize()
manager = ModelFactory.get_model_manager()

ModelFactory.add_adapter("custom", config_dict)
ModelFactory.remove_adapter("custom")
```

## 模型优先级与降级

`ModelManager` 按优先级顺序遍历可用适配器，某适配器失败后自动切换到下一个，直到成功或全部失败。

优先级配置来自 `settings.get_model_priority()`，降级策略由 `settings.get_fallback_config()` 控制。
