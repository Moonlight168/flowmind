"""Backend lookup failures must not be confused with valid empty results."""

from types import SimpleNamespace

import pytest
import requests

from app.integrations.backend.client import BackendClient, BackendLookupError


def test_backend_list_allows_explicit_empty_result(monkeypatch):
    client = BackendClient()
    response = SimpleNamespace(status_code=200, json=lambda: {"code": 200, "rows": []})
    monkeypatch.setattr(client, "_get", lambda *args, **kwargs: response)
    assert (
        client._get_list("http://backend/list", params={}, resource_name="表单") == []
    )


def test_backend_list_raises_when_dependency_is_unavailable(monkeypatch):
    client = BackendClient()

    def fail(*args, **kwargs):
        raise requests.ConnectTimeout("secret backend detail")

    monkeypatch.setattr(client, "_get", fail)
    with pytest.raises(BackendLookupError, match="表单查询网络不可用"):
        client._get_list("http://backend/list", params={}, resource_name="表单")


def test_backend_list_raises_on_business_error(monkeypatch):
    client = BackendClient()
    response = SimpleNamespace(
        status_code=200, json=lambda: {"code": 500, "msg": "fail"}
    )
    monkeypatch.setattr(client, "_get", lambda *args, **kwargs: response)
    with pytest.raises(BackendLookupError, match="表单查询返回业务错误"):
        client._get_list("http://backend/list", params={}, resource_name="表单")
