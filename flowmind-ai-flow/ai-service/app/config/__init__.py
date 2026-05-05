"""
FlowMind 智能流程设计服务 - 配置模块

统一管理所有配置项：
- LLM 任务：Prompt 构建
"""

from app.config.llm_task import (
    TASK_CONFIGS,
    Task,
    TaskConfig,
    get_all_task_configs,
    get_task_config,
)

__all__ = [
    # LLM 任务
    "Task",
    "TaskConfig",
    "TASK_CONFIGS",
    "get_task_config",
    "get_all_task_configs",
]
