"""
FlowMind 智能流程设计服务 - 流程模型服务

本模块提供流程模型相关的业务逻辑，包括模型查询、创建等。
"""

from typing import Any

import requests

from app.config.settings import settings
from app.infra.logger import logger
from app.integrations.backend.client import BackendClient


class FlowModelClient(BackendClient):
    """流程模型服务

    继承 BackendClient，自动处理认证令牌。
    """

    @property
    def api_path(self) -> str:
        """获取流程模型 API 路径"""
        return settings.backend.flow_model_api_path

    def search_flow_models(
        self, model_name: str | None = None, model_key: str | None = None
    ) -> list[dict[str, Any]]:
        """搜索流程模型（支持按名称或key搜索）

        Args:
            model_name: 流程模型名称（可选）
            model_key: 流程模型key（可选）

        Returns:
            匹配的流程模型列表，不存在返回空列表
        """
        try:
            url = f"{self.base_url}{self.api_path}/list"
            params = {}
            if model_name:
                params["modelName"] = model_name
            if model_key:
                params["modelKey"] = model_key

            response = self._get(url, params=params)

            if response.status_code == 200:
                result = response.json()
                rows = result.get("data") or result.get("rows")
                if rows and len(rows) > 0:
                    logger.info(f"搜索到 {len(rows)} 个流程模型")
                    return list(rows)
            return []

        except requests.exceptions.RequestException as e:
            logger.error(f"搜索流程模型失败（网络错误）：{e}")
            return []
        # Fallback: 捕获 JSON 解析、数据类型等意外错误
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"搜索流程模型失败（未预期）：{e}", exc_info=True)
            return []

    def get_model_by_name(self, model_name: str) -> dict[str, Any] | None:
        """根据流程模型名称获取第一个匹配的流程模型

        Args:
            model_name: 流程模型名称

        Returns:
            流程模型信息，不存在返回 None
        """
        models = self.search_flow_models(model_name=model_name)
        return models[0] if models else None

    def get_model_by_key(self, model_key: str) -> dict[str, Any] | None:
        """根据流程模型key获取流程模型（精确匹配）

        Args:
            model_key: 流程模型key

        Returns:
            流程模型信息，不存在返回 None
        """
        models = self.search_flow_models(model_key=model_key)
        return models[0] if models else None

    def create_model(
        self,
        model_name: str,
        model_key: str,
        bpmn_xml: str,
        category: str,
        description: str = "",
    ) -> dict[str, Any] | None:
        """创建流程模型

        Args:
            model_name: 流程模型名称
            model_key: 流程模型key
            bpmn_xml: BPMN XML 内容
            category: 流程分类编码
            description: 模型描述

        Returns:
            创建成功返回流程模型信息，失败返回 None
        """
        try:
            url = f"{self.base_url}{self.api_path}"

            # 注意：不传递 modelId（后端自动生成）
            payload = {
                "modelName": model_name,
                "modelKey": model_key,
                "bpmnXml": bpmn_xml,
                "category": category,
                "description": description,
            }

            response = self._post(url, json=payload)

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    logger.info(f"流程模型创建成功：{model_name} ({model_key})")
                    return result.get("data") or {
                        "modelName": model_name,
                        "modelKey": model_key,
                    }
                else:
                    logger.warning(f"流程模型创建失败：{result.get('msg')}")
                    return None
            else:
                logger.error(f"流程模型创建请求失败：{response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"创建流程模型异常（网络错误）：{e}")
            return None
        # Fallback: 捕获 JSON 解析、数据类型等意外错误
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"创建流程模型异常（未预期）：{e}", exc_info=True)
            return None

    def update_model(
        self,
        model_id: str,
        model_name: str,
        model_key: str,
        bpmn_xml: str,
        category: str,
        description: str = "",
    ) -> dict[str, Any] | None:
        """更新流程模型

        Args:
            model_id: 流程模型ID
            model_name: 流程模型名称
            model_key: 流程模型key
            bpmn_xml: BPMN XML 内容
            category: 流程分类编码
            description: 模型描述

        Returns:
            更新成功返回流程模型信息，失败返回 None
        """
        try:
            url = f"{self.base_url}{self.api_path}"

            payload = {
                "modelId": model_id,
                "modelName": model_name,
                "modelKey": model_key,
                "bpmnXml": bpmn_xml,
                "category": category,
                "description": description,
            }

            response = self._put(url, json=payload)

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    logger.info(f"流程模型更新成功：{model_name} ({model_key})")
                    return result.get("data") or {
                        "modelName": model_name,
                        "modelKey": model_key,
                    }
                else:
                    logger.warning(f"流程模型更新失败：{result.get('msg')}")
                    return None
            else:
                logger.error(f"流程模型更新请求失败：{response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"更新流程模型异常（网络错误）：{e}")
            return None
        # Fallback: 捕获 JSON 解析、数据类型等意外错误
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"更新流程模型异常（未预期）：{e}", exc_info=True)
            return None
