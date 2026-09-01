"""
FlowMind 智能流程设计服务 - 设计 Agent

ReAct 主路径：create_react_agent 边推理边调检索工具取真实数据，
最终用结构化输出（response_format）约束字段。
失败重试(≤3)，耗尽返回 error（不甩锅用户）。
"""

from typing import Any

import httpx
from langgraph.prebuilt import create_react_agent
from openai import OpenAIError
from pydantic import ValidationError

from app.adapters.factory import ModelFactory
from app.agents.design_spec import DESIGN_SPEC
from app.agents.tools import search_categories
from app.config import Task
from app.domain.schemas.pydantic_models import BasicDesign
from app.infra.logger import logger
from app.infra.observability import langchain_config
from app.prompts.builder import build_prompt

MAX_STRUCTURED_RETRY = 3


def run_react_agent(
    design_type: str,
    messages: list[dict],
    current_form_data: dict[str, Any] | None = None,
    task_name: str | None = None,
    mode: str = "design",
) -> dict[str, Any]:
    """运行设计 Agent：ReAct 检索 + 结构化输出，失败重试(≤3)→error

    Args:
        design_type: 设计类型 (category_design/flow_design/form_design)
        messages: 已构建好的消息列表（包含对话历史）
        current_form_data: 当前表单数据状态（增量修改的基线）
        task_name: 任务名称
        mode: 设计模式 ("design" | "basic")

    Returns:
        LLM 输出的业务 JSON（或 {"intent":"error", ...}）
    """
    manager = ModelFactory.get_model_manager()

    task_map = {
        "flow_design": Task.FLOW_DESIGN_BASIC if mode == "basic" else Task.FLOW_DESIGN,
        "form_design": Task.FORM_DESIGN,
        "category_design": Task.CATEGORY_DESIGN,
    }
    task = task_map.get(design_type)
    if not task:
        raise ValueError(f"不支持的设计类型: {design_type}")

    prompt_text = build_prompt(
        task, variables={"current_form_data": current_form_data or {}}
    )
    full_messages = [{"role": "system", "content": prompt_text}, *messages]

    # 选 schema + 工具集：basic 模式用 BasicDesign + 仅分类工具
    if mode == "basic":
        schema = BasicDesign
        tools = [search_categories]
    else:
        spec = DESIGN_SPEC.get(design_type)
        if not spec:
            raise ValueError(f"不支持的设计类型: {design_type}")
        schema = spec["schema"]
        tools = spec["tools"]

    last_error: Exception | None = None
    failed_providers: set[str] = set()
    for attempt in range(1, MAX_STRUCTURED_RETRY + 1):
        provider: str | None = None
        try:
            llm, provider = manager.create_llm_with_provider(
                task_name=task_name,
                structured=True,
                excluded_providers=failed_providers,
            )
            agent = create_react_agent(llm, tools, response_format=schema)
            result = agent.invoke(
                {"messages": full_messages}, config=langchain_config()
            )
            obj = result.get("structured_response")
            if obj is not None:
                logger.info("[LLM] ReAct 结构化输出成功")
                return obj.model_dump() if hasattr(obj, "model_dump") else obj
            last_error = ValueError("结构化输出返回 None")
            logger.warning(
                f"[LLM] 结构化输出返回 None（第 {attempt}/{MAX_STRUCTURED_RETRY} 次）"
            )
        except (
            ValidationError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        ) as e:
            last_error = e
            logger.warning(
                f"[LLM] 结构化输出失败（第 {attempt}/{MAX_STRUCTURED_RETRY} 次）: {e}"
            )
        except (
            OpenAIError,
            httpx.HTTPError,
            ConnectionError,
            TimeoutError,
            OSError,
            RuntimeError,
        ) as e:
            last_error = e
            if provider:
                failed_providers.add(provider)
            logger.warning(
                f"[LLM] provider={provider or 'unknown'} 调用失败，"
                f"尝试备用模型（第 {attempt}/{MAX_STRUCTURED_RETRY} 次）: {e}"
            )

    logger.error(f"[LLM] 结构化输出重试耗尽: {last_error}")
    return {"intent": "error", "message": "AI 服务暂时异常，请稍后重试"}
