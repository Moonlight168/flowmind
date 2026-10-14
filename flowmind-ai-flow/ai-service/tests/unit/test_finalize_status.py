"""Public AI design response status and safe-fallback tests."""

from app.graph.nodes.finalize import finalize_node


def test_validation_failure_never_returns_a_draft():
    state = {
        "design_type": "flow_design",
        "intent": "error",
        "design_output": {
            "nodes": [{"id": "unsafe", "type": "USER_TASK", "name": "草稿"}],
            "review": {"passed": False, "errors": ["缺少开始节点"]},
            "operation_count": 1,
        },
    }
    result = finalize_node(state)["design_output"]
    assert result["status"] == "error"
    assert result["form_data"] is None
    assert result["validation"]["errors"] == ["缺少开始节点"]


def test_clarification_uses_needs_input_status():
    state = {
        "design_type": "form_design",
        "intent": "clarification",
        "design_output": {"message": "请选择表单"},
    }
    result = finalize_node(state)["design_output"]
    assert result["status"] == "needs_input"
    assert result["form_data"] is None


def test_ready_response_exposes_operations_and_validation(monkeypatch):
    monkeypatch.setattr(
        "app.graph.nodes.finalize.generate_bpmn_xml",
        lambda structure, category, process_key="": "<xml/>",
    )
    state = {
        "design_type": "flow_design",
        "mode": "design",
        "intent": "success",
        "current_form_data": {"modelName": "请假"},
        "design_output": {
            "nodes": [
                {"id": "start", "type": "START_EVENT", "name": "开始", "form_key": "1"}
            ],
            "edges": [],
            "operations": [{"op": "replace_graph", "nodes": [], "edges": []}],
            "operation_count": 1,
            "review": {"passed": True, "errors": []},
        },
    }
    result = finalize_node(state)["design_output"]
    assert result["status"] == "ready"
    assert result["operation_count"] == 1
    assert result["operations"][0]["op"] == "replace_graph"


def test_success_message_omits_name_when_blank():
    """form_name 为空串时不能渲染出空书名号，也不该编造名字。"""
    state = {
        "design_type": "form_design",
        "intent": "success",
        "design_output": {
            "widgetList": [{"type": "input"}],
            "form_name": "",
            "operations": [{"op": "add_widget", "widget": {"options": {"label": "申请人"}}}],
            "operation_count": 1,
            "review": {"passed": True, "errors": []},
        },
    }

    message = finalize_node(state)["design_output"]["message"]

    assert message == "表单：新增 1 个字段"
    assert "「」" not in message


def test_success_message_uses_generated_name_and_summarises_changes():
    state = {
        "design_type": "form_design",
        "intent": "success",
        "design_output": {
            "widgetList": [{"type": "input"}],
            "form_name": "请假申请单",
            "operations": [{"op": "add_widget", "widget": {"options": {"label": "申请人"}}}],
            "operation_count": 1,
            "review": {"passed": True, "errors": []},
        },
    }

    result = finalize_node(state)["design_output"]

    assert result["message"] == "表单「请假申请单」：新增 1 个字段"
    assert result["change_details"] == [
        {"action": "add", "label": "新增 1 个字段", "detail": "申请人"}
    ]


def test_category_keeps_the_plain_preview_message():
    """分类只改几个文本字段，沿用原有文案，不生成变更明细。"""
    state = {
        "design_type": "category_design",
        "intent": "success",
        "design_output": {
            "category_name": "人事管理",
            "operations": [{"op": "update_category", "changes": {"category_name": "人事管理"}}],
            "operation_count": 1,
            "review": {"passed": True, "errors": []},
        },
    }

    result = finalize_node(state)["design_output"]

    assert result["message"] == "已生成分类【人事管理】的变更预览"
    assert "change_details" not in result


def test_flow_basic_keeps_the_plain_preview_message():
    state = {
        "design_type": "flow_design",
        "mode": "basic",
        "intent": "success",
        "design_output": {
            "flow_name": "请假审批",
            "operations": [
                {"op": "update_flow_metadata", "changes": {"flow_name": "请假审批"}}
            ],
            "operation_count": 1,
            "review": {"passed": True, "errors": []},
        },
    }

    result = finalize_node(state)["design_output"]

    assert result["message"] == "已生成流程变更预览"
    assert "change_details" not in result


