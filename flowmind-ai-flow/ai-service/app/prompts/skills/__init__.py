"""
FlowMind 智能流程设计服务 - Prompt Skills

本模块提供可注入 system prompt 的领域知识文档。
"""

from app.prompts.skills.bpmn_design import BPMN_DESIGN_SKILL

__all__ = [
    "BPMN_DESIGN_SKILL",
]
