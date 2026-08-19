"""
FlowMind 智能审批服务 - 设计 Agent

结构化输出为主路径：with_structured_output + Pydantic schema 约束 LLM 输出。
失败重试(≤3)，耗尽返回 error（不甩锅用户）。
"""

import json
from typing import Any

from pydantic import ValidationError

from app.adapters.factory import ModelFactory
from app.agents.design_spec import DESIGN_SPEC, prefetch_summaries
from app.config import Task
from app.domain.schemas.pydantic_models import BasicDesign
from app.infra.logger import logger
from app.prompts.builder import build_prompt

MAX_STRUCTURED_RETRY = 3


def run_react_agent(
    design_type: str,
    messages: list[dict],
    auth_token: str,
    current_form_data: dict[str, Any] | None = None,
    task_name: str | None = None,
    mode: str = "design",
) -> dict[str, Any]:
    """运行设计 Agent：结构化输出，失败重试(≤3)→error

    Args:
        design_type: 设计类型 (category_design/flow_design/form_design)
        messages: 已构建好的消息列表（包含对话历史）
        auth_token: 认证令牌
        current_form_data: 当前表单数据状态（增量修改的基线）
        task_name: 任务名称
        mode: 设计模式 ("design" | "basic")

    Returns:
        LLM 输出的业务 JSON（或 {"intent":"error", ...}）
    """
    manager = ModelFactory.get_model_manager()

    # 根据 mode 选择 Task
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

    # 选 schema：basic 模式用 BasicDesign，否则按 DESIGN_SPEC
    if mode == "basic":
        schema = BasicDesign
        # basic 模式也预取分类（code 从分类选，避免编造）
        try:
            summaries = prefetch_summaries("category_design", auth_token)
            if summaries:
                full_messages[0]["content"] = _append_summaries(prompt_text, summaries)
        except (
            RuntimeError,
            ValueError,
            TypeError,
            KeyError,
            OSError,
            AttributeError,
        ) as e:
            logger.warning(f"[design] 预取失败（置空继续）: {e}")
    else:
        spec = DESIGN_SPEC.get(design_type)
        if not spec:
            raise ValueError(f"不支持的设计类型: {design_type}")
        schema = spec["schema"]
        # 预取（单独 try，失败置空继续，不降级、不影响生成）
        try:
            summaries = prefetch_summaries(design_type, auth_token)
            if summaries:
                full_messages[0]["content"] = _append_summaries(prompt_text, summaries)
        except (
            RuntimeError,
            ValueError,
            TypeError,
            KeyError,
            OSError,
            AttributeError,
        ) as e:
            logger.warning(f"[design] 预取失败（置空继续）: {e}")

    # 结构化输出（重试 ≤3 次）
    last_error = None
    for attempt in range(1, MAX_STRUCTURED_RETRY + 1):
        try:
            llm = manager.create_llm(task_name=task_name, structured=True)
            obj = llm.with_structured_output(schema).invoke(full_messages)
            if obj is not None:
                logger.info("[LLM] 结构化输出成功")
                return obj.model_dump()
            last_error = ValueError("结构化输出返回 None")
            logger.warning(
                f"[LLM] 结构化输出返回 None（第 {attempt}/{MAX_STRUCTURED_RETRY} 次）"
            )
        except (
            ValidationError,
            RuntimeError,
            ValueError,
            TypeError,
            KeyError,
            OSError,
            AttributeError,
        ) as e:
            last_error = e
            logger.warning(
                f"[LLM] 结构化输出失败（第 {attempt}/{MAX_STRUCTURED_RETRY} 次）: {e}"
            )

    logger.error(f"[LLM] 结构化输出重试耗尽: {last_error}")
    return {"intent": "error", "message": "AI 服务暂时异常，请稍后重试"}


def _append_summaries(prompt_text: str, summaries: dict) -> str:
    """把预取的真实数据摘要拼进 prompt，让 LLM 从真实数据选而非编造"""
    lines = [
        '\n\n## 可用数据（直接从以下真实数据中选择，禁止编造；忽略上文所有"调用工具"的指令）'
    ]
    for name, rows in summaries.items():
        if rows:
            lines.append(f"- {name}: {json.dumps(rows, ensure_ascii=False)}")
        else:
            lines.append(f"- {name}: 空（无可用数据，对应字段留空）")
    return prompt_text + "\n".join(lines)
