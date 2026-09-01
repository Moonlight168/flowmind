"""
FlowMind 智能流程设计服务 - 角色池
"""

from app.prompts.loader import load_prompt

ROLE_PROMPTS: dict[str, str] = {
    "CATEGORY_DESIGNER": "roles/category_designer.md",
    "FORM_DESIGNER": "roles/form_designer.md",
    "FLOW_DESIGNER": "roles/flow_designer.md",
}


def get_role(role: str) -> str:
    prompt_path = ROLE_PROMPTS.get(role)
    return load_prompt(prompt_path) if prompt_path else ""
