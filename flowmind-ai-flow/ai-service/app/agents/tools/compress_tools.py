"""
FlowMind 智能流程设计服务 - 对话历史压缩工具

本模块实现对话历史的压缩功能，支持：
- rule_based: 基于规则的快速压缩
- llm_enhanced: 基于 LLM 的智能摘要压缩
- hybrid: 优先智能摘要，失败时回退规则压缩
"""

import re
from typing import Any

from app.infra.logger import logger

# 默认保留的最近消息条数
DEFAULT_RECENT_COUNT = 4
# LLM 摘要模型的 token 上限
SUMMARY_MAX_TOKENS = 500

COMPRESS_CONVERSATION_HISTORY_SCHEMA = {
    "name": "compress_conversation_history",
    "description": (
        "当对话历史过长时，压缩历史消息以节省 token。适用于复杂任务需要回顾多轮上下文，"
        "或简单任务可忽略早期对话的场景。\n\n"
        "模式选择建议：\n"
        "- rule_based：简单指令（继续、确认），速度快无额外 token 消耗\n"
        "- llm_enhanced：复杂决策、需要回顾早期上下文，语义完整但需额外 token\n"
        "- hybrid（默认推荐）：优先尝试 llm_enhanced，失败时自动回退 rule_based\n"
        "- 不确定时使用 hybrid"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "mode": {
                "type": "string",
                "enum": ["rule_based", "llm_enhanced", "hybrid"],
                "description": "压缩模式"
            },
            "conversation_history": {
                "type": "array",
                "description": "待压缩的对话历史，格式为 [{\"role\": \"user\"/\"assistant\"/\"system\", \"content\": \"...\"}]"
            }
        },
        "required": ["mode", "conversation_history"]
    }
}


def compress_conversation_history(
    mode: str,
    conversation_history: list[dict[str, Any]],
) -> dict[str, Any]:
    """压缩对话历史

    Args:
        mode: 压缩模式
        conversation_history: 待压缩的对话历史

    Returns:
        压缩结果，包含 compressed_history 和统计信息
    """
    original_count = len(conversation_history)

    if original_count <= DEFAULT_RECENT_COUNT:
        return {
            "success": True,
            "original_count": original_count,
            "compressed_count": original_count,
            "mode": mode,
            "compressed_history": conversation_history,
            "skipped": True,
            "reason": "消息数量未超过阈值，无需压缩"
        }

    try:
        if mode == "rule_based":
            compressed = _rule_based_compress(conversation_history)
        elif mode == "llm_enhanced":
            compressed = _llm_enhanced_compress(conversation_history)
        elif mode == "hybrid":
            compressed = _hybrid_compress(conversation_history)
        else:
            return {
                "success": False,
                "error": f"未知压缩模式: {mode}",
                "original_count": original_count,
                "compressed_count": 0,
                "mode": mode
            }

        return {
            "success": True,
            "original_count": original_count,
            "compressed_count": len(compressed),
            "mode": mode,
            "compressed_history": compressed
        }

    except Exception as e:
        logger.error(f"压缩对话历史失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "original_count": original_count,
            "compressed_count": 0,
            "mode": mode
        }


