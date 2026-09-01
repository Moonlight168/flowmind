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
from app.prompts.loader import render_prompt


class Intent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["design", "clarification", "rollback", "reset"]
    target: str | None = None  # rollback 时："start"(一开始) / "prev"(上一步)
    message: str | None = None  # clarification 时的追问内容


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

    context_lines = []
    if baseline_summary:
        context_lines.append(f"当前已有设计：{baseline_summary}")
    if version_count > 0:
        context_lines.append(f"版本历史：共 {version_count} 个版本")
    prompt = render_prompt(
        "agents/intent.md",
        {
            "design_context": "\n".join(context_lines),
            "user_input": user_input,
        },
    )

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
