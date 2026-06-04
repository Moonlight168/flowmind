"""
FlowMind 智能审批服务 - ReAct Agent

本模块封装 LangGraph create_react_agent，提供：
- run_react_agent(): 统一入口
"""

import ast
import json
import re
from typing import Any

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

    处理多种 LLM 输出格式：
    1. 纯 JSON
    2. Markdown 代码块包裹的 JSON
    3. 前置文本 + JSON + 后续文本
    4. JSON 后跟 LLM 的自然语言总结
    5. Python dict 格式（单引号，LLM 疲劳时可能出现）
    6. JSON 字符串值中包含未转义的双引号（常见 LLM 问题）
    """
    try:
        text = content.strip()

        # 尝试从 markdown 代码块中提取 JSON（支持前置文本）
        # 处理不完整的代码块（没有结束标记）
        code_block_match = re.search(r"```(?:json)?\s*\n?(.*)", text, re.DOTALL)
        if code_block_match:
            text = code_block_match.group(1).strip()
            # 移除可能存在的结束标记
            if text.endswith("```"):
                text = text[:-3].strip()

        # 使用 raw_decode 解析第一个完整 JSON 对象，忽略后续文本
        # 这解决了 LLM 输出 JSON 后跟自然语言总结的问题
        decoder = json.JSONDecoder()
        parsed, _ = decoder.raw_decode(text)

        # 确保返回的是 dict，不是 list 或其他类型
        if not isinstance(parsed, dict):
            logger.warning(f"LLM 返回了非 dict 类型: {type(parsed).__name__}, 内容: {str(parsed)[:100]}")
            return {"intent": "clarification", "message": "LLM 输出格式错误，请重试"}
        return parsed
    except json.JSONDecodeError:
        # JSON 解析失败，尝试修复常见的 LLM 输出问题
        logger.warning("JSON 解析失败，尝试修复常见问题")
        try:
            fixed_text = _fix_json_string_quotes(text)
            decoder = json.JSONDecoder()
            parsed, _ = decoder.raw_decode(fixed_text)
            if isinstance(parsed, dict):
                logger.info("成功修复 JSON 中的未转义引号")
                return parsed
        except (json.JSONDecodeError, Exception):
            pass

        # 尝试解析 Python dict 格式（单引号）
        try:
            dict_match = re.search(r"\{.*\}", text, re.DOTALL)
            if dict_match:
                dict_str = dict_match.group(0)
                parsed = ast.literal_eval(dict_str)
                if isinstance(parsed, dict):
                    logger.info("成功解析 Python dict 格式")
                    return parsed
        except (ValueError, SyntaxError) as e:
            logger.error(f"Python dict 解析失败：{e}")

        logger.error(f"JSON 解析失败，原始内容：{content[:200]}...")
        return {"intent": "clarification", "message": "无法解析 LLM 输出，请重试"}
    except (IndexError, Exception) as e:
        logger.error(f"JSON 解析异常：{e}，原始内容：{content[:200]}")
        return {"intent": "clarification", "message": "无法解析 LLM 输出，请重试"}


def _fix_json_string_quotes(text: str) -> str:
    """修复 JSON 字符串值中未转义的双引号

    常见 LLM 问题：{"message": "他说"你好""}
    修复为：{"message": "他说\"你好\""}
    """
    # 匹配 JSON 字符串值中的内容
    # 策略：找到 "key": "value" 模式，确保 value 内的引号被转义
    result = []
    in_string = False
    in_key = False
    escape_next = False
    string_start = -1

    i = 0
    while i < len(text):
        char = text[i]

        if escape_next:
            result.append(char)
            escape_next = False
            i += 1
            continue

        if char == '\\':
            result.append(char)
            escape_next = True
            i += 1
            continue

        if char == '"':
            if not in_string:
                # 进入字符串
                in_string = True
                string_start = len(result)
                result.append(char)
            else:
                # 检查是否是字符串结束
                # 如果下一个字符是 : , } ] 或空白，说明字符串结束
                next_chars = text[i+1:i+3].lstrip() if i+1 < len(text) else ""
                if not next_chars or next_chars[0] in ':,}]':
                    # 字符串结束
                    in_string = False
                    result.append(char)
                else:
                    # 字符串内部的引号，需要转义
                    result.append('\\"')
            i += 1
            continue

        result.append(char)
        i += 1

    return ''.join(result)
