"""
FlowMind 智能流程设计服务 - AI 生产链路集成测试

覆盖从 invoke_design_workflow 入口到最终 design_output 的完整链路：
design（压缩 + LLM）→ review（校验 + 死循环检测）→ format（组装）

mock 点：
- run_react_agent：LLM 输出（可控，避免真实 API 调用）
- checkpointer / redis lock：用 MemorySaver + fake redis（无外部依赖）
- 后端 HTTP service：返回空列表（校验器降级为不查存在性/唯一性）
"""

import importlib

import pytest
from langgraph.checkpoint.memory import MemorySaver

# 用 importlib 获取真实模块（避免模块名与变量名冲突导致拿到编译图对象）
react_agent_node = importlib.import_module("app.graph.nodes.react_agent_node")
review_node = importlib.import_module("app.graph.nodes.review_node")
dw = importlib.import_module("app.graph.workflows.design_workflow")

invoke_design_workflow = dw.invoke_design_workflow


class _FakeRedis:
    """替代 redis lock 的假客户端"""

    def set(self, *args, **kwargs):
        return True

    def delete(self, *args, **kwargs):
        return True


class _FakeBackendService:
    """替代后端 HTTP service，返回空列表（校验器降级）"""

    def __init__(self, auth_token=None):
        pass

    def search_forms(self, *args, **kwargs):
        return []

    def search_categories(self, *args, **kwargs):
        return []

    def search_flow_models(self, *args, **kwargs):
        return []


@pytest.fixture
def chain(monkeypatch):
    """准备完整链路：MemorySaver checkpoint + fake redis lock + 空后端"""
    mem = MemorySaver()
    mem.thread_exists = lambda thread_id: False  # 首次调用
    monkeypatch.setattr(dw, "checkpointer", mem)
    monkeypatch.setattr(dw, "design_workflow", dw.create_design_workflow())
    monkeypatch.setattr(dw, "_get_redis_client", lambda: _FakeRedis())
    monkeypatch.setattr(review_node, "FormService", _FakeBackendService)
    monkeypatch.setattr(review_node, "CategoryService", _FakeBackendService)
    monkeypatch.setattr(review_node, "FlowService", _FakeBackendService)
    return dw


def _mock_llm(monkeypatch, results):
    """mock run_react_agent：按调用顺序弹出结果"""
    queue = list(results)

    def _run(**kwargs):
        if not queue:
            return {"intent": "clarification", "message": "无更多 mock 结果"}
        return queue.pop(0)

    monkeypatch.setattr(react_agent_node, "run_react_agent", _run)


_FLOW_RESULT = {
    "nodes": [
        {"id": "startEvent", "name": "开始", "type": "START_EVENT", "form_key": "form1"},
        {"id": "node_approve", "name": "部门经理审批", "type": "USER_TASK", "candidate_groups": ["ROLE1"], "text": "部门经理"},
        {"id": "endEvent", "name": "结束", "type": "END_EVENT"},
    ],
    "edges": [
        {"source": "start", "target": "node_approve"},
        {"source": "node_approve", "target": "end"},
    ],
}


def test_flow_design_full_chain(chain, monkeypatch):
    """flow_design 完整链路：design → review → format → 含 bpmn_xml"""
    _mock_llm(monkeypatch, [_FLOW_RESULT])
    result = invoke_design_workflow(
        "flow_design",
        "设计一个请假审批流程",
        thread_id="test-flow-1",
        current_form_data={"modelName": "请假审批", "code": "leave"},
        mode="design",
    )
    assert result["intent"] == "success"
    form_data = result["form_data"]
    assert form_data["bpmn_xml"], "应生成 BPMN XML"
    assert len(form_data["nodes"]) == 3
    assert form_data["modelName"] == "请假审批"  # 前端基本信息保留
    assert "bpmn2:process" in form_data["bpmn_xml"]
    # DI 图不应残留重映射前的 startEvent/endEvent shape
    assert 'bpmnElement="startEvent"' not in form_data["bpmn_xml"]
    assert 'bpmnElement="endEvent"' not in form_data["bpmn_xml"]


