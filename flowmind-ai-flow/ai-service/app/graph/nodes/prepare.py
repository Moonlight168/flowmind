"""设计工作流前置处理节点。"""

from app.design.bpmn_parser import enrich_flow_baseline
from app.design.operations import normalize_design_baseline
from app.graph.nodes.base import node_handler
from app.graph.state import AppState

DESIGN_TYPES = {"category_design", "flow_design", "form_design"}
DESIGN_MODES = {"basic", "design"}


@node_handler("prepare")
def prepare_design_node(state: AppState) -> AppState:
    """校验工作流参数并标准化当前设计基线。"""
    design_type = state.get("design_type") or ""
    mode = state.get("mode") or "design"
    if design_type not in DESIGN_TYPES:
        raise ValueError(f"不支持的设计类型: {design_type}")
    if mode not in DESIGN_MODES or (mode == "basic" and design_type != "flow_design"):
        raise ValueError(f"不支持的设计模式: {design_type}/{mode}")

    baseline = state.get("current_form_data") or {}
    if design_type == "flow_design":
        baseline = enrich_flow_baseline(baseline)
    state["current_form_data"] = normalize_design_baseline(design_type, baseline)
    return state
