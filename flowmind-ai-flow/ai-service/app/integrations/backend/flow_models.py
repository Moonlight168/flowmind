"""
FlowMind 智能流程设计服务 - 流程模型服务

本模块提供流程模型查询（设计链只读检索；写操作由前端经网关直接完成）。
"""

from typing import Any

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
        url = f"{self.base_url}{self.api_path}/list"
        params = {}
        if model_name:
            params["modelName"] = model_name
        if model_key:
            params["modelKey"] = model_key
        rows = self._get_list(url, params=params, resource_name="流程模型")
        logger.info(f"搜索到 {len(rows)} 个流程模型")
        return rows
