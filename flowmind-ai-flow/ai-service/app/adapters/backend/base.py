"""
FlowMind 智能流程设计服务 - 后端服务基类

本模块提供后端服务的基类封装，统一处理认证令牌和请求头构建。
"""


import requests

from app.config.settings import settings


class BackendService:
    """后端服务基类

    封装通用的后端请求功能：
    - 统一的认证令牌管理
    - 标准化的请求头构建
    - 通用的错误处理

    子类只需关注业务逻辑，无需重复处理认证和请求构建。
    """

    def __init__(self, auth_token: str | None = None):
        """初始化后端服务

        Args:
            auth_token: 用户认证令牌（可选）
        """
        self._auth_token = auth_token

    @property
    def auth_token(self) -> str | None:
        """获取当前认证令牌"""
        return self._auth_token

    @auth_token.setter
    def auth_token(self, value: str | None):
        """设置认证令牌"""
        self._auth_token = value

    @property
    def base_url(self) -> str:
        """获取后端基础 URL"""
        return settings.backend.base_url

    @property
    def timeout(self) -> int:
        """获取请求超时时间"""
        return settings.backend.timeout

    def _get_headers(self, content_type: str = "application/json") -> dict[str, str]:
        """构建请求头

        Args:
            content_type: Content-Type，默认 application/json

        Returns:
            请求头字典
        """
        headers = {"Content-Type": content_type}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        return headers

    def _request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> requests.Response:
        """发送 HTTP 请求

        自动注入请求头，统一处理超时设置。

        Args:
            method: HTTP 方法（GET, POST, PUT, DELETE）
            url: 请求 URL
            **kwargs: 传递给 requests 的其他参数

        Returns:
            HTTP 响应
        """
        # 合并默认 headers
        headers = self._get_headers()
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))

        # 设置默认超时
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout

        return requests.request(method, url, headers=headers, **kwargs)

    def _get(self, url: str, **kwargs) -> requests.Response:
        """发送 GET 请求"""
        return self._request("GET", url, **kwargs)

    def _post(self, url: str, **kwargs) -> requests.Response:
        """发送 POST 请求"""
        return self._request("POST", url, **kwargs)

    def _put(self, url: str, **kwargs) -> requests.Response:
        """发送 PUT 请求"""
        return self._request("PUT", url, **kwargs)

    def _delete(self, url: str, **kwargs) -> requests.Response:
        """发送 DELETE 请求"""
        return self._request("DELETE", url, **kwargs)
