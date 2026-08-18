"""
FlowMind 智能流程设计服务 - 对话历史前置压缩

在调用 LLM 之前对消息列表做确定性裁剪：保留 system + 最近 N 条，
中间段可选 LLM 摘要替换。压缩是优化而非正确性，失败静默回退。

注：裁剪用简单切片（消息是 dict 列表，非 langchain BaseMessage，
langchain 的 trim_messages 用不上）；LLM 摘要复用 ModelFactory.create_llm。
"""

from typing import Any

from app.adapters.factory import ModelFactory
from app.config.settings import settings
from app.infra.logger import logger


def compress_history(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """压缩对话历史（前置步骤）

    Args:
        messages: 消息列表，含 system / user / assistant

    Returns:
        压缩后的消息列表
    """
    config = settings.compress
    if len(messages) <= config.max_messages:
        return messages

    system = [m for m in messages if m.get("role") == "system"]
    non_system = [m for m in messages if m.get("role") != "system"]
    if len(non_system) <= config.keep_recent:
        return messages

    middle = non_system[: -config.keep_recent]
    recent = non_system[-config.keep_recent:]

    if config.enable_llm_summary:
        summary = _llm_summary(middle)
        if summary:
            logger.info(f"[compress] LLM 摘要 {len(middle)} 条中间消息，保留 {len(recent)} 条")
            return [
                *system,
                {"role": "assistant", "content": f"[历史摘要] {summary}"},
                *recent,
            ]
        logger.info(f"[compress] LLM 摘要失败，回退纯裁剪")

    # 纯裁剪：中间段直接丢弃
    logger.info(f"[compress] 裁剪 {len(middle)} 条中间消息，保留 {len(recent)} 条")
    return [*system, *recent]


def _llm_summary(middle: list[dict[str, Any]]) -> str:
    """用 LLM 摘要中间段，失败返回空串（回退纯裁剪）"""
    try:
        llm = ModelFactory.get_model_manager().create_llm(task_name="compress")
        resp = llm.invoke([{"role": "user", "content": _build_summary_prompt(middle)}])
        summary = (resp.content or "").strip() if hasattr(resp, "content") else ""
        return summary
    except (RuntimeError, ValueError, KeyError, OSError) as e:
        logger.warning(f"[compress] LLM 摘要失败，回退纯裁剪: {e}")
        return ""


def _build_summary_prompt(messages: list[dict[str, Any]]) -> str:
    """构建摘要提示词"""
    history_text = "\n".join(
        f"{'[用户]' if m.get('role') == 'user' else '[助手]'}: {str(m.get('content', ''))[:200]}"
        for m in messages
    )
    return (
        "请为以下对话历史生成简洁摘要，保留关键信息（用户意图、分类/流程/表单实体、"
        f"关键参数）。直接输出摘要，不超过 200 字。\n\n{history_text}"
    )
