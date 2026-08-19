"""
FlowMind 智能流程设计服务 - DESIGN_SPEC + 预取摘要单元测试
"""

from app.agents.design_spec import DESIGN_SPEC, prefetch_summaries


def test_spec_has_three_types():
    assert set(DESIGN_SPEC.keys()) == {"flow_design", "form_design", "category_design"}
    assert all("schema" in s and "prefetch" in s and "baseline" in s for s in DESIGN_SPEC.values())


def test_flow_prefetch_four_categories(monkeypatch):
    import app.agents.design_spec as ds

    class _Cat:
        def search_categories(self):
            return [{"categoryId": 1, "categoryName": "请假", "code": "leave"}]

    class _Form:
        def search_forms(self, name=None):
            return [{"formId": 1, "formName": "请假单", "formKey": "form1"}]

    class _Role:
        def search_roles(self):
            return [{"roleId": 1, "roleName": "经理"}]

    class _Flow:
        def search_flow_models(self):
            return [{"modelId": 1, "modelName": "请假流程", "modelKey": "leave_flow"}]

    monkeypatch.setattr(ds, "CategoryService", lambda **kw: _Cat())
    monkeypatch.setattr(ds, "FormService", lambda **kw: _Form())
    monkeypatch.setattr(ds, "RoleService", lambda **kw: _Role())
    monkeypatch.setattr(ds, "FlowService", lambda **kw: _Flow())

    data = prefetch_summaries("flow_design")
    assert set(data.keys()) == {"categories", "forms", "roles", "models"}
    assert data["categories"][0]["code"] == "leave"
    assert data["roles"][0]["key"] == "ROLE1"


def test_form_prefetch_only_forms(monkeypatch):
    import app.agents.design_spec as ds

    class _Form:
        def search_forms(self, name=None):
            return []

    monkeypatch.setattr(ds, "FormService", lambda **kw: _Form())
    data = prefetch_summaries("form_design")
    assert set(data.keys()) == {"forms"}


def test_category_prefetch_only_categories(monkeypatch):
    import app.agents.design_spec as ds

    class _Cat:
        def search_categories(self):
            return []

    monkeypatch.setattr(ds, "CategoryService", lambda **kw: _Cat())
    data = prefetch_summaries("category_design")
    assert set(data.keys()) == {"categories"}
    assert data["categories"] == []
