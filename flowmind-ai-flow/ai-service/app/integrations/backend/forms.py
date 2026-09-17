"""
FlowMind 智能流程设计服务 - 表单服务

本模块提供表单查询（设计链只读检索；写操作由前端经网关直接完成）。
"""

from typing import Any

from app.config.settings import settings
from app.infra.logger import logger
from app.integrations.backend.client import BackendClient


class FormClient(BackendClient):
    """表单服务

    继承 BackendClient，自动处理认证令牌。
    """

    @property
    def api_path(self) -> str:
        """获取表单 API 路径"""
        return settings.backend.form_api_path

    def search_forms(self, form_name: str | None = None) -> list[dict[str, Any]]:
        """搜索表单（支持按名称搜索）

        Args:
            form_name: 表单名称（可选）

        Returns:
            匹配的表单列表，不存在返回空列表
        """
        url = f"{self.base_url}{self.api_path}/list"
        params = {"formName": form_name} if form_name else {}
        rows = self._get_list(url, params=params, resource_name="表单")
        logger.info(f"搜索到 {len(rows)} 个表单")
        return rows
