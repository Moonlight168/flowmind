"""
FlowMind 智能审批服务 - ReAct Agent

本模块封装 LangGraph create_react_agent，提供：
- run_react_agent(): 统一入口
"""

import json
import re
from typing import Any

from json_repair import loads as repair_loads
from langgraph.prebuilt import create_react_agent

from app.adapters.factory import ModelFactory
from app.agents.tools.react_tools import create_tools
from app.config import Task
from app.infra.logger import logger
from app.prompts.builder import build_prompt


def run_react_agent(
    design_type: str,
    messages: list[dict],
    auth_token: str,
    current_form_data: dict[str, Any] | None = None,
    task_name: str | None = None,
    mode: str = "design",
) -> dict[str, Any]:
    """运行 ReAct Agent 并返回 LLM 输出的业务 JSON

    Args:
        design_type: 设计类型 (category_design/flow_design/form_design)
        messages: 已构建好的消息列表（包含对话历史，由 checkpoint 维护）
        auth_token: 认证令牌
        current_form_data: 当前表单数据状态
        task_name: 任务名称
        mode: 设计模式 ("design" | "basic")

    Returns:
        LLM 输出的业务 JSON
    """
    manager = ModelFactory.get_model_manager()
    llm = manager.create_llm(task_name=task_name)
    tools = create_tools(design_type, auth_token)

    # 构建系统提示词并添加到消息列表
    # 根据 mode 选择 Task
    task_map = {
        "flow_design": Task.FLOW_DESIGN_BASIC if mode == "basic" else Task.FLOW_DESIGN,
        "form_design": Task.FORM_DESIGN,
        "category_design": Task.CATEGORY_DESIGN,
    }
    task = task_map.get(design_type)
    if not task:
        raise ValueError(f"不支持的设计类型: {design_type}")

    prompt_text = build_prompt(task, variables={"current_form_data": current_form_data or {}})
    full_messages = [{"role": "system", "content": prompt_text}, *messages]

    llm_with_strict_tools = llm.bind_tools(tools, strict=True)
    agent = create_react_agent(llm_with_strict_tools, tools)

    logger.info(f"[LLM] 调用前: {len(full_messages)} 条消息, tools={len(tools)}, tool_names={[t.name for t in tools]}")

    result = agent.invoke(
        {"messages": full_messages},
        config={"recursion_limit": 15},
    )

    # 详细日志：打印所有消息
    for i, msg in enumerate(result["messages"]):
        msg_type = type(msg).__name__
        content_preview = str(msg.content)[:100] if hasattr(msg, 'content') else "N/A"
        tool_calls = getattr(msg, 'tool_calls', None)
        logger.info(f"[AGENT] msg[{i}] {msg_type}: {content_preview} | tool_calls={tool_calls}")

    final_content = result["messages"][-1].content
    logger.info(f"[LLM] 最终输出: {len(final_content)} 字符")

    return _parse_json_response(final_content)


def _parse_json_response(content: str) -> dict[str, Any]:
    """从 LLM 输出中提取 JSON

    处理多种输出格式：纯 JSON、Markdown 代码块、前置文本 + JSON、非法 JSON。
    非法 JSON 用 json-repair 库修复（未转义引号、单引号、尾逗号等常见 LLM 问题）。
    """
    try:
        text = content.strip()

        # 从 markdown 代码块中提取 JSON（支持前置文本 + 不完整代码块）
        code_block_match = re.search(r"```(?:json)?\s*\n?(.*)", text, re.DOTALL)
        if code_block_match:
            text = code_block_match.group(1).strip()
            if text.endswith("```"):
                text = text[:-3].strip()

        # 先用标准 raw_decode（忽略 JSON 后的自然语言总结）
        try:
            decoder = json.JSONDecoder()
            parsed, _ = decoder.raw_decode(text)
        except json.JSONDecodeError:
            # 标准解析失败 → 提取 { ... } 片段后用 json-repair 修复
            dict_match = re.search(r"\{.*\}", text, re.DOTALL)
            if dict_match:
                text = dict_match.group(0)
            parsed = repair_loads(text)

        if not isinstance(parsed, dict):
            logger.warning(f"LLM 返回了非 dict 类型: {type(parsed).__name__}")
            return {"intent": "clarification", "message": "LLM 输出格式错误，请重试"}
        return parsed
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.error(f"JSON 解析失败: {e}，原始内容：{content[:200]}...")
        return {"intent": "clarification", "message": "无法解析 LLM 输出，请重试"}

