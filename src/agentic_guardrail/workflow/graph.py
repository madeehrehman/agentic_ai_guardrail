"""Regulatory workflow: Phases 2–5 (input, RAG, tools, frameworks) + Phase 1 HITL."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agentic_guardrail.checkpointing import get_checkpointer
from agentic_guardrail.phase1.nodes import (
    fail_run,
    human_approval_gate,
    plan_kinetic_action,
    receive_request,
    reject_action,
    route_after_human,
    timeout_action,
    validate_after_resume,
)
from agentic_guardrail.phase4.nodes import (
    authorize_tool,
    execute_guarded,
    pre_authorize_proposal,
    route_after_authorize,
    route_after_pre_authorize,
)
from agentic_guardrail.phase2.node import (
    input_escalation_gate,
    input_guard,
    refuse_input,
    route_after_escalation,
    route_after_input_guard,
)
from agentic_guardrail.phase5.nodes import (
    route_after_topical,
    topical_dialog_rail,
)
from agentic_guardrail.phase3.nodes import (
    draft_response,
    is_kinetic_request,
    output_guard,
    retrieve_chunks,
    retrieval_rail,
    retrieval_refusal,
    route_after_retrieval,
)
from agentic_guardrail.workflow.state import WorkflowState


def build_graph() -> StateGraph:
    builder = StateGraph(WorkflowState)

    # Phase 2
    builder.add_node("input_guard", input_guard)
    builder.add_node("refuse_input", refuse_input)
    builder.add_node("input_escalation", input_escalation_gate)

    # Phase 5 — topical dialog rail (NeMo-shaped stub by default)
    builder.add_node("topical_rail", topical_dialog_rail)
    builder.add_node("topical_refuse", retrieval_refusal)

    # Phase 3 — RAG path
    builder.add_node("retrieve", retrieve_chunks)
    builder.add_node("retrieval_rail", retrieval_rail)
    builder.add_node("retrieval_refuse", retrieval_refusal)
    builder.add_node("draft_response", draft_response)
    builder.add_node("output_guard", output_guard)

    # Phase 1 + 4 — kinetic path (HITL + guarded_tool)
    builder.add_node("receive_request", receive_request)
    builder.add_node("plan", plan_kinetic_action)
    builder.add_node("pre_authorize", pre_authorize_proposal)
    builder.add_node("human_gate", human_approval_gate)
    builder.add_node("validate", validate_after_resume)
    builder.add_node("authorize_tool", authorize_tool)
    builder.add_node("execute", execute_guarded)
    builder.add_node("reject", reject_action)
    builder.add_node("timeout", timeout_action)
    builder.add_node("fail", fail_run)

    builder.add_edge(START, "input_guard")
    builder.add_conditional_edges(
        "input_guard",
        route_after_input_guard,
        {"refuse": "refuse_input", "escalate": "input_escalation", "continue": "receive_request"},
    )
    builder.add_edge("refuse_input", END)
    builder.add_conditional_edges(
        "input_escalation",
        route_after_escalation,
        {"continue": "receive_request", "end": END},
    )

    builder.add_edge("receive_request", "topical_rail")
    builder.add_conditional_edges(
        "topical_rail",
        route_after_topical,
        {"refuse": "topical_refuse", "continue": "retrieve"},
    )
    builder.add_edge("topical_refuse", END)

    # All requests: retrieve + retrieval rail (indirect injection door)
    builder.add_edge("retrieve", "retrieval_rail")
    builder.add_conditional_edges(
        "retrieval_rail",
        route_after_retrieval,
        {"refuse": "retrieval_refuse", "kinetic": "plan", "qa": "draft_response"},
    )
    builder.add_edge("retrieval_refuse", END)

    # Q&A path
    builder.add_edge("draft_response", "output_guard")
    builder.add_edge("output_guard", END)

    # Kinetic path — Phase 4 pre-auth before HITL, guarded execution after
    builder.add_edge("plan", "pre_authorize")
    builder.add_conditional_edges(
        "pre_authorize",
        route_after_pre_authorize,
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
        return "authorize"

    builder.add_conditional_edges(
        "validate",
        after_validate,
        {"authorize": "authorize_tool", "end": END},
    )
    builder.add_conditional_edges(
        "authorize_tool",
        route_after_authorize,
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
