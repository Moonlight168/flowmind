"""
FlowMind AI Service - 测试配置

提供共享 fixtures：
- redis_client: 连接测试环境 Redis
- app: FastAPI TestClient
"""

from __future__ import annotations

import os
import uuid
from typing import Generator

import pytest
import redis
from dotenv import load_dotenv
from fastapi.testclient import TestClient

# 加载 .env 文件
_load_dotenv = load_dotenv("/f/MyProjects/flowmind/flowmind-ai-flow/ai-service/.env")

from app.main import app
from app.config.settings import settings


@pytest.fixture(scope="session")
def redis_client() -> redis.Redis:
    """连接 Redis（使用 settings 配置）"""
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