def _rule_based_compress(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """基于规则的压缩

    策略：
    1. 保留系统消息（第一条）
    2. 保留最近 N 条完整消息
    3. 中间消息用摘要替代
    """
    recent_count = DEFAULT_RECENT_COUNT
    result = []

    # 提取非系统消息
    non_system = [m for m in history if m.get("role") != "system"]
    system_messages = [m for m in history if m.get("role") == "system"]

    # 系统消息
    result.extend(system_messages)

    if len(non_system) <= recent_count:
        result.extend(non_system)
        return result

    # 保留最近消息
    recent = non_system[-recent_count:]
    # 压缩中间消息
    middle = non_system[:-recent_count]

    # 生成摘要
    summary = _generate_rule_based_summary(middle)

    # 添加摘要作为一条 assistant 消息
    if summary:
        result.append({
            "role": "assistant",
            "content": f"[对话历史摘要] 共 {len(middle)} 条消息已压缩：{summary}"
        })

    result.extend(recent)
    return result


def _generate_rule_based_summary(messages: list[dict[str, Any]]) -> str:
    """基于规则生成摘要

    提取关键信息：
    - 用户意图（设计类型、操作）
    - 关键实体（分类名、流程名、表单名）
    - 关键参数（审批节点数、表单字段等）
    """
    if not messages:
        return ""

    intents = []
    entities = []

    for msg in messages:
        content = msg.get("content", "")
        role = msg.get("role", "")

        if role == "user":
            # 提取用户意图
            if "设计" in content or "创建" in content:
                if "分类" in content:
                    intents.append("用户正在设计分类")
                elif "流程" in content:
                    intents.append("用户正在设计流程")
                elif "表单" in content:
                    intents.append("用户正在设计表单")

            # 提取关键实体
            category_match = re.search(r"分类[：:]\s*([^\n，,。]+)", content)
            if category_match:
                entities.append(f"分类: {category_match.group(1)}")

            flow_match = re.search(r"流程[：:]\s*([^\n，,。]+)", content)
            if flow_match:
                entities.append(f"流程: {flow_match.group(1)}")

            form_match = re.search(r"表单[：:]\s*([^\n，,。]+)", content)
            if form_match:
                entities.append(f"表单: {form_match.group(1)}")

        elif role == "assistant":
            # 提取助手的关键响应
            if "分类" in content and "编码" in content:
                key_match = re.search(r"编码[：:]\s*([A-Za-z0-9_]+)", content)
                if key_match:
                    entities.append(f"分类编码: {key_match.group(1)}")

            if "节点" in content:
                node_match = re.search(r"(\d+)\s*个节点", content)
                if node_match:
                    entities.append(f"节点数: {node_match.group(1)}")

    # 构建摘要
    parts = []
    if intents:
        parts.append("; ".join(set(intents)))
    if entities:
        parts.append("; ".join(set(entities)[:5]))  # 最多5个实体

    return " | ".join(parts) if parts else "多轮对话"


def _llm_enhanced_compress(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """基于 LLM 的智能压缩

    使用 LLM 生成语义完整的对话摘要
    """
    from app.agents.react_agent import create_llm

    recent_count = 2  # 保留最近2条完整消息
    non_system = [m for m in history if m.get("role") != "system"]
    system_messages = [m for m in history if m.get("role") == "system"]

    if len(non_system) <= recent_count + 1:
        return history

    # 准备需要摘要的消息
    to_summarize = non_system[:-recent_count]

    # 构建摘要提示
    summary_prompt = _build_summary_prompt(to_summarize)

    try:
        llm = create_llm()
        response = llm.invoke([{"role": "user", "content": summary_prompt}])
        summary = response.content if hasattr(response, "content") else str(response)

        result = list(system_messages)

        if summary.strip():
            result.append({
                "role": "assistant",
                "content": f"[对话历史摘要] {summary.strip()}"
            })

        result.extend(non_system[-recent_count:])

        return result

    except Exception as e:
        logger.warning(f"LLM 压缩失败，回退到规则压缩: {e}")
        return _rule_based_compress(history)


def _build_summary_prompt(messages: list[dict[str, Any]]) -> str:
    """构建摘要提示"""
    history_text = "\n".join([
        f"{'[用户]' if m.get('role') == 'user' else '[助手]'}: {m.get('content', '')[:200]}"
        for m in messages
    ])

    return f"""请为以下对话历史生成简洁摘要，保留关键信息：

{history_text}

要求：
1. 识别用户的主要意图和操作
2. 提取关键实体（分类、流程、表单、角色等）
3. 保留重要的参数和配置
4. 摘要长度不超过200字

直接输出摘要，无需解释。"""


def _hybrid_compress(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """混合压缩：优先 LLM，失败时回退规则"""
    try:
        return _llm_enhanced_compress(history)
    except Exception as e:
        logger.warning(f"hybrid 模式 LLM 压缩失败，回退到 rule_based: {e}")
        return _rule_based_compress(history)


__all__ = [
    "COMPRESS_CONVERSATION_HISTORY_SCHEMA",
    "compress_conversation_history",
]
