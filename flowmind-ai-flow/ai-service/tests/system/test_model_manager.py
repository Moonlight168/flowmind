"""
FlowMind AI Service - 模型运行时系统测试

验证统一模型运行时（app.llm.runtime.ModelRuntime）的模型管理与降级行为：
- 单 Provider 可用时直接执行
- 多 Provider 按优先级选择
- 构建失败/调用失败自动切换下一个 Provider
- 全部失败抛出 ModelExhaustedError
- 任务级参数（temperature）与结构化候选过滤
"""

from __future__ import annotations

import pytest
from langchain_openai import ChatOpenAI

from app.llm import ModelExhaustedError, reset_model_runtime
from app.llm.runtime import ModelRuntime, ModelRuntimeConfig


def _cfg(model: str = "m", structured: bool = True) -> dict:
    return {
        "model_name": model,
        "base_url": "http://localhost:9999/v1",
        "api_key": "test-key",
        "supports_structured_output": structured,
    }


@pytest.fixture(autouse=True)
def reset_runtime():
    """每个测试前后清空全局模型运行时（对应旧 ModelFactory.reset）"""
    reset_model_runtime()
    yield
    reset_model_runtime()


class TestSingleProvider:
    """单模型可用测试"""

    def test_operation_runs_on_only_provider(self):
        calls: list[str] = []

        def builder(provider, config, task_name):
            calls.append(provider)
            return object()

        runtime = ModelRuntime(
            providers={"p1": _cfg()},
            priority=["p1"],
            model_builder=builder,
            config=ModelRuntimeConfig(max_retries=0, retry_interval=0),
        )
        result = runtime.execute("chat", lambda llm: llm)
        assert result is not None
        assert calls == ["p1"]

    def test_default_builder_returns_chatopenai(self):
        """默认 model_builder 返回 ChatOpenAI 实例"""
        runtime = ModelRuntime(
            providers={"p1": _cfg()},
            priority=["p1"],
            config=ModelRuntimeConfig(max_retries=0),
        )
        model = runtime._get_model("p1", "chat")
        assert isinstance(model, ChatOpenAI)
        assert model.model_name == "m"


class TestModelPriority:
    """多模型优先级测试"""

    def test_providers_follow_priority(self):
        """describe_providers 按 priority 顺序返回"""
        runtime = ModelRuntime(
            providers={"p1": _cfg(), "p2": _cfg(model="m2")},
            priority=["p2", "p1"],
        )
        names = [item["name"] for item in runtime.describe_providers()]
        assert names == ["p2", "p1"]


class TestModelFallback:
    """模型降级测试"""

    def test_build_failure_falls_back_to_next_provider(self):
        """第一个模型构建失败时自动使用第二个"""
        def builder(provider, config, task_name):
            if provider == "p1":
                raise ValueError("模拟 p1 配置不可用")
            return "model-p2"

        runtime = ModelRuntime(
            providers={"p1": _cfg(), "p2": _cfg(model="m2")},
            priority=["p1", "p2"],
            model_builder=builder,
            config=ModelRuntimeConfig(max_retries=1, retry_interval=0),
        )
        assert runtime.execute("chat", lambda llm: llm) == "model-p2"

    def test_call_failure_falls_back_to_next_provider(self):
        """第一个模型调用失败时自动降级到第二个"""
        def builder(provider, config, task_name):
            return provider

        runtime = ModelRuntime(
            providers={"p1": _cfg(), "p2": _cfg(model="m2")},
            priority=["p1", "p2"],
            model_builder=builder,
            config=ModelRuntimeConfig(max_retries=1, retry_interval=0),
        )

        def operation(model):
            if model == "p1":
                raise RuntimeError("模拟 p1 调用失败")
            return f"ok:{model}"

        assert runtime.execute("chat", operation) == "ok:p2"

    def test_all_models_fail_raises_exception(self):
        """所有模型都失败时抛出 ModelExhaustedError"""
        def builder(provider, config, task_name):
            raise ValueError("所有模型不可用")

        runtime = ModelRuntime(
            providers={"p1": _cfg()},
            priority=["p1"],
            model_builder=builder,
            config=ModelRuntimeConfig(max_retries=0, retry_interval=0),
        )
        with pytest.raises(ModelExhaustedError, match="不可用"):
            runtime.execute("chat", lambda llm: llm)


class TestTaskConfig:
    """任务级配置测试"""

    def test_task_temperature_config(self):
        """不同任务使用不同 temperature"""
        runtime = ModelRuntime(
            providers={"p1": _cfg()},
            priority=["p1"],
            config=ModelRuntimeConfig(max_retries=0),
        )
        chat_model = runtime._get_model("p1", "chat")
        design_model = runtime._get_model("p1", "category_design")
        assert chat_model.temperature == 0.8
        assert design_model.temperature == 0.3

    def test_structured_candidates_filter(self):
        """结构化任务只选择声明支持结构化输出的 Provider"""
        providers = {
            "vllm": _cfg(structured=False),
            "qwen": _cfg(model="qwen"),
        }
        runtime = ModelRuntime(providers=providers, priority=["vllm", "qwen"])
        assert runtime._candidates(structured=True) == ["qwen"]
        assert runtime._candidates(structured=False) == ["vllm", "qwen"]
