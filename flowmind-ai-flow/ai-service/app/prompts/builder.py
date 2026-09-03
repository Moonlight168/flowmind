"""
FlowMind 智能流程设计服务 - Prompt 构建器
"""

import json
from typing import Any

from app.config.llm_task import Task, get_task_config
from app.prompts.loader import load_prompt, render_prompt
from app.prompts.roles import get_role


def build_prompt(task: "Task | str", variables: dict[str, Any]) -> str:
    """构建 Prompt（分层组装）"""
    if isinstance(task, str):
        task = Task(task)

    config = get_task_config(task)
    if not config:
        raise ValueError(f"任务 {task} 未找到配置")

    role = get_role(config.role)
    # 格式化 current_form_data 为 flow_basic_info
    current_form_data = variables.get("current_form_data", {})
    flow_basic_info = _format_flow_basic_info(current_form_data)

    # 使用手动替换避免 ${initiator} 等被误解析
    task_text = render_prompt(
        config.prompt,
        {"flow_basic_info": flow_basic_info},
    )

    # 根据任务类型注入领域知识 skill
    skill_text = _load_task_skill(task)

    parts = [role, task_text]
    if skill_text:
        parts.append(skill_text)
    parts.append(load_prompt("shared/design_intent.md"))

    return "\n\n".join(parts)


def _format_variables(variables: dict[str, Any]) -> str:
    """格式化所有变量为 Prompt 文本"""
    lines = []
    for key, value in variables.items():
        formatter = _get_formatter(key)
        formatted = formatter(value)
        if formatted:
            lines.append(formatted)
    return "\n".join(lines)


def _get_formatter(key: str):
    """根据变量名获取格式化器"""
    formatters = {
        "current_form_data": _format_current_form_data,
    }
    return formatters.get(key, _format_default)


def _format_current_form_data(value: dict) -> str:
    """格式化当前表单数据"""
    if not value:
        return "【当前表单数据】: （新建）"
    lines = ["【当前表单数据】:"]
    for k, v in value.items():
        if v:
            lines.append(f"  {k}: {v}")
    return "\n".join(lines)


def _format_flow_basic_info(current_form_data: dict) -> str:
    """Format the normalized artifact baseline without large serialized blobs."""
    if not current_form_data:
        return "（空白设计）"
    omitted = {"bpmnXml", "bpmn_xml", "content"}
    baseline = {
        key: value
        for key, value in current_form_data.items()
        if key not in omitted and value not in (None, "")
    }
    return json.dumps(baseline, ensure_ascii=False, indent=2)


def _format_default(value: Any) -> str:
    if value is None or value == "":
        return ""
    return f"{value}"


_TASK_SKILL_MAP: dict[str, str] = {
    Task.FLOW_DESIGN.value: "skills/bpmn_design.md",
}


def _load_task_skill(task: "Task") -> str:
    """根据任务类型加载对应的 skill 知识文档"""
    prompt_path = _TASK_SKILL_MAP.get(task.value)
    return load_prompt(prompt_path) if prompt_path else ""
