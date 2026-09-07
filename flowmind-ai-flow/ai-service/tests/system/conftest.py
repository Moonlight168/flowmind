"""FlowMind AI Service 系统测试配置。

系统测试保留真实模型和 Redis，仅固定 Java 后端的权威目录数据。
"""

import json
from typing import Any

import pytest
import requests

CATEGORIES = [{"categoryId": 1, "categoryName": "通用流程", "code": "GENERAL"}]
FORMS = [
    {
        "formId": 1,
        "formName": "请假申请表",
        "formKey": "leave_form",
        "content": json.dumps(
            {
                "widgetList": [
                    {"type": "select", "options": {"name": "leaveType"}},
                    {"type": "date", "options": {"name": "startDate"}},
                    {"type": "date", "options": {"name": "endDate"}},
                    {"type": "textarea", "options": {"name": "reason"}},
                ]
            },
            ensure_ascii=False,
        ),
    }
]
ROLES = [{"roleId": 1, "roleName": "部门经理"}]
FLOW_MODELS = [
    {"modelId": 1, "modelName": "通用审批流程", "modelKey": "general_approval"}
]


def _backend_rows(url: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    if url.endswith("/flowable/category/list"):
        rows = CATEGORIES
        if params.get("code"):
            code = str(params["code"]).lower()
            rows = [row for row in rows if row["code"].lower() == code]
        if params.get("categoryName"):
            name = str(params["categoryName"])
            rows = [row for row in rows if name in row["categoryName"]]
        return rows
    if url.endswith("/flowable/form/list"):
        return FORMS
    if url.endswith("/system/role/list"):
        return ROLES
    if url.endswith("/flowable/model/list"):
        return FLOW_MODELS
    raise AssertionError(f"系统测试出现未声明的后端请求: {url}")


def _response(rows: list[dict[str, Any]]) -> requests.Response:
    response = requests.Response()
    response.status_code = 200
    response.encoding = "utf-8"
    response._content = json.dumps(
        {"code": 200, "rows": rows}, ensure_ascii=False
    ).encode()
    return response


@pytest.fixture(autouse=True)
def backend_catalog(monkeypatch: pytest.MonkeyPatch) -> None:
    """固定 Java 后端数据，防止外部目录波动干扰模型链路测试。"""

    def request(method: str, url: str, **kwargs: Any) -> requests.Response:
        del method
        return _response(_backend_rows(url, kwargs.get("params") or {}))

    monkeypatch.setattr(requests, "request", request)
