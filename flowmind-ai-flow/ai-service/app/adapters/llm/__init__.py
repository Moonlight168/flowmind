"""
FlowMind 智能流程设计服务 - LLM 适配器模块

本模块提供LLM模型调用能力，属于适配器层。

使用方式：
    from app.adapters.llm.core import get_llm_client
"""

# 不在此处导入子模块，避免循环依赖
# llm/__init__ → llm_client → factory → llm/openai_adapter → llm/__init__ (空)
__all__ = ["core"]
