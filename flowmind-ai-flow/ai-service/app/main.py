"""
FlowMind 智能流程设计服务 - 主应用入口

本模块实现 FastAPI 应用入口，提供应用创建、配置和路由注册功能。
"""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, design, health
from app.config.settings import settings
from app.core.exceptions import register_exception_handlers
from app.infra.logger import generate_request_id, logger, set_request_id, setup_logging
from app.infra.nacos import deregister_from_nacos, register_to_nacos
from app.infra.observability import shutdown_observability
from app.llm import initialize_model_runtime

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    runtime = initialize_model_runtime()
    readiness = runtime.describe_readiness()
    if not readiness["structured_fallback_ready"]:
        reasons = ",".join(readiness["not_ready_reasons"])
        logger.error(f"结构化模型降级未就绪: {reasons}")

    # 注册到 Nacos（失败时会抛出异常）
    if not register_to_nacos():
        logger.error("Nacos 注册失败，服务启动中止")
        raise RuntimeError("Nacos 注册失败，请检查 Nacos 服务是否正常运行")

    try:
        yield
    finally:
        # 关闭时释放资源，并确保批量观测数据完整上报
        try:
            deregister_from_nacos()
        finally:
            shutdown_observability()


app = FastAPI(
    title="FlowMind 智能流程设计服务",
    description="基于规则约束和大模型辅助的智能流程设计服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 注册异常处理器
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_context_middleware(request: Request, call_next):
    """HTTP 请求中间件 - 注入日志上下文

    为每个请求生成 request_id 并注入到日志上下文中。
    """
    # 生成请求 ID（优先使用 X-Request-ID 请求头）
    request_id = request.headers.get("X-Request-ID") or generate_request_id()

    # 设置到上下文
    set_request_id(request_id)

    # 处理请求
    response = await call_next(request)

    # 在响应头中返回 request_id
    response.headers["X-Request-ID"] = request_id

    return response


# 路由注册（网关层已通过 StripPrefix 去掉 /flowmind-ai，此处直接注册业务路径）
app.include_router(chat.router, prefix="", tags=["对话"])
app.include_router(design.router, prefix="", tags=["设计"])
app.include_router(health.router, tags=["health"])


@app.get("/")
def root() -> dict:
    return {
        "name": "FlowMind 智能流程设计服务",
        "version": "1.0.0",
        "description": "基于规则约束和大模型辅助的智能流程设计服务",
        "docs": "/docs",
        "api": "/api",
        "status": "running",
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        workers=1 if settings.app.debug else settings.app.workers,
    )
