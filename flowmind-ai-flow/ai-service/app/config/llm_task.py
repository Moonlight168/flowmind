"""
FlowMind 智能流程设计服务 - LLM 任务配置

按任务枚举登记提示词与角色；结构化输出 schema 由 design/spec.py 与
domain/design_models.py 统一管理，不在此处重复。
"""

from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    """角色类型"""

    FLOW_DESIGNER = "FLOW_DESIGNER"
    FORM_DESIGNER = "FORM_DESIGNER"
    CATEGORY_DESIGNER = "CATEGORY_DESIGNER"


@dataclass(frozen=True)
class TaskConfig:
    prompt: str
    role: "Role"


class Task(StrEnum):
    FLOW_DESIGN_BASIC = "flow_design_basic"
    FLOW_DESIGN = "flow_design"
    FORM_DESIGN = "form_design"
    CATEGORY_DESIGN = "category_design"


TASK_CONFIGS: dict[Task, TaskConfig] = {
    Task.FLOW_DESIGN_BASIC: TaskConfig(
        prompt="tasks/flow_model_basic.md",
        role=Role.FLOW_DESIGNER,
    ),
    Task.FLOW_DESIGN: TaskConfig(
        prompt="tasks/flow_model_design.md",
        role=Role.FLOW_DESIGNER,
    ),
    Task.FORM_DESIGN: TaskConfig(
        prompt="tasks/form_design.md",
        role=Role.FORM_DESIGNER,
    ),
    Task.CATEGORY_DESIGN: TaskConfig(
        prompt="tasks/category_design.md",
        role=Role.CATEGORY_DESIGNER,
    ),
}


def get_task_config(task: Task) -> TaskConfig | None:
    return TASK_CONFIGS.get(task)


def get_all_task_configs() -> dict[Task, TaskConfig]:
    return TASK_CONFIGS.copy()
