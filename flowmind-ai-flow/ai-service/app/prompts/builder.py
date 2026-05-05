"""
FlowMind 智能流程设计服务 - Prompt 构建器
"""

import importlib
from typing import Any

from app.config.llm_task import Task, get_task_config
from app.prompts.roles import get_role


def build_prompt(task: "Task | str", variables: dict[str, Any]) -> str:
    """构建 Prompt（分层组装）"""
    if isinstance(task, str):
        task = Task(task)

    config = get_task_config(task)
    if not config:
        raise ValueError(f"任务 {task} 未找到配置")

    role = get_role(config.role)
    task_module = _import_task_module(config.module)
    inputs = _format_variables(variables)

    return f"{role}。\n\n{task_module.TASK}。\n\n{inputs}"


def _import_task_module(module_path: str):
    return importlib.import_module(module_path)


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
        "context": _format_context,
        "conversation_history": _format_conversation_history,
        "available_categories": _format_category_list,
        "available_roles": _format_role_list,
        "available_forms": _format_form_list,
        "current_form_data": _format_current_flow,
    }
    return formatters.get(key, _format_default)


def _format_context(value: dict) -> str:
    if not value:
        return "context: 无"
    lines = []
    for k, v in value.items():
        if k == "conversation_history":
            lines.append(_format_conversation_history(v))
        elif k != "confirmed_data" and v:
            lines.append(f"{k}: {v}")
    return "\n".join(lines) if lines else "context: 无"


def _format_conversation_history(value: list) -> str:
    if not value:
        return "conversation_history: 无"
    lines = ["conversation_history:"]
    for item in value:
        role = item.get("role", "")
        content = item.get("content", "")
        lines.append(f"  {role}: {content}")
    return "\n".join(lines)


def _format_category_list(value: list) -> str:
    if not value:
        return "【可用分类】: （暂无）"
    lines = ["【可用分类】:"]
    for cat in value:
        lines.append(f"  - [{cat.get('code', '')}] {cat.get('name', '')}")
    return "\n".join(lines)


def _format_role_list(value: list) -> str:
    if not value:
        return "【可用角色】: （暂无）"
    lines = ["【可用角色】:"]
    for r in value:
        lines.append(f"  - [{r.get('key', '')}] {r.get('name', '')}")
    return "\n".join(lines)


def _format_form_list(value: list) -> str:
    if not value:
        return "【可用表单】: （暂无）"
    lines = ["【可用表单】:"]
    for f in value:
        lines.append(f"  - [{f.get('id', '')}] {f.get('name', '')}")
    return "\n".join(lines)


def _format_current_flow(value: dict) -> str:
    if not value:
        return "【当前流程信息】: （新建流程）"
    lines = ["【当前流程信息】:"]
    for k, v in value.items():
        if v:
            lines.append(f"  {k}: {v}")
    return "\n".join(lines)


def _format_default(value: Any) -> str:
    if value is None or value == "":
        return ""
    return f"{value}"