def test_category_design_does_not_report_pending_category():
    """分类窗口的 category_name 是被设计的实体本身，不是依赖实体。

    照搬成 pending_entities 会让预览在任何一次分类编辑（含更新）上都显示
    「将创建流程分类」，前端还会在「应用变更」时抢先建库，用户再保存就重复创建。
    """
    state = {
        "design_type": "category_design",
        "mode": "design",
        "intent": "success",
        "design_output": {
            "category_name": "请假审批",
            "code": "leave_approval",
            "operations": [{"op": "update_category", "changes": {"remark": "员工请假"}}],
            "operation_count": 1,
            "review": {"passed": True, "errors": []},
        },
    }
    result = finalize_node(state)["design_output"]

    assert result["status"] == "ready"
    assert "pending_entities" not in result


def test_flow_design_still_reports_pending_category():
    state = {
        "design_type": "flow_design",
        "mode": "basic",
        "intent": "success",
        "design_output": {
            "flow_name": "请假审批",
            "code": "leave_approval",
            "category_name": "请假审批",
            "operations": [{"op": "update_flow_metadata", "changes": {"code": "leave_approval"}}],
            "operation_count": 1,
            "review": {"passed": True, "errors": []},
        },
    }
    result = finalize_node(state)["design_output"]

    assert result["pending_entities"] == {"category_name": "请假审批"}


def test_flow_design_exposes_complete_form_drafts_for_apply_confirmation():
    draft = {
        "form_name": "主管审批表",
        "node_ids": ["manager"],
        "widgetList": [
            {
                "type": "textarea",
                "formItemFlag": True,
                "options": {"name": "opinion", "label": "审批意见", "required": True},
            }
        ],
        "formConfig": {},
    }
    state = {
        "design_type": "flow_design",
        "mode": "design",
        "intent": "success",
        "design_output": {
            "nodes": [{"id": "manager", "type": "USER_TASK", "name": "主管审批"}],
            "edges": [],
            "new_forms": [draft],
            "operations": [
                {"op": "update_node", "node_id": "manager", "changes": {}}
            ],
            "operation_count": 1,
            "review": {"passed": True, "errors": []},
        },
    }

    result = finalize_node(state)["design_output"]

    assert result["pending_entities"]["forms"] == [draft]


def test_flow_preview_includes_pending_form_binding_in_target_node_diff():
    """表单尚未创建真实 key 时，节点明细仍要显示待应用的表单绑定。"""
    draft = {
        "form_name": "请假审批意见表",
        "node_ids": ["manager"],
        "widgetList": [
            {
                "type": "textarea",
                "formItemFlag": True,
                "options": {"name": "opinion", "label": "审批意见", "required": True},
            }
        ],
        "formConfig": {},
    }
    state = {
        "design_type": "flow_design",
        "mode": "design",
        "intent": "success",
        "current_form_data": {
            "modelName": "员工请假审批流程",
            "nodes": [
                {"id": "manager", "type": "USER_TASK", "name": "直属主管审批"},
                {"id": "director", "type": "USER_TASK", "name": "部门负责人审批"},
            ],
            "edges": [],
        },
        "design_output": {
            "nodes": [
                {"id": "manager", "type": "USER_TASK", "name": "直属主管审批"},
                {"id": "director", "type": "USER_TASK", "name": "部门负责人审批"},
            ],
            "edges": [],
            "new_forms": [draft],
            "operations": [
                {"op": "update_node", "node_id": "manager", "changes": {}}
            ],
            "operation_count": 1,
            "review": {"passed": True, "errors": []},
        },
    }

    result = finalize_node(state)["design_output"]

    assert result["message"] == "流程「员工请假审批流程」：修改 1 个节点"
    assert result["change_details"] == [
        {
            "action": "update",
            "label": "修改 1 个节点",
            "detail": "直属主管审批 · 表单 未绑定 → 请假审批意见表",
        }
    ]
    assert result["operations"] == [
        {"op": "update_node", "node_id": "manager", "changes": {}}
    ]