def test_flow_design_basic(chain, monkeypatch):
    """flow_design basic 模式：只生成基本信息，不生成 BPMN"""
    _mock_llm(monkeypatch, [{"flow_name": "报销审批", "code": "expense", "description": "报销流程"}])
    result = invoke_design_workflow(
        "flow_design",
        "设计报销流程基本信息",
        thread_id="test-flow-basic-1",
        current_form_data={},
        mode="basic",
    )
    assert result["intent"] == "success"
    assert "bpmn_xml" not in result["form_data"] or not result["form_data"].get("bpmn_xml")


def test_form_design_full_chain(chain, monkeypatch):
    """form_design 完整链路：design → review → format（transform_to_vform3）"""
    form_result = {
        "form_name": "请假申请单",
        "widgetList": [
            {"type": "input", "formItemFlag": True, "options": {"name": "reason", "label": "请假事由"}},
            {"type": "date", "formItemFlag": True, "options": {"name": "start_date", "label": "开始日期"}},
        ],
        "formConfig": {"modelName": "leaveForm", "labelWidth": 100},
    }
    _mock_llm(monkeypatch, [form_result])
    result = invoke_design_workflow(
        "form_design",
        "设计请假表单",
        thread_id="test-form-1",
        current_form_data={},
        mode="design",
    )
    assert result["intent"] == "success"
    form_data = result["form_data"]
    assert form_data["form_name"] == "请假申请单"
    assert len(form_data["widgetList"]) == 2
    # transform_to_vform3 补全了完整 options（如 columnWidth）
    assert all("options" in w for w in form_data["widgetList"])


def test_category_design_full_chain(chain, monkeypatch):
    """category_design 完整链路：design → review → format"""
    _mock_llm(monkeypatch, [{"category_name": "请假审批", "code": "leave_approval", "remark": "请假类流程"}])
    result = invoke_design_workflow(
        "category_design",
        "创建请假审批分类",
        thread_id="test-cat-1",
        current_form_data={},
        mode="design",
    )
    assert result["intent"] == "success"
    assert result["form_data"]["category_name"] == "请假审批"
    assert result["form_data"]["code"] == "leave_approval"


def test_review_rejects_invalid_then_retry(chain, monkeypatch):
    """非法输出（START_EVENT 缺 form_key）→ review 失败 → 重跑 design → 通过"""
    invalid = {
        "nodes": [
            {"id": "startEvent", "name": "开始", "type": "START_EVENT"},  # 缺 form_key
            {"id": "endEvent", "name": "结束", "type": "END_EVENT"},
        ],
        "edges": [{"source": "start", "target": "end"}],
    }
    _mock_llm(monkeypatch, [invalid, _FLOW_RESULT])
    result = invoke_design_workflow(
        "flow_design",
        "设计请假审批流程",
        thread_id="test-retry-1",
        current_form_data={"modelName": "请假审批", "code": "leave"},
        mode="design",
    )
    # 第一次非法被 review 拦截，重试后通过
    assert result["intent"] == "success"
    assert result["form_data"]["bpmn_xml"]


def test_review_dead_loop(chain, monkeypatch):
    """连续相同错误 → 死循环检测 → 返回半成品草稿（友好降级，不再冷冰冰 error）"""
    invalid = {
        "nodes": [
            {"id": "startEvent", "name": "开始", "type": "START_EVENT"},  # 缺 form_key
            {"id": "endEvent", "name": "结束", "type": "END_EVENT"},
        ],
        "edges": [{"source": "start", "target": "end"}],
    }
    # 始终返回相同非法结果，触发死循环检测
    _mock_llm(monkeypatch, [invalid, invalid, invalid, invalid])
    result = invoke_design_workflow(
        "flow_design",
        "设计请假审批流程",
        thread_id="test-loop-1",
        current_form_data={"modelName": "请假审批", "code": "leave"},
        mode="design",
    )
    # 死循环检测触发，返回半成品草稿供手动调整
    assert result["partial"] is True
    assert result["form_data"] is not None
    assert result["form_data"]["bpmn_xml"] == ""
