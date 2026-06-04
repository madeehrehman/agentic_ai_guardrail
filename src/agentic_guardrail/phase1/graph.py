"""Compile the Phase 1 regulatory workflow graph with checkpointer."""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agentic_guardrail.phase1.models import State
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


def build_graph() -> StateGraph:
    builder = StateGraph(State)

    builder.add_node("receive_request", receive_request)
    builder.add_node("plan", plan_kinetic_action)
    builder.add_node("human_gate", human_approval_gate)
    builder.add_node("validate", validate_after_resume)
    builder.add_node("execute", execute_kinetic)
    builder.add_node("reject", reject_action)
    builder.add_node("timeout", timeout_action)
    builder.add_node("fail", fail_run)

    builder.add_edge(START, "receive_request")
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


def compile_graph(*, checkpointer: MemorySaver | None = None):
    cp = checkpointer or MemorySaver()
    return build_graph().compile(checkpointer=cp)
