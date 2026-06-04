"""Regulatory workflow: Phase 2 input guard → Phase 1 HITL kinetic gate."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agentic_guardrail.checkpointing import get_checkpointer
from agentic_guardrail.phase1.nodes import (
    execute_kinetic,
    fail_run,
    human_approval_gate,
    plan_kinetic_action,
    receive_request,
    reject_action,
    route_after_human,
    timeout_action,
    validate_after_resume,
)
from agentic_guardrail.phase2.node import (
    input_escalation_gate,
    input_guard,
    refuse_input,
    route_after_escalation,
    route_after_input_guard,
)
from agentic_guardrail.workflow.state import WorkflowState


def build_graph() -> StateGraph:
    builder = StateGraph(WorkflowState)

    builder.add_node("input_guard", input_guard)
    builder.add_node("refuse", refuse_input)
    builder.add_node("input_escalation", input_escalation_gate)
    builder.add_node("receive_request", receive_request)
    builder.add_node("plan", plan_kinetic_action)
    builder.add_node("human_gate", human_approval_gate)
    builder.add_node("validate", validate_after_resume)
    builder.add_node("execute", execute_kinetic)
    builder.add_node("reject", reject_action)
    builder.add_node("timeout", timeout_action)
    builder.add_node("fail", fail_run)

    builder.add_edge(START, "input_guard")
    builder.add_conditional_edges(
        "input_guard",
        route_after_input_guard,
        {"refuse": "refuse", "escalate": "input_escalation", "continue": "receive_request"},
    )
    builder.add_edge("refuse", END)
    builder.add_conditional_edges(
        "input_escalation",
        route_after_escalation,
        {"continue": "receive_request", "end": END},
    )

    builder.add_edge("receive_request", "plan")

    def route_after_plan(state: dict) -> str:
        return "human_gate" if state.get("pending_proposal") else "fail"

    builder.add_conditional_edges(
        "plan",
        route_after_plan,
        {"human_gate": "human_gate", "fail": "fail"},
    )
    builder.add_conditional_edges(
        "human_gate",
        route_after_human,
        {
            "validate": "validate",
            "reject": "reject",
            "timeout": "timeout",
            "fail": "fail",
        },
    )

    def after_validate(state: dict) -> str:
        if state.get("status") == "stale_blocked":
            return "end"
        return "execute"

    builder.add_conditional_edges(
        "validate",
        after_validate,
        {"execute": "execute", "end": END},
    )
    builder.add_edge("execute", END)
    builder.add_edge("reject", END)
    builder.add_edge("timeout", END)
    builder.add_edge("fail", END)

    return builder


def compile_graph(
    *,
    checkpointer=None,
    checkpoint_backend: str | None = None,
    db_path=None,
):
    cp = checkpointer or get_checkpointer(backend=checkpoint_backend, db_path=db_path)
    return build_graph().compile(checkpointer=cp)
