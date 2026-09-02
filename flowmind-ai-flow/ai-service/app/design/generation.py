"""
FlowMind 智能流程设计服务 - 设计 Agent

ReAct 主路径：create_react_agent 边推理边调检索工具取真实数据，
最终用结构化输出（response_format）约束字段。
失败重试(≤3)，耗尽返回 error（不甩锅用户）。
"""

from typing import Any

from langgraph.prebuilt import create_react_agent
from pydantic import ValidationError

from app.config import Task
from app.design.spec import DESIGN_SPEC
from app.design.tools import search_categories
from app.domain.design_models import BasicDesign
from app.infra.logger import logger
from app.infra.observability import langchain_config
from app.llm import ModelExhaustedError, get_model_runtime
from app.prompts.builder import build_prompt
from app.prompts.loader import load_prompt

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
    runtime = get_model_runtime()

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
    for attempt in range(1, MAX_STRUCTURED_RETRY + 1):
        try:
            result = runtime.execute(
                task_name,
                lambda llm: _invoke_agent(llm, tools, schema, full_messages),
                structured=True,
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
        except ModelExhaustedError as e:
            last_error = e
            logger.warning(f"[LLM] 可用 Provider 已耗尽: {e}")
            break

    logger.error(f"[LLM] 结构化输出重试耗尽: {last_error}")
    return {"intent": "error", "message": "AI 服务暂时异常，请稍后重试"}


def _invoke_agent(llm: Any, tools: list[Any], schema: Any, messages: list[dict]):
    """使用指定模型构建并执行一次 ReAct Agent。"""
    versioned_tools = [
        tool.model_copy(update={"description": load_prompt(f"tools/{tool.name}.md")})
        for tool in tools
    ]
    agent = create_react_agent(llm, versioned_tools, response_format=schema)
    return agent.invoke({"messages": messages}, config=langchain_config())
