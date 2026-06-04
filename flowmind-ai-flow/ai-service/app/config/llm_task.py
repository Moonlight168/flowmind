"""
FlowMind 智能流程设计服务 - LLM 任务配置
"""

from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    """角色类型"""

    FLOW_DESIGNER = "FLOW_DESIGNER"
    FORM_DESIGNER = "FORM_DESIGNER"
    CATEGORY_DESIGNER = "CATEGORY_DESIGNER"


TASK_MODULE_FLOW_DESIGN = "app.prompts.tasks.flow_model_design"
TASK_MODULE_FORM_GENERATION = "app.prompts.tasks.form_design"
TASK_MODULE_CATEGORY_CLASSIFY = "app.prompts.tasks.category_design"


@dataclass(frozen=True)
class TaskConfig:
    module: str
    schema: str | None
    role: "Role"
    description: str = ""


class Task(StrEnum):
    FLOW_DESIGN_BASIC = "flow_design_basic"
    FLOW_DESIGN = "flow_design"
    FORM_DESIGN = "form_design"
    CATEGORY_DESIGN = "category_design"


TASK_CONFIGS: dict[Task, TaskConfig] = {
    Task.FLOW_DESIGN_BASIC: TaskConfig(
        module="app.prompts.tasks.flow_model_basic",
        schema="flow_design_basic",
        role=Role.FLOW_DESIGNER,
        description="流程模型基本信息设计",
    ),
    Task.FLOW_DESIGN: TaskConfig(
        module=TASK_MODULE_FLOW_DESIGN,
        schema="flow_design_nodes",
        role=Role.FLOW_DESIGNER,
        description="使用bpmnio.js生成流程模型设计",
    ),
    Task.FORM_DESIGN: TaskConfig(
        module=TASK_MODULE_FORM_GENERATION,
        schema="form_design",
        role=Role.FORM_DESIGNER,
        description="使用vform3生成流程表单设计",
    ),
    Task.CATEGORY_DESIGN: TaskConfig(
        module=TASK_MODULE_CATEGORY_CLASSIFY,
        schema="category_design",
        role=Role.CATEGORY_DESIGNER,
        description="进行流程分类设计",
    ),
}


def get_task_config(task: Task) -> TaskConfig | None:
    return TASK_CONFIGS.get(task)


def get_all_task_configs() -> dict[Task, TaskConfig]:
    return TASK_CONFIGS.copy()
