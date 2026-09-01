"""
FlowMind 智能流程设计服务 - Prompt 构建器
"""

import json
import re
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
    """格式化流程基本信息为提示词片段"""
    if not current_form_data:
        return "（新流程，尚无基本信息）"

    lines = []
    # 兼容前端和后端的不同字段名
    flow_name = current_form_data.get("flow_name") or current_form_data.get("modelName")
    code = current_form_data.get("code") or current_form_data.get("category")
    description = current_form_data.get("description")
    bpmn_xml = current_form_data.get("bpmnXml") or current_form_data.get("bpmn_xml")
    nodes = current_form_data.get("nodes")
    edges = current_form_data.get("edges")

    if flow_name:
        lines.append(f"- 流程名称：{flow_name}")
    if code:
        lines.append(f"- 分类编码：{code}")
    if description:
        lines.append(f"- 流程描述：{description}")

    if nodes:
        # nodes 优先：传完整结构（而非节点名），让 LLM 在完整结构上增量修改，保留用户手动改的审批人/表单绑定
        lines.append("现有流程结构（完整，必须在此基础上增量修改）：")
        lines.append(f"nodes: {json.dumps(nodes, ensure_ascii=False)}")
        lines.append(f"edges: {json.dumps(edges or [], ensure_ascii=False)}")
        lines.append(
            "- 只修改用户指令提到的内容，未提及的节点/连线/审批人/表单绑定【逐字保留】原样返回"
        )
        lines.append("- 完整返回 nodes + edges（含保留的节点，不是只返回改动部分）")
    elif bpmn_xml:
        lines.append("- 已有流程编排，用户正在修改现有流程")
        # 尝试从 bpmnXml 中提取节点信息供 AI 参考（无 nodes 时的 fallback）
        try:
            # 提取 userTask 节点名称
            task_names = re.findall(r'<bpmn2?:userTask[^>]*name="([^"]*)"', bpmn_xml)
            if task_names:
                lines.append(f"- 现有审批节点：{', '.join(task_names)}")
        except TypeError:
            pass
    else:
        lines.append("- 尚无流程编排，将全新生成")

    return "\n".join(lines) if lines else "（新流程，尚无基本信息）"


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
