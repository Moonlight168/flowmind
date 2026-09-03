"""
FlowMind 智能流程设计服务 - Markdown 提示词单元测试
"""

import json
from pathlib import Path

from app.config.llm_task import Task, get_all_task_configs
from app.design.tools import (
    search_categories,
    search_flow_models,
    search_forms,
    search_roles,
)
from app.design.validators import ValidationError
from app.graph.nodes.review import _build_error_feedback
from app.prompts.builder import build_prompt
from app.prompts.loader import load_prompt, render_prompt


def test_all_task_prompts_are_markdown_documents() -> None:
    """所有任务配置都指向可读取的 Markdown 提示词。"""
    for config in get_all_task_configs().values():
        assert config.prompt.endswith(".md")
        assert load_prompt(config.prompt)


def test_render_prompt_only_replaces_named_variables() -> None:
    """渲染时保留 JSON、BPMN 表达式中的花括号。"""
    prompt = render_prompt(
        "tasks/flow_model_design.md",
        {"flow_basic_info": "- 流程名称：请假"},
    )

    assert "- 流程名称：请假" in prompt
    assert '"op":"add_node"' in prompt
    assert "结构化 condition" in prompt


def test_render_prompt_does_not_replace_placeholders_inside_values() -> None:
    """变量值中的占位符字面量不会被递归替换。"""
    prompt = render_prompt(
        "agents/intent.md",
        {
            "design_context": "当前设计包含 {user_input}",
            "user_input": "真实输入",
        },
    )

    assert "当前设计包含 {user_input}" in prompt
    assert "用户输入：真实输入" in prompt


def test_build_prompt_combines_markdown_layers() -> None:
    """角色、任务、领域知识与公共约束仍按原链路组装。"""
    prompt = build_prompt(
        Task.FLOW_DESIGN,
        {"current_form_data": {"flow_name": "请假流程"}},
    )

    assert prompt.startswith("你是流程模型设计专家")
    assert '"flow_name": "请假流程"' in prompt
    assert "# BPMN 设计约束" in prompt
    assert "## 意图识别" in prompt


def test_tool_descriptions_come_from_markdown() -> None:
    """ReAct 工具描述也纳入统一提示词管理。"""
    tools = [
        (search_categories, "tools/search_categories.md"),
        (search_forms, "tools/search_forms.md"),
        (search_roles, "tools/search_roles.md"),
        (search_flow_models, "tools/search_flow_models.md"),
    ]

    for tool, prompt_path in tools:
        assert tool.description == load_prompt(prompt_path)


def test_review_feedback_is_rendered_from_markdown() -> None:
    """校验反馈保留动态网关信息并通过 Markdown 模板组装。"""
    feedback = _build_error_feedback(
        [ValidationError("NODE_N006", "网关 'Gateway_1' 出边数量不足")],
        {
            "nodes": [{"id": "Gateway_1", "name": "金额判断"}],
            "edges": [{"source": "Gateway_1", "target": "approve"}],
        },
    )

    assert feedback.startswith(load_prompt("agents/review_feedback.md").splitlines()[0])
    assert '排他网关 "金额判断"(id=Gateway_1) 当前只有 1 条出边' in feedback


def test_all_runtime_prompts_are_explicitly_versioned() -> None:
    prompt_root = Path(__file__).parents[2] / "app" / "prompts"
    registry = json.loads((prompt_root / "versions.json").read_text(encoding="utf-8"))
    registered = set(registry["prompts"])
    markdown_files = {
        path.relative_to(prompt_root).as_posix() for path in prompt_root.rglob("*.md")
    }

    assert markdown_files == registered
