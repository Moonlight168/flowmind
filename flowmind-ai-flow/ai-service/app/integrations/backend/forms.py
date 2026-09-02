"""
FlowMind 智能流程设计服务 - 表单服务

本模块提供表单相关的业务逻辑，包括表单查询、创建等。
"""

from typing import Any

import requests

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
        try:
            url = f"{self.base_url}{self.api_path}/list"
            params = {}
            if form_name:
                params["formName"] = form_name

            response = self._get(url, params=params)

            if response.status_code == 200:
                result = response.json()
                rows = result.get("data") or result.get("rows")
                if rows and len(rows) > 0:
                    logger.info(f"搜索到 {len(rows)} 个表单")
                    return list(rows)
            return []

        except requests.exceptions.RequestException as e:
            logger.error(f"搜索表单失败（网络错误）：{e}")
            return []
        # Fallback: 捕获 JSON 解析、数据类型等意外错误
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"搜索表单失败（未预期）：{e}", exc_info=True)
            return []

    def get_form_by_name(self, form_name: str) -> dict[str, Any] | None:
        """根据表单名称获取第一个匹配的表单

        Args:
            form_name: 表单名称

        Returns:
            表单信息，不存在返回 None
        """
        forms = self.search_forms(form_name=form_name)
        return forms[0] if forms else None

    def create_form(
        self,
        form_name: str,
        content: str,
        remark: str = "",
    ) -> dict[str, Any] | None:
        """创建表单

        Args:
            form_name: 表单名称
            content: 表单内容（JSON 字符串）
            remark: 备注说明

        Returns:
            创建成功返回表单信息，失败返回 None
        """
        try:
            url = f"{self.base_url}{self.api_path}"

            payload = {
                "formName": form_name,
                "content": content,
                "remark": remark,
            }

            response = self._post(url, json=payload)

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    logger.info(f"表单创建成功：{form_name}")
                    return result.get("data") or {"formName": form_name}
                else:
                    logger.warning(f"表单创建失败：{result.get('msg')}")
                    return None
            else:
                logger.error(f"表单创建请求失败：{response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"创建表单异常（网络错误）：{e}")
            return None
        # Fallback: 捕获 JSON 解析、数据类型等意外错误
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"创建表单异常（未预期）：{e}", exc_info=True)
            return None

    def update_form(
        self,
        form_id: int | str,
        form_name: str,
        content: str,
        remark: str = "",
    ) -> dict[str, Any] | None:
        """更新表单

        Args:
            form_id: 表单ID
            form_name: 表单名称
            content: 表单内容（JSON 字符串）
            remark: 备注说明

        Returns:
            更新成功返回表单信息，失败返回 None
        """
        try:
            url = f"{self.base_url}{self.api_path}"

            payload = {
                "formId": int(form_id),
                "formName": form_name,
                "content": content,
                "remark": remark,
            }

            response = self._put(url, json=payload)

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    logger.info(f"表单更新成功：{form_name}")
                    return result.get("data") or {"formName": form_name}
                else:
                    logger.warning(f"表单更新失败：{result.get('msg')}")
                    return None
            else:
                logger.error(f"表单更新请求失败：{response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"更新表单异常（网络错误）：{e}")
            return None
        # Fallback: 捕获 JSON 解析、数据类型等意外错误
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"更新表单异常（未预期）：{e}", exc_info=True)
            return None
