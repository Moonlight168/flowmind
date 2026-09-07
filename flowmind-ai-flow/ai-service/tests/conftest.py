"""
FlowMind AI Service - 测试配置

提供共享 fixtures：
- redis_client: 连接测试环境 Redis
- app: FastAPI TestClient
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import jwt
import pytest
import redis
from dotenv import load_dotenv
from fastapi.testclient import TestClient

# 加载 .env 文件（ai-service 根目录，须在导入 app 前完成）
_env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_env_path)

# 系统/集成测试固定使用独立 Redis DB，避免误清理本地开发数据。
os.environ["REDIS_DB"] = os.getenv("TEST_REDIS_DB", "15")
os.environ["JWT_SECRET"] = "flowmind-system-test-only-" + ("x" * 48)


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


@pytest.fixture(scope="session")
def auth_headers() -> dict[str, str]:
    """生成仅供本地接口测试使用的有效 JWT。"""
    from app.config.settings import settings

    token = jwt.encode(
        {"user_id": 1, "username": "system-test", "user_key": "system-test"},
        settings.jwt_secret,
        algorithm="HS512",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def thread_id() -> str:
    """生成独立 thread_id"""
    return f"test_{uuid.uuid4().hex[:16]}"


@pytest.fixture
def clean_redis(redis_client: redis.Redis, thread_id: str) -> redis.Redis:
    """仅清理本用例新建的 Redis 数据，不触碰同库既有键。"""
    del thread_id
    keys_before = set(redis_client.scan_iter())
    threads_key = b"chat:threads"
    threads_before = redis_client.smembers(threads_key)
    yield redis_client
    new_keys = set(redis_client.scan_iter()) - keys_before
    if new_keys:
        redis_client.delete(*new_keys)
    new_threads = redis_client.smembers(threads_key) - threads_before
    if new_threads:
        redis_client.srem(threads_key, *new_threads)
