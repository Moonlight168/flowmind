"""
FlowMind 智能流程设计服务 - 角色服务

本模块提供角色相关的业务逻辑，包括角色查询。
"""

from typing import Any

import requests

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
        try:
            url = f"{self.base_url}{self.api_path}/list"
            params = {}
            if role_name:
                params["roleName"] = role_name

            response = self._get(url, params=params)

            if response.status_code == 200:
                result = response.json()
                rows = result.get("rows") or result.get("data")
                if rows and len(rows) > 0:
                    logger.info(f"搜索到 {len(rows)} 个角色")
                    return list(rows)
            return []

        except requests.exceptions.RequestException as e:
            logger.error(f"搜索角色失败（网络错误）：{e}")
            return []
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"搜索角色失败（未预期）：{e}", exc_info=True)
            return []
