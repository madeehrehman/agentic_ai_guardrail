"""guarded_tool — pre/post rails, budget accounting, execution."""

from __future__ import annotations

from typing import Any

from agentic_guardrail.phase1 import backends
from agentic_guardrail.phase1.backends import WorldState
from agentic_guardrail.phase1.models import (
    ActionKind,
    AuditEvent,
    HumanDecision,
    HumanDecisionType,
    KineticProposal,
    RunStatus,
    parse_decision,
    parse_proposal,
)
from agentic_guardrail.phase3.scanners import scan_chunk_for_injection
from agentic_guardrail.phase4.models import (
    PostToolVerdict,
    ToolGuardDecision,
    ToolScopePolicy,
    proposal_fingerprint,
)
from agentic_guardrail.phase4.policy import REGULATORY_WORKFLOW_SCOPE, authorize_tool_call


def _audit(policy_id: str, decision: str, detail: str) -> dict[str, Any]:
    return {
        "audit_log": [
            AuditEvent(policy_id=policy_id, decision=decision, detail=detail).model_dump(
                mode="json"
            )
        ]
    }


def _effective_proposal(
    proposal: KineticProposal, decision: HumanDecision
) -> KineticProposal:
    if decision.type != HumanDecisionType.EDIT:
        return proposal
    data = proposal.model_dump()
    if decision.edited_grc:
        data["grc"] = decision.edited_grc.model_dump()
    if decision.edited_email:
        data["email"] = decision.edited_email.model_dump()
    return KineticProposal.model_validate(data)


def score_tool_result(raw_result: str) -> PostToolVerdict:
    """Post-execution rail — tool output is untrusted input (Phase 3 pattern)."""
    score, hits = scan_chunk_for_injection(raw_result)
    if score >= 0.85 or hits:
        return PostToolVerdict(
            decision=ToolGuardDecision.BLOCK,
            policy_id="tool.post.injection",
            detail=f"tool result blocked: injection signals {hits or score}",
        )
    return PostToolVerdict(
        decision=ToolGuardDecision.ALLOW,
        policy_id="tool.post.allow",
        detail="tool result safe to retain",
        sanitized_result=raw_result,
    )


def guarded_tool(
    state: dict[str, Any],
    *,
    world: WorldState | None = None,
    policy: ToolScopePolicy = REGULATORY_WORKFLOW_SCOPE,
) -> dict[str, Any]:
    """
    Execute a kinetic proposal after pre-authorization and apply post-exec scanning.

    Caller must run ``authorize_tool_call`` first (workflow ``authorize_tool`` node).
    """
    world = world or backends.WORLD
    auth = authorize_tool_call(state, policy=policy, at_plan_stage=False)
    if auth.decision != ToolGuardDecision.ALLOW:
        return {
            "status": RunStatus.FAILED.value,
            "execution_result": auth.detail,
            **auth.to_state_patch(),
            **_audit(auth.policy_id, "block", auth.detail),
        }

    proposal = parse_proposal(state.get("pending_proposal"))
    decision = parse_decision(state.get("human_decision"))
    if proposal is None or decision is None:
        return {
            "status": RunStatus.FAILED.value,
            "execution_result": "missing proposal or decision",
            **_audit("tool.executor", "block", "invalid state"),
        }

    effective = _effective_proposal(proposal, decision)
    dedupe_key = f"executed:{effective.proposal_id}"
    if state.get("execution_result") == dedupe_key:
        return {}

    try:
        if effective.action == ActionKind.GRC_CLOSE_FINDING and effective.grc:
            raw = world.close_finding(
                effective.grc.finding_id,
                effective.grc.comment or "approved close",
            )
        elif effective.action == ActionKind.EMAIL_SEND and effective.email:
            raw = world.send_email(
                effective.email.to,
                effective.email.subject,
                effective.email.body,
            )
        else:
            return {
                "status": RunStatus.FAILED.value,
                "execution_result": "unknown action",
                **_audit("tool.executor", "block", "unknown action"),
            }
    except ValueError as exc:
        return {
            "status": RunStatus.STALE_BLOCKED.value,
            "execution_result": str(exc),
            **_audit("tool.executor", "block", str(exc)),
        }

    post = score_tool_result(raw)
    if post.decision == ToolGuardDecision.BLOCK:
        return {
            "status": RunStatus.STALE_BLOCKED.value,
            "execution_result": post.detail,
            **post.to_state_patch(),
            **_audit(post.policy_id, "block", post.detail),
        }

    cost = policy.action_budget_cost.get(effective.action, 1)
    fingerprint = proposal_fingerprint(effective)
    history = list(state.get("tool_call_fingerprints") or [])
    if fingerprint:
        history.append(fingerprint)

    return {
        "status": RunStatus.COMPLETED.value,
        "execution_result": dedupe_key,
        "tool_result": post.sanitized_result,
        "kinetic_action_count": state.get("kinetic_action_count", 0) + 1,
        "tool_budget_spent": state.get("tool_budget_spent", 0) + cost,
        "tool_call_fingerprints": history,
        **post.to_state_patch(),
        **_audit("tool.executor", "allow", raw),
    }
