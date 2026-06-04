"""LangGraph nodes for Phase 2 input guard — drop-in reusable."""

from __future__ import annotations

from typing import Any

from langgraph.types import interrupt

from agentic_guardrail.phase1.models import AuditEvent, RunStatus
from agentic_guardrail.phase2.guard import score_user_input
from agentic_guardrail.phase2.models import GuardDecision


def _audit(policy_id: str, decision: str, detail: str) -> dict[str, Any]:
    return {
        "audit_log": [
            AuditEvent(policy_id=policy_id, decision=decision, detail=detail).model_dump(
                mode="json"
            )
        ]
    }


def input_guard(state: dict[str, Any]) -> dict[str, Any]:
    """
    Score user_request; write decision contract to state.

    Downstream nodes must use `user_request` (rewritten when decision=rewrite).
    Original preserved in `raw_user_request`.
    """
    raw = state.get("raw_user_request") or state.get("user_request") or ""
    verdict = score_user_input(raw)

    patch = verdict.to_state_patch()
    patch["raw_user_request"] = raw
    patch["status"] = RunStatus.RUNNING.value

    decision_audit = verdict.decision.value
    if verdict.decision == GuardDecision.BLOCK:
        patch["status"] = RunStatus.REJECTED.value
        patch["refusal_message"] = verdict.refusal_message
    elif verdict.decision == GuardDecision.REWRITE:
        patch["user_request"] = verdict.sanitized_text or raw
    elif verdict.decision == GuardDecision.ALLOW:
        patch["user_request"] = verdict.sanitized_text or raw
    else:
        patch["user_request"] = verdict.sanitized_text or raw
        patch["input_escalation_pending"] = True

    patch.update(
        _audit(verdict.policy_id, decision_audit, verdict.detail),
    )
    return patch


def route_after_input_guard(state: dict[str, Any]) -> str:
    decision = state.get("input_guard_decision")
    if decision == GuardDecision.BLOCK.value:
        return "refuse"
    if decision == GuardDecision.ESCALATE.value:
        return "escalate"
    return "continue"


def refuse_input(state: dict[str, Any]) -> dict[str, Any]:
    msg = state.get("refusal_message") or "Request blocked by input policy."
    return {
        "status": RunStatus.REJECTED.value,
        "execution_result": msg,
        **_audit("input.refusal", "block", "user shown refusal"),
    }


def input_escalation_gate(state: dict[str, Any]) -> dict[str, Any]:
    """
    Security review for escalate path — uses interrupt() before agent/planner.

    Approve → continue to receive_request; reject → END.
    """
    payload = {
        "policy_id": state.get("input_guard_policy_id", "input.injection.escalate"),
        "message": "Security review required before this request proceeds.",
        "scores": state.get("input_guard_scores"),
        "request_preview": state.get("user_request"),
        "allowed_decisions": ["approve", "reject"],
    }

    raw = interrupt(payload)

    if isinstance(raw, dict) and raw.get("type") == "reject":
        return {
            "status": RunStatus.REJECTED.value,
            "execution_result": "security reviewer rejected escalated input",
            "input_escalation_pending": False,
            **_audit("input.escalation", "block", "reviewer rejected"),
        }

    return {
        "input_escalation_pending": False,
        **_audit("input.escalation", "allow", "reviewer approved escalated input"),
    }


def route_after_escalation(state: dict[str, Any]) -> str:
    if state.get("status") == RunStatus.REJECTED.value:
        return "end"
    return "continue"
