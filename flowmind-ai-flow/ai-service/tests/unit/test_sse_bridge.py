"""SSE 同步生成器桥接测试。"""

import asyncio
from threading import Event

import pytest

from app.api._sse import to_async_stream
from app.core.auth_context import get_auth_token, set_auth_token


@pytest.mark.asyncio
async def test_stream_worker_inherits_request_context() -> None:
    set_auth_token("expected-token")

    def source():
        yield get_auth_token()

    stream = to_async_stream(source())
    try:
        assert await anext(stream) == "expected-token"
    finally:
        await stream.aclose()
        set_auth_token(None)


@pytest.mark.asyncio
async def test_closing_stream_stops_and_closes_source() -> None:
    source_closed = Event()

    def source():
        try:
            while True:
                yield "chunk"
        finally:
            source_closed.set()

    stream = to_async_stream(source(), maxsize=1)
    assert await anext(stream) == "chunk"
    await stream.aclose()

    assert await asyncio.to_thread(source_closed.wait, 2)


@pytest.mark.asyncio
async def test_source_close_error_is_forwarded_without_hanging() -> None:
    class Source:
        def __init__(self) -> None:
            self.sent = False

        def __iter__(self):
            return self

        def __next__(self):
            if self.sent:
                raise StopIteration
            self.sent = True
            return "chunk"

        def close(self) -> None:
            raise ValueError("close failed")

    stream = to_async_stream(Source())
    assert await anext(stream) == "chunk"
    with pytest.raises(ValueError, match="close failed"):
        await anext(stream)
