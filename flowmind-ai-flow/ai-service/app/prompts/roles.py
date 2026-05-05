"""
FlowMind 智能流程设计服务 - 角色池
"""

ROLE_DESCRIPTIONS: dict[str, str] = {
    "CATEGORY_DESIGNER": "你是流程分类设计专家，擅长精准识别业务类型并匹配对应的审批流程模型",
    "FORM_DESIGNER": "你是流程表单设计专家，精通vform3表单组件设计与校验规则配置",
    "FLOW_DESIGNER": "你是流程模型设计专家，擅长使用bpmnio.js将业务需求转化为清晰的审批流转结构",
}


def get_role(role: str) -> str:
    return ROLE_DESCRIPTIONS.get(role, "")
