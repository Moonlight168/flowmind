"""
FlowMind AI Service - 测试配置

提供共享 fixtures：
- redis_client: 连接测试环境 Redis
- app: FastAPI TestClient
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import redis
from dotenv import load_dotenv
from fastapi.testclient import TestClient

# 加载 .env 文件（ai-service 根目录，须在导入 app 前完成）
_env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_env_path)


@pytest.fixture(scope="session")
def redis_client() -> redis.Redis:
    """连接 Redis（使用 settings 配置）"""
    from app.config.settings import settings

    client = redis.Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        password=settings.redis.password or None,
        decode_responses=False,
    )
    yield client
    client.close()


@pytest.fixture(scope="session")
def client() -> TestClient:
    """FastAPI TestClient"""
    from app.main import app

    return TestClient(app)


@pytest.fixture
def thread_id() -> str:
    """生成独立 thread_id"""
    return f"test_{uuid.uuid4().hex[:16]}"


@pytest.fixture
def clean_redis(redis_client: redis.Redis, thread_id: str) -> redis.Redis:
    """每个测试前后清空 Redis 测试数据"""
    redis_client.flushdb()
    yield redis_client
    redis_client.flushdb()
