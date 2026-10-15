"""Design API conversation namespace tests."""

from app.api.design import SSE_HEADERS, _design_thread_id, _safe_stream_error
from app.core.auth import TokenUser


def _user(user_id: int, user_key: str) -> TokenUser:
    return TokenUser(user_id=user_id, username="test", user_key=user_key)


def test_design_thread_namespace_separates_artifact_mode_and_user():
    base = _design_thread_id("flow_design", _user(1, "key-a"), "design", "artifact-1")
    assert base != _design_thread_id("flow_design", _user(1, "key-a"), "basic", "artifact-1")
    assert base != _design_thread_id("form_design", _user(1, "key-a"), "design", "artifact-1")
    assert base != _design_thread_id("flow_design", _user(2, "key-a"), "design", "artifact-1")


def test_design_thread_namespace_is_stable_across_relogin():
    # 隔离键使用 user_id：同一用户重新登录（user_key 变化）后会话保持连续
    first = _design_thread_id("flow_design", _user(1, "key-old"), "design", "artifact-1")
    second = _design_thread_id("flow_design", _user(1, "key-new"), "design", "artifact-1")
    assert first == second


def test_design_thread_namespace_does_not_expose_raw_business_identifier():
    thread_id = _design_thread_id(
        "flow_design", _user(1, "key-a"), "design", "sensitive-business-key"
    )
    assert "sensitive-business-key" not in thread_id


def test_design_stream_error_is_traceable_without_internal_details():
    event = _safe_stream_error("trace-1")
    assert '"trace_id": "trace-1"' in event
    assert '"status": "error"' in event
    assert "password" not in event


def test_design_sse_disables_proxy_buffering():
    assert SSE_HEADERS == {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    }
