"""
FlowMind 智能流程设计服务 - Nacos 注册器

本模块使用 Nacos 官方 SDK 实现服务注册，内置自动心跳维持机制。
"""

import os
import socket
import time

import nacos

from app.config.settings import settings
from app.infra.logger import logger


class NacosRegistry:
    """Nacos 服务注册器（基于官方 SDK）

    使用 nacos-sdk-python 实现，特性：
    - 自动心跳维持（SDK 内置，无需手动线程）
    - 自动重试和连接池管理
    - API 兼容性（自动适配 Nacos 服务端版本）
    """

    def __init__(self):
        self.service_name = "flowmind-ai-flow"
        self.group_name = "DEFAULT_GROUP"
        self.cluster_name = "DEFAULT"
        self._client = None
        self._registered = False
        self._register_ip: str | None = None
        self._register_port: int | None = None

    def _init_client(self) -> None:
        """初始化 Nacos 客户端"""
        if self._client is None:
            server_addr = os.getenv(
                "NACOS_SERVER_ADDR",
                settings.nacos.server_addr
            )
            self._client = nacos.NacosClient(server_addr)
            logger.info(f"Nacos 客户端已初始化 - 地址：{server_addr}")

    def register(self) -> bool:
        """注册服务到 Nacos（SDK 自动维持心跳）

        Returns:
            注册是否成功
        """
        try:
            self._init_client()

            # 获取注册 IP 和端口
            ip = os.getenv("NACOS_REGISTER_IP") or self._get_local_ip()
            port = int(os.getenv("NACOS_REGISTER_PORT", 0)) or settings.app.port

            self._register_ip = ip
            self._register_port = port

            # 注册实例（SDK 会自动维持心跳，无需手动线程）
            # add_naming_instance 参数：service_name, ip, port, cluster_name, weight, metadata, enable, healthy, ephemeral, group_name, heartbeat_interval
            self._client.add_naming_instance(
                service_name=self.service_name,
                ip=ip,
                port=port,
                cluster_name=self.cluster_name,
                weight=1.0,
                metadata={},
                enable=True,
                healthy=True,
                ephemeral=True,
                group_name=self.group_name,
                heartbeat_interval=5,  # SDK 自动心跳间隔（秒）
            )

            self._registered = True
            logger.info(
                f"服务注册成功 - 服务名：{self.service_name}, "
                f"IP: {ip}, 端口：{port} (SDK 自动心跳)"
            )
            return True

        except Exception as e:
            logger.error(f"服务注册异常：{e}")
            return False

    def _get_local_ip(self) -> str:
        """获取本地 IP 地址"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def deregister(self) -> bool:
        """从 Nacos 注销服务

        Returns:
            注销是否成功
        """
        if not self._registered or self._client is None:
            logger.debug("服务未注册，跳过注销")
            return True

        try:
            self._client.remove_naming_instance(
                service_name=self.service_name,
                ip=self._register_ip or self._get_local_ip(),
                port=self._register_port or settings.app.port,
                cluster_name=self.cluster_name,
            )

            self._registered = False
            logger.info(f"服务注销成功 - 服务名：{self.service_name}")
            return True

        except Exception as e:
            logger.error(f"服务注销异常：{e}")
            return False


# 全局注册器实例
_registry: NacosRegistry | None = None


def get_registry() -> NacosRegistry:
    """获取全局 Nacos 注册器实例

    Returns:
        Nacos 注册器实例
    """
    global _registry
    if _registry is None:
        _registry = NacosRegistry()
    return _registry


def register_to_nacos(max_retries: int = 5, retry_interval: int = 5) -> bool:
    """注册服务到 Nacos（便捷函数）

    Args:
        max_retries: 最大重试次数
        retry_interval: 重试间隔（秒）

    Returns:
        注册是否成功
    """
    registry = get_registry()

    for attempt in range(1, max_retries + 1):
        success = registry.register()
        if success:
            return True

        if attempt < max_retries:
            logger.warning(
                f"Nacos 注册失败，{retry_interval}秒后重试 "
                f"({attempt}/{max_retries})..."
            )
            time.sleep(retry_interval)

    logger.error(f"Nacos 注册失败，已重试{max_retries}次，服务将无法被发现")
    return False


def deregister_from_nacos() -> bool:
    """从 Nacos 注销服务（便捷函数）

    Returns:
        注销是否成功
    """
    registry = get_registry()
    return registry.deregister()
