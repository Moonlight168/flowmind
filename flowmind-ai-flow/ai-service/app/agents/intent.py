"""
FlowMind 智能流程设计服务 - 意图判别

阶段1：区分 design / clarification / rollback / reset。
判别失败默认 design（宁可多预取，不漏真实设计意图）。
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from app.adapters.factory import ModelFactory
from app.infra.logger import logger
from app.infra.observability import langchain_config


class Intent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["design", "clarification", "rollback", "reset"]
    target: str | None = None  # rollback 时："start"(一开始) / "prev"(上一步)
    message: str | None = None  # clarification 时的追问内容


INTENT_SYSTEM_PROMPT = """判断用户输入的意图，输出以下四种之一：
- design：用户要设计或修改流程/表单/分类（含"加节点"、"改成总监"、"设计请假流程"等增量或全新指令）
- clarification：输入无意义或需求不明确（如"你好"、"随便"），或信息不足无法设计（如只说"设计流程"但没说是什么流程）——此时在 message 字段给出具体追问内容
- rollback：用户要回到历史版本（"回到一开始/最初的版本"→target="start"，"上一步/撤销"→target="prev"）
- reset：用户要清空重新开始

规则：
1. 拿不准就判 design（宁可多判 design，不要漏掉真实设计需求）
2. 有"当前已有设计"上下文时，指令性输入（如"改成总监"）判 design
3. 只有明确表达"回到/回退/撤销/清空"才判 rollback 或 reset
"""


def discriminate_intent(
    user_input: str,
    baseline_summary: str = "",
    version_count: int = 0,
    llm=None,
) -> Intent:
    """判别用户意图；判别失败默认 design

    Args:
        user_input: 用户输入
        baseline_summary: 当前已有设计的摘要（如"3 个节点"）
        version_count: 版本历史数量（用于 rollback 消歧）
        llm: 可注入的 LLM（测试用），None 时从 ModelFactory 取
    """
    if llm is None:
        llm = ModelFactory.get_model_manager().create_llm(
            task_name="intent", structured=True
        )

    prompt = INTENT_SYSTEM_PROMPT
    if baseline_summary:
        prompt += f"\n\n当前已有设计：{baseline_summary}"
    if version_count > 0:
        prompt += f"\n版本历史：共 {version_count} 个版本"
    prompt += f"\n\n用户输入：{user_input}"

    try:
        result = llm.with_structured_output(Intent).invoke(
            [{"role": "system", "content": prompt}], config=langchain_config()
        )
        if result is None:
            return Intent(kind="design")
        return result
    except (
        ValidationError,
        RuntimeError,
        ValueError,
        TypeError,
        KeyError,
        OSError,
    ) as e:
        logger.warning(f"[intent] 判别失败，默认 design: {e}")
        return Intent(kind="design")
