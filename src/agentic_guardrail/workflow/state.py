"""Full regulatory workflow state (Phase 1 HITL + Phase 2 input guard)."""

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
    # Phase 2 — input guard contract
    raw_user_request: NotRequired[str]
    input_guard_decision: NotRequired[str]
    input_guard_policy_id: NotRequired[str]
    input_guard_detail: NotRequired[str]
    input_guard_scores: NotRequired[dict[str, Any]]
    pii_token_map: NotRequired[dict[str, str]]
    refusal_message: NotRequired[str | None]
    input_escalation_pending: NotRequired[bool]
