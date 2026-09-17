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
        """搜索角色（全量获取后按名称过滤）

        使用 /optionselect 而非 /list：
        - /list 需要 system:role:list 权限，非管理员用户会 403 并中断设计链；
        - /list 是分页接口（默认 10 条），角色较多时会被截断误判"角色不存在"。
        optionselect 登录即可用且返回全量，字段与校验器（roleId）兼容。
        """
        url = f"{self.base_url}{self.api_path}/optionselect"
        rows = self._get_list(url, params={}, resource_name="角色")
        if role_name:
            rows = [
                row
                for row in rows
                if role_name in str(row.get("roleName") or row.get("role_name") or "")
            ]
        logger.info(f"搜索到 {len(rows)} 个角色")
        return rows
