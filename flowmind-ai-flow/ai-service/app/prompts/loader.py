"""
FlowMind 智能流程设计服务 - Markdown 提示词加载器
"""

import re
from functools import cache
from pathlib import Path
from typing import Any

PROMPT_ROOT = Path(__file__).parent
VARIABLE_PATTERN = re.compile(r"(?<!\$)\{([A-Za-z_][A-Za-z0-9_]*)\}")


@cache
def load_prompt(relative_path: str) -> str:
    """读取提示词 Markdown 文档。"""
    return (PROMPT_ROOT / relative_path).read_text(encoding="utf-8").strip()


def render_prompt(relative_path: str, variables: dict[str, Any]) -> str:
    """替换显式变量，保留提示词中的 JSON 与表达式花括号。"""
    content = load_prompt(relative_path)
    return VARIABLE_PATTERN.sub(
        lambda match: str(variables.get(match.group(1), match.group(0))),
        content,
    )
