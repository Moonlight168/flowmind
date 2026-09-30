import pytest
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps import require_auth
from app.config.settings import settings


def _request(headers: dict[str, str]) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/design/flow",
            "headers": [
                (name.lower().encode(), value.encode())
                for name, value in headers.items()
            ],
        }
    )


@pytest.mark.asyncio
async def test_require_auth_trusts_gateway_identity_without_jwt_secret(monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret", "")
    request = _request(
        {"user_id": "42", "username": "%E6%B5%8B%E8%AF%95+%E7%94%A8%E6%88%B7", "user_key": "session-1"}
    )
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="gateway-validated-token"
    )

    user = await require_auth(request, credentials)

    assert user.user_id == 42
    assert user.username == "测试 用户"
    assert user.user_key == "session-1"


@pytest.mark.asyncio
async def test_require_auth_rejects_missing_gateway_identity_without_jwt_secret(
    monkeypatch,
):
    monkeypatch.setattr(settings, "jwt_secret", "")

    with pytest.raises(HTTPException, match="Missing gateway identity headers"):
        await require_auth(_request({}), None)
