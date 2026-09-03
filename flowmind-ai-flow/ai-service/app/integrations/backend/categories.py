"""
FlowMind 智能流程设计服务 - 流程分类服务

本模块提供流程分类相关的业务逻辑，包括分类查询、创建等。
"""

from typing import Any

import requests

from app.config.settings import settings
from app.infra.logger import logger
from app.integrations.backend.client import BackendClient


class CategoryClient(BackendClient):
    """流程分类服务

    继承 BackendClient，自动处理认证令牌。
    """

    @property
    def api_path(self) -> str:
        """获取分类 API 路径"""
        return settings.backend.category_api_path

    def check_category_exists(self, category_code: str) -> bool:
        """检查分类是否已存在

        Args:
            category_code: 分类编码

        Returns:
            分类是否已存在
        """
        return bool(self.search_categories(category_code=category_code))

    def search_categories(
        self, category_name: str | None = None, category_code: str | None = None
    ) -> list[dict[str, Any]]:
        """搜索分类（支持按名称或编码搜索）

        Args:
            category_name: 分类名称（可选）
            category_code: 分类编码（可选）

        Returns:
            匹配的分类列表，不存在返回空列表
        """
        url = f"{self.base_url}{self.api_path}/list"
        params = {}
        if category_name:
            params["categoryName"] = category_name
        if category_code:
            params["code"] = category_code
        rows = self._get_list(url, params=params, resource_name="分类")
        logger.info(f"搜索到 {len(rows)} 个分类")
        return rows

    def get_category_by_name(self, category_name: str) -> dict[str, Any] | None:
        """根据分类名称获取第一个匹配的分类（向后兼容）

        Args:
            category_name: 分类名称

        Returns:
            分类信息，不存在返回 None
        """
        categories = self.search_categories(category_name=category_name)
        return categories[0] if categories else None

    def get_category_by_code(self, category_code: str) -> dict[str, Any] | None:
        """根据分类编码获取分类（精确匹配）

        Args:
            category_code: 分类编码

        Returns:
            分类信息，不存在返回 None
        """
        categories = self.search_categories(category_code=category_code)
        return categories[0] if categories else None

    def create_category(
        self,
        category_name: str,
        category_code: str,
        remark: str = "",
    ) -> dict[str, Any] | None:
        """创建流程分类

        Args:
            category_name: 分类名称
            category_code: 分类编码
            remark: 备注说明

        Returns:
            创建成功返回分类信息，失败返回 None
        """
        try:
            url = f"{self.base_url}{self.api_path}"

            payload = {
                "categoryName": category_name,
                "code": category_code,
                "remark": remark,
            }

            response = self._post(url, json=payload)

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    logger.info(f"分类创建成功：{category_name} ({category_code})")
                    return result.get("data") or {
                        "categoryName": category_name,
                        "code": category_code,
                    }
                else:
                    logger.warning(f"分类创建失败：{result.get('msg')}")
                    return None
            else:
                logger.error(f"分类创建请求失败：{response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"创建分类异常（网络错误）：{e}")
            return None
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"创建分类异常（未预期）：{e}", exc_info=True)
            return None

    def update_category(
        self,
        category_id: int | str,
        category_name: str,
        category_code: str,
        remark: str = "",
    ) -> dict[str, Any] | None:
        """更新流程分类

        Args:
            category_id: 分类ID
            category_name: 分类名称
            category_code: 分类编码
            remark: 备注说明

        Returns:
            更新成功返回分类信息，失败返回 None
        """
        try:
            url = f"{self.base_url}{self.api_path}"

            payload = {
                "categoryId": int(category_id),
                "categoryName": category_name,
                "code": category_code,
                "remark": remark,
            }

            response = self._put(url, json=payload)

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    logger.info(f"分类更新成功：{category_name} ({category_code})")
                    return result.get("data") or {
                        "categoryName": category_name,
                        "code": category_code,
                    }
                else:
                    logger.warning(f"分类更新失败：{result.get('msg')}")
                    return None
            else:
                logger.error(f"分类更新请求失败：{response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"更新分类异常（网络错误）：{e}")
            return None
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"更新分类异常（未预期）：{e}", exc_info=True)
            return None

    def ensure_category(
        self,
        category_name: str,
        category_code: str,
        remark: str = "",
    ) -> dict[str, Any]:
        """确保分类存在，不存在则创建

        Args:
            category_name: 分类名称
            category_code: 分类编码
            remark: 备注说明

        Returns:
            分类信息（已存在的或新创建的）
        """
        existing = self.get_category_by_name(category_name)
        if existing:
            logger.info(f"分类已存在：{existing}")
            return existing

        created = self.create_category(category_name, category_code, remark)
        if created:
            return created

        logger.warning(f"分类创建失败，返回传入参数：{category_name}")
        return {
            "categoryName": category_name,
            "code": category_code,
            "remark": remark,
        }
