"""
FlowMind 智能流程设计服务 - BPMN Skill 加载测试
"""

from app.config.llm_task import Task
from app.prompts.builder import build_prompt


def test_flow_design_prompt_contains_bpmn_skill():
    prompt = build_prompt(
        Task.FLOW_DESIGN,
        {"current_form_data": {"modelName": "测试流程", "category": "1"}},
    )
    assert "BPMN 设计约束" in prompt
    assert "EXCLUSIVE_GATEWAY" in prompt
    assert "排他分支" in prompt
    assert "禁止自环" in prompt


def test_category_design_prompt_no_bpmn_skill():
    prompt = build_prompt(Task.CATEGORY_DESIGN, {"current_form_data": {}})
    assert "BPMN 设计约束" not in prompt
