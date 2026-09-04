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
    assert "BPMN 流程设计规范" in prompt
    assert "EXCLUSIVE_GATEWAY" in prompt
    assert "排他网关" in prompt
    assert "条件分支审批" in prompt
    assert "DATA_OBJECT" in prompt
    assert "SUB_PROCESS" in prompt


def test_category_design_prompt_no_bpmn_skill():
    prompt = build_prompt(Task.CATEGORY_DESIGN, {"current_form_data": {}})
    assert "BPMN 流程设计规范" not in prompt
