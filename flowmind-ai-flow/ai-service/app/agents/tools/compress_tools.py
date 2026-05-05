"""
FlowMind 智能流程设计服务 - 压缩工具
"""

from typing import Any

from app.infra.logger import logger

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
    """压缩对话历史（暂未实现）"""
    original_count = len(conversation_history)

    logger.warning("compress_conversation_history 暂未实现，返回原始历史")

    return {
        "success": True,
        "original_count": original_count,
        "compressed_count": original_count,
        "mode": mode,
        "compressed_history": conversation_history
    }
