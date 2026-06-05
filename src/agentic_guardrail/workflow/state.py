"""Full regulatory workflow state (Phases 1–4)."""

from __future__ import annotations

from typing import Annotated, Any, NotRequired, TypedDict

from agentic_guardrail.phase1.models import merge_audit


class WorkflowState(TypedDict):
    user_id: str
    entity_id: str
    user_request: str
    loop_count: int
    max_loops: int
    status: str
    pending_proposal: dict[str, Any] | None
    human_decision: dict[str, Any] | None
    execution_result: str | None
    audit_log: Annotated[list[dict[str, Any]], merge_audit]
    # Phase 2
    raw_user_request: NotRequired[str]
    input_guard_decision: NotRequired[str]
    input_guard_policy_id: NotRequired[str]
    input_guard_detail: NotRequired[str]
    input_guard_scores: NotRequired[dict[str, Any]]
    pii_token_map: NotRequired[dict[str, str]]
    refusal_message: NotRequired[str | None]
    input_escalation_pending: NotRequired[bool]
    # Phase 3 — RAG + output
    raw_retrieved_chunks: NotRequired[list[dict[str, Any]]]
    retrieved_chunks: NotRequired[list[dict[str, Any]]]
    approved_chunks: NotRequired[list[dict[str, Any]]]
    blocked_chunk_ids: NotRequired[list[str]]
    retrieval_decision: NotRequired[str]
    retrieval_policy_id: NotRequired[str]
    retrieval_detail: NotRequired[str]
    agent_response: NotRequired[str]
    output_guard_decision: NotRequired[str]
    output_guard_policy_id: NotRequired[str]
    output_guard_detail: NotRequired[str]
    final_response: NotRequired[str]
    # Phase 4 — tool-call rails
    kinetic_action_count: NotRequired[int]
    max_kinetic_actions: NotRequired[int]
    tool_budget_spent: NotRequired[int]
    max_tool_budget: NotRequired[int]
    tool_call_fingerprints: NotRequired[list[str]]
    tool_authorization_decision: NotRequired[str]
    tool_authorization_policy_id: NotRequired[str]
    tool_authorization_detail: NotRequired[str]
    tool_result: NotRequired[str]
    post_tool_decision: NotRequired[str]
    post_tool_policy_id: NotRequired[str]
    post_tool_detail: NotRequired[str]
    # Phase 5 — frameworks
    topical_decision: NotRequired[str]
    topical_policy_id: NotRequired[str]
    topical_detail: NotRequired[str]
    output_guard_framework: NotRequired[str]
