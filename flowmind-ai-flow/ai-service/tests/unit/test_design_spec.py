"""
FlowMind 智能流程设计服务 - DESIGN_SPEC 单元测试
"""

from app.agents.design_spec import DESIGN_SPEC


def test_spec_has_three_types():
    assert set(DESIGN_SPEC.keys()) == {"flow_design", "form_design", "category_design"}
    assert all("schema" in s and "tools" in s for s in DESIGN_SPEC.values())


def test_flow_design_four_tools():
    tools = {t.name for t in DESIGN_SPEC["flow_design"]["tools"]}
    assert tools == {
        "search_categories",
        "search_forms",
        "search_roles",
        "search_flow_models",
    }


def test_form_design_only_forms():
    tools = {t.name for t in DESIGN_SPEC["form_design"]["tools"]}
    assert tools == {"search_forms"}


def test_category_design_only_categories():
    tools = {t.name for t in DESIGN_SPEC["category_design"]["tools"]}
    assert tools == {"search_categories"}
