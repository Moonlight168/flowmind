"""
FlowMind 智能流程设计服务 - 分类设计 Agent

本模块实现独立的分类设计 Agent，用于表单填充场景。
"""
from app.adapters.llm.core.llm_client import get_llm_client
from app.config import Task, get_task_config
from app.infra.logger import logger
from app.prompts.builder import build_prompt


class DesignCategoryAgent:
    """专门用于表单填充的分类生成 Agent"""

    def __init__(self):
        pass

    def generate(self, user_input: str, history: list[dict], current_form_data: dict | None = None) -> dict:
        """生成表单数据

        Args:
            user_input: 用户输入
            history: 对话历史 [{"role": "user/assistant", "content": "..."}]
            current_form_data: 当前表单数据，用于提供上下文

        Returns:
            dict: 包含 form_data 和 message
        """
        try:
            conversation_history = _build_history(history)

            variables = {
                "user_input": user_input,
                "conversation_history": conversation_history or [],
                "current_form_data": current_form_data or {},
            }

            llm_client = get_llm_client()
            prompt = build_prompt(Task.CATEGORY_CLASSIFICATION, variables)
            result = llm_client.generate_json_with_retry(
                prompt,
                schema_name=get_task_config(Task.CATEGORY_CLASSIFICATION).schema,
                task_name="design_category"
            )

            if not result:
                return {
                    "form_data": {
                        "category_name": "默认分类",
                        "code": "DEFAULT",
                        "remark": ""
                    },
                    "message": "抱歉，无法理解您的需求，请重新描述。"
                }

            form_data = {
                "category_name": result.get("category_name", ""),
                "code": result.get("code", ""),
                "remark": result.get("remark", "")
            }

            return {
                "form_data": form_data,
                "message": f"已为您生成【{form_data['category_name']}】分类"
            }

        except Exception as e:
            logger.error(f"DesignCategoryAgent 生成失败：{e}", exc_info=True)
            return {
                "form_data": {
                    "category_name": "默认分类",
                    "code": "DEFAULT",
                    "remark": ""
                },
                "message": "服务暂时不可用，请稍后重试。"
            }


def _build_history(history: list[dict]) -> list[dict]:
    """构建对话历史"""
    if not history:
        return []
    result = []
    for msg in history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role in ("user", "assistant"):
            result.append({"role": role, "content": content})
    return result
