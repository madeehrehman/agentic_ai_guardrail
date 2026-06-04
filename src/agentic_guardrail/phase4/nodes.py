"""Phase 4 graph nodes — pre-authorize, authorize, guarded execution."""

from __future__ import annotations

from typing import Any

from agentic_guardrail.phase1.models import AuditEvent, RunStatus
from agentic_guardrail.phase4.guarded_tool import guarded_tool
from agentic_guardrail.phase4.models import ToolGuardDecision
from agentic_guardrail.phase4.policy import authorize_tool_call


def _audit(policy_id: str, decision: str, detail: str) -> dict[str, Any]:
    return {
        "audit_log": [
            AuditEvent(policy_id=policy_id, decision=decision, detail=detail).model_dump(
                mode="json"
            )
        ]
    }


def pre_authorize_proposal(state: dict[str, Any]) -> dict[str, Any]:
    """Pre-execution scope + HITL routing before the human gate."""
    verdict = authorize_tool_call(state, at_plan_stage=True)
    patch = verdict.to_state_patch()
    if verdict.fingerprint:
        patch["tool_call_fingerprints"] = list(state.get("tool_call_fingerprints") or [])

    if verdict.decision == ToolGuardDecision.BLOCK:
        return {
            "status": RunStatus.FAILED.value,
            "execution_result": verdict.detail,
            "pending_proposal": None,
            **patch,
            **_audit(verdict.policy_id, "block", verdict.detail),
        }

    if verdict.decision == ToolGuardDecision.ESCALATE:
        return {
            **patch,
            **_audit(verdict.policy_id, "escalate", verdict.detail),
        }

    return {
        **patch,
        **_audit(verdict.policy_id, "allow", verdict.detail),
    }


def route_after_pre_authorize(state: dict[str, Any]) -> str:
    if state.get("tool_authorization_decision") == ToolGuardDecision.BLOCK.value:
        return "fail"
    if state.get("pending_proposal"):
        return "human_gate"
    return "fail"


def authorize_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Final pre-execution check (budget, loop) immediately before side effects."""
    verdict = authorize_tool_call(state, at_plan_stage=False)
    patch = verdict.to_state_patch()
    if verdict.decision != ToolGuardDecision.ALLOW:
        return {
            "status": RunStatus.FAILED.value,
            "execution_result": verdict.detail,
            **patch,
            **_audit(verdict.policy_id, "block", verdict.detail),
        }
    return {
        **patch,
        **_audit(verdict.policy_id, "allow", verdict.detail),
    }


def route_after_authorize(state: dict[str, Any]) -> str:
    if state.get("tool_authorization_decision") == ToolGuardDecision.ALLOW.value:
        return "execute"
    return "end"


def execute_guarded(state: dict[str, Any]) -> dict[str, Any]:
    return guarded_tool(state)


def tool_authorization_refusal(state: dict[str, Any]) -> dict[str, Any]:
    detail = state.get("tool_authorization_detail") or state.get("execution_result")
    return {
        "status": RunStatus.FAILED.value,
        "final_response": f"Tool call blocked by policy: {detail}",
        **_audit(
            state.get("tool_authorization_policy_id") or "tool.pre",
            "block",
            str(detail),
        ),
    }
