"""
FlowMind 智能流程设计服务 - 角色服务

本模块提供角色相关的业务逻辑，包括角色查询。
"""

from typing import Any

from app.config.settings import settings
from app.infra.logger import logger
from app.integrations.backend.client import BackendClient


class RoleClient(BackendClient):
    """角色服务

    继承 BackendClient，自动处理认证令牌。
    """

    @property
    def api_path(self) -> str:
        """获取角色 API 路径"""
        return settings.backend.role_api_path

    def search_roles(self, role_name: str | None = None) -> list[dict[str, Any]]:
        """搜索角色（支持按名称搜索）

        Args:
            role_name: 角色名称（可选）

        Returns:
            匹配的角色列表，不存在返回空列表
        """
        url = f"{self.base_url}{self.api_path}/list"
        params = {"roleName": role_name} if role_name else {}
        rows = self._get_list(url, params=params, resource_name="角色")
        logger.info(f"搜索到 {len(rows)} 个角色")
        return rows
