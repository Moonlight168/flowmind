"""
FlowMind 智能流程设计服务 - 流程设计 Agent

本模块实现独立的流程设计 Agent，用于表单填充场景。
Agent 会查询已有的流程分类、角色和表单，为 LLM 提供上下文。
"""
from app.adapters.backend.category import CategoryService
from app.adapters.backend.form import FormService
from app.adapters.backend.role import RoleService
from app.adapters.llm.core.llm_client import get_llm_client
from app.config import Task, get_task_config
from app.core.auth_context import get_auth_token
from app.infra.logger import logger
from app.prompts.builder import build_prompt


class DesignFlowAgent:
    """专门用于表单填充的流程生成 Agent"""

    def generate(self, user_input: str, history: list[dict], current_form_data: dict | None = None, mode: str = "design") -> dict:
        """生成流程数据

        Args:
            user_input: 用户输入
            history: 对话历史
            current_form_data: 当前表单数据
            mode: 设计模式 - "basic" 仅返回基本信息，"design" 含 BPMN XML

        Returns:
            dict: 包含 form_data, bpmn_xml, message
        """
        try:
            conversation_history = _build_history(history)

            # 按模式查询所需资源，减少不必要的请求和 token 消耗
            variables = {
                "user_input": user_input,
                "conversation_history": conversation_history or [],
                "current_form_data": current_form_data or {},
            }

            if mode == "basic":
                variables["available_categories"] = _get_available_categories()
            elif mode == "design":
                variables["available_roles"] = _get_available_roles()
                variables["available_forms"] = _get_available_forms()

            llm_client = get_llm_client()
            prompt = build_prompt(Task.FLOW_DESIGN, variables)
            result = llm_client.generate_json_with_retry(
                prompt,
                schema_name=get_task_config(Task.FLOW_DESIGN).schema,
                task_name="design_flow"
            )

            if not result:
                return {
                    "form_data": {"flow_name": "", "category_id": ""},
                    "bpmn_xml": "",
                    "message": "抱歉，无法理解您的需求，请重新描述。"
                }

            flow_name = result.get("flow_name", "")
            category_id = result.get("category_id", "")
            description = result.get("description", "")
            nodes = result.get("nodes", [])

            # 从 nodes 生成 BPMN XML（仅 design 模式）
            bpmn_xml = ""
            if nodes and mode == "design":
                bpmn_category = {
                    "categoryName": flow_name or "流程",
                    "code": category_id or "default",
                }
                bpmn_xml = _generate_bpmn({"nodes": nodes}, bpmn_category)

            return {
                "form_data": {
                    "flow_name": flow_name,
                    "category_id": category_id,
                    "description": description,
                },
                "bpmn_xml": bpmn_xml,
                "message": f"已为您生成【{flow_name}】流程",
            }

        except Exception as e:
            logger.error(f"DesignFlowAgent 生成失败：{e}", exc_info=True)
            return {
                "form_data": {"flow_name": "", "category_id": ""},
                "bpmn_xml": "",
                "message": "服务暂时不可用，请稍后重试。"
            }


def _build_history(history: list[dict]) -> list[dict]:
    """构建对话历史"""
    if not history:
        return []
    return [
        {"role": msg.get("role", ""), "content": msg.get("content", "")}
        for msg in history
        if msg.get("role") in ("user", "assistant")
    ]


def _get_available_categories() -> list[dict[str, str]]:
    """获取所有可用的流程分类"""
    try:
        auth_token = get_auth_token()
        service = CategoryService(auth_token=auth_token)
        categories = service.search_categories()
        return [
            {"name": cat.get("categoryName", ""), "code": cat.get("code", "")}
            for cat in categories
            if cat.get("code")
        ]
    except Exception as e:
        logger.warning(f"查询可用分类失败：{e}")
        return []


def _get_available_roles() -> list[dict[str, str]]:
    """获取所有可用的角色

    返回格式与前端手动设计一致：
    - key: "ROLE{roleId}"（candidateGroups 值）
    - name: roleName（显示名称）
    """
    try:
        auth_token = get_auth_token()
        service = RoleService(auth_token=auth_token)
        roles = service.search_roles()
        return [
            {"name": role.get("roleName", ""), "key": f"ROLE{role.get('roleId', '')}"}
            for role in roles
            if role.get("roleId")
        ]
    except Exception as e:
        logger.warning(f"查询可用角色失败：{e}")
        return []


def _get_available_forms() -> list[dict[str, str]]:
    """获取所有可用的流程表单"""
    try:
        auth_token = get_auth_token()
        service = FormService(auth_token=auth_token)
        forms = service.search_forms()
        return [
            {"name": form.get("formName", ""), "id": str(form.get("formId", ""))}
            for form in forms
            if form.get("formId")
        ]
    except Exception as e:
        logger.warning(f"查询可用表单失败：{e}")
        return []


def _generate_bpmn(bpmn_structure: dict, category: dict) -> str:
    """生成 BPMN XML"""
    try:
        from app.agents.tools.flow_tools import generate_bpmn_xml

        return generate_bpmn_xml(bpmn_structure, category)
    except Exception as e:
        logger.warning(f"生成 BPMN XML 失败：{e}")
        return ""
