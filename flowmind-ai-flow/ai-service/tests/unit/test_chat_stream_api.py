"""
FlowMind 智能流程设计服务 - 聊天 SSE API 单元测试
"""

from app.api import chat
from app.domain.dto import ChatRequestDTO
from app.utils.auth import TokenUser


async def test_chat_stream_sends_meta_tokens_and_done(monkeypatch):
    """SSE 接口应先返回会话信息，再透传 token 和完成事件。"""
    monkeypatch.setattr(chat, "generate_trace_id", lambda: "trace-1")
    monkeypatch.setattr(
        chat,
        "stream_chat_workflow",
        lambda **kwargs: iter(
            [
                {"type": "delta", "content": "你"},
                {"type": "done", "response": "你好"},
            ]
        ),
    )

    response = chat.chat_stream(
        ChatRequestDTO(user_input="hello"),
        TokenUser(user_id=1, username="tester", user_key="user-key"),
    )
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk.decode() if isinstance(chunk, bytes) else chunk)
    body = "".join(chunks)

    assert '"type": "meta"' in body
    assert '"thread_id": "user-key"' in body
    assert '"content": "你"' in body
    assert '"response": "你好"' in body
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"


async def test_chat_stream_hides_internal_error_details(monkeypatch):
    """流式异常应返回稳定文案，不得泄露内部连接信息。"""

    def _failed_stream(**kwargs):
        yield from ()
        raise RuntimeError("redis password=secret")

    monkeypatch.setattr(chat, "generate_trace_id", lambda: "trace-1")
    monkeypatch.setattr(chat, "stream_chat_workflow", _failed_stream)
    response = chat.chat_stream(
        ChatRequestDTO(user_input="hello"),
        TokenUser(user_id=1, username="tester", user_key="user-key"),
    )
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk.decode() if isinstance(chunk, bytes) else chunk)
    body = "".join(chunks)

    assert "AI 服务暂时异常，请稍后重试" in body
    assert "password" not in body
    assert "secret" not in body
