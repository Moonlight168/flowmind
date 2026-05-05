"""
FlowMind 智能流程设计服务 - 表单设计 Agent

本模块实现独立的表单设计 Agent，用于表单填充场景。
"""
from app.adapters.llm.core.llm_client import get_llm_client
from app.config import Task, get_task_config
from app.infra.logger import logger
from app.prompts.builder import build_prompt
from app.utils.vform3_transformer import transform_to_vform3


class DesignFormAgent:
    """专门用于表单填充的表单生成 Agent"""

    def __init__(self):
        pass

    def generate(self, user_input: str, history: list[dict], current_form_data: dict | None = None) -> dict:
        """生成表单数据

        Args:
            user_input: 用户输入
            history: 对话历史
            current_form_data: 当前表单数据

        Returns:
            dict: 包含 form_data（完整 VForm3 JSON）, message
        """
        try:
            conversation_history = _build_history(history)

            variables = {
                "user_input": user_input,
                "conversation_history": conversation_history or [],
                "current_form_data": current_form_data or {},
            }

            llm_client = get_llm_client()
            prompt = build_prompt(Task.FORM_GENERATION, variables)
            result = llm_client.generate_json_with_retry(
                prompt,
                schema_name=get_task_config(Task.FORM_GENERATION).schema,
                task_name="design_form"
            )

            if not result:
                default_form = _get_default_form_json()
                return {
                    "form_data": default_form,
                    "form_name": "默认表单",
                    "message": "抱歉，无法理解您的需求，请重新描述。"
                }

            # 将 AI 简化格式转换为完整 VForm3 JSON
            form_json = transform_to_vform3(result)

            # 返回完整 VForm3 JSON（前端直接 setFormJson），
            # 同时带上 formName 供前端设置标题
            return {
                "form_data": form_json,
                "form_name": result.get("form_name", "默认表单"),
                "message": f"已为您生成【{result.get('form_name', '默认表单')}】表单"
            }

        except Exception as e:
            logger.error(f"DesignFormAgent 生成失败：{e}", exc_info=True)
            default_form = _get_default_form_json()
            return {
                "form_data": default_form,
                "form_name": "默认表单",
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


def _get_default_form_json() -> dict:
    """获取默认表单 JSON（完整 VForm3 格式）"""
    return {
        "widgetList": [],
        "formConfig": {
            "modelName": "formData",
            "refName": "vForm",
            "rulesName": "rules",
            "labelWidth": 80,
            "labelPosition": "left",
            "size": "",
            "labelAlign": "label-left-align",
            "cssCode": "",
            "customClass": "",
            "functions": "",
            "layoutType": "PC",
            "jsonVersion": 3,
            "onFormCreated": "",
            "onFormMounted": "",
            "onFormDataChange": "",
            "onFormValidate": "",
        },
    }
