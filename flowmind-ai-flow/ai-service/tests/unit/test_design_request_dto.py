"""
FlowMind 智能流程设计服务 - 设计请求 DTO 测试

回归：后端业务 id 是 Long，JSON 里是数字。调用方把它直接赋给 thread_id 时，
Pydantic 的 str 字段会判 422（Input should be a valid string），前端又只能显示
状态码，排查成本很高。thread_id 统一在这里转成字符串。
"""

import pytest
from pydantic import ValidationError

from app.domain.dto.design_request import DesignRequestDTO, RollbackRequestDTO


def test_thread_id_accepts_numeric_id_from_backend() -> None:
    dto = DesignRequestDTO(user_input="加个字段", thread_id=1)

    assert dto.thread_id == "1"


def test_thread_id_keeps_string_untouched() -> None:
    dto = DesignRequestDTO(user_input="加个字段", thread_id="leave_form")

    assert dto.thread_id == "leave_form"


def test_thread_id_may_be_omitted() -> None:
    assert DesignRequestDTO(user_input="加个字段").thread_id is None


def test_rollback_dto_accepts_numeric_thread_id() -> None:
    assert RollbackRequestDTO(message_count=3, thread_id=1).thread_id == "1"


def test_conversion_does_not_bypass_max_length() -> None:
    with pytest.raises(ValidationError):
        DesignRequestDTO(user_input="加个字段", thread_id="x" * 101)
