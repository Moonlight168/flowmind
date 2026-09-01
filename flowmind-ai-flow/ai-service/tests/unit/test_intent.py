"""
FlowMind 智能流程设计服务 - 意图判别单元测试
"""

from app.agents.intent import Intent, discriminate_intent


class _FakeLLM:
    def __init__(self, result=None, exc=None):
        self._result = result
        self._exc = exc

    def with_structured_output(self, schema):
        return self

    def invoke(self, messages, config=None):
        if self._exc:
            raise self._exc
        return self._result


def test_design():
    llm = _FakeLLM(result=Intent(kind="design"))
    assert discriminate_intent("设计请假流程", llm=llm).kind == "design"


def test_clarification():
    llm = _FakeLLM(result=Intent(kind="clarification"))
    assert discriminate_intent("你好", llm=llm).kind == "clarification"


def test_rollback():
    llm = _FakeLLM(result=Intent(kind="rollback", target="start"))
    assert discriminate_intent("回到一开始", llm=llm).target == "start"


def test_reset():
    llm = _FakeLLM(result=Intent(kind="reset"))
    assert discriminate_intent("清空重来", llm=llm).kind == "reset"


def test_failure_defaults_to_design():
    """判别失败 → 默认 design"""
    llm = _FakeLLM(exc=RuntimeError("模型挂了"))
    assert discriminate_intent("设计流程", llm=llm).kind == "design"


def test_none_defaults_to_design():
    """判别返回 None → 默认 design"""
    llm = _FakeLLM(result=None)
    assert discriminate_intent("设计流程", llm=llm).kind == "design"
