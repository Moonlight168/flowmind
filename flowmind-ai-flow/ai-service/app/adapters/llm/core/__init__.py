"""
FlowMind 智能流程设计服务 - LLM 核心模块

本模块提供 LLM 客户端核心实现。
"""

from app.adapters.llm.core.llm_client import LLMClient, get_llm_client

__all__ = ["LLMClient", "get_llm_client"]
