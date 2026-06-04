"""Phase 1 graph nodes — planner stub, HITL gate, stale validation, execution."""

from __future__ import annotations

from typing import Any

from langgraph.types import interrupt

from agentic_guardrail.phase1 import backends
from agentic_guardrail.phase1.backends import WorldState
from agentic_guardrail.phase1.models import (
    ActionKind,
    AuditEvent,
    EmailSendPayload,
    GrcClosePayload,
    HumanDecision,
    HumanDecisionType,
    InterruptPayload,
    KineticProposal,
    RunStatus,
    parse_decision,
    parse_proposal,
)


def _audit(policy_id: str, decision: str, detail: str) -> dict[str, Any]:
    return {
        "audit_log": [
            AuditEvent(policy_id=policy_id, decision=decision, detail=detail).model_dump(
                mode="json"
            )
        ]
    }


def receive_request(state: dict[str, Any]) -> dict[str, Any]:
    loops = state.get("loop_count", 0) + 1
    if loops > state.get("max_loops", 8):
        return {
            "status": RunStatus.FAILED.value,
            "execution_result": "loop limit exceeded",
            **_audit("control.loop", "block", "max_loops reached"),
        }
    return {
        "loop_count": loops,
        "status": RunStatus.RUNNING.value,
        **_audit("control.loop", "allow", f"iteration {loops}"),
    }


def plan_kinetic_action(state: dict[str, Any]) -> dict[str, Any]:
    """Stub planner: maps keywords to highest-blast-radius actions (no side effects)."""
    req = (state.get("user_request") or "").lower()
    user_id = state["user_id"]
    entity_id = state.get("entity_id", "entity-uk-bank-01")

    if "close" in req and "finding" in req:
        finding_id = "FIN-2024-017"
        finding = backends.WORLD.get_finding(finding_id)
        proposal = KineticProposal(
            action=ActionKind.GRC_CLOSE_FINDING,
            rationale="User requested remediation closure for BCBS gap finding.",
            requested_by=user_id,
            entity_id=entity_id,
            grc=GrcClosePayload(
                finding_id=finding_id,
                comment="Remediation complete per control testing.",
                expected_status="open",
            ),
            world_finding_version=finding.version if finding else None,
        )
    elif "email" in req or "notify" in req:
        proposal = KineticProposal(
            action=ActionKind.EMAIL_SEND,
            rationale="User requested notification to compliance distribution.",
            requested_by=user_id,
            entity_id=entity_id,
            email=EmailSendPayload(
                to=["compliance-leads@bank.internal"],
                subject="Regulatory workflow notification",
                body="Please review the attached remediation summary.",
                internal_only=True,
            ),
        )
    else:
        return {
            "status": RunStatus.FAILED.value,
            "execution_result": "no kinetic action planned for request",
            **_audit("planner.route", "block", "unsupported request"),
        }

    return {
        "pending_proposal": proposal.model_dump(mode="json"),
        **_audit("planner.route", "allow", f"proposed {proposal.action.value}"),
    }


def human_approval_gate(state: dict[str, Any]) -> dict[str, Any]:
    """
    HITL gate: idempotent snapshot before interrupt(); process decision after resume.

    LangGraph re-runs this node from the top on resume — do not perform writes
    before interrupt().
    """
    proposal = parse_proposal(state.get("pending_proposal"))
    if proposal is None:
        return {
            "status": RunStatus.FAILED.value,
            "execution_result": "missing proposal at gate",
            **_audit("hitl.kinetic.t0", "block", "no proposal"),
        }

    payload = InterruptPayload(
        message=(
            "Approve, edit, or reject this kinetic action. "
            "World state will be re-validated after your decision."
        ),
        proposal=proposal,
    )

    # Pause execution — resume value becomes return of interrupt() on next entry
    raw = interrupt(payload.model_dump(mode="json"))

    if isinstance(raw, dict) and raw.get("type") == HumanDecisionType.TIMEOUT.value:
        decision = HumanDecision(
            type=HumanDecisionType.TIMEOUT,
            reviewer_id="system",
            comment="approval window elapsed",
        )
    else:
        decision = HumanDecision.model_validate(raw)

    return {
        "human_decision": decision.model_dump(mode="json"),
        "status": RunStatus.RUNNING.value,
        **_audit(
            "hitl.kinetic.t0",
            "escalate" if decision.type == HumanDecisionType.TIMEOUT else "allow",
            f"human {decision.type.value} by {decision.reviewer_id}",
        ),
    }


def route_after_human(state: dict[str, Any]) -> str:
    decision = parse_decision(state.get("human_decision"))
    if decision is None:
        return "fail"
    if decision.type == HumanDecisionType.REJECT:
        return "reject"
    if decision.type == HumanDecisionType.TIMEOUT:
        return "timeout"
    if decision.type in (HumanDecisionType.APPROVE, HumanDecisionType.EDIT):
        return "validate"
    return "fail"


def reject_action(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": RunStatus.REJECTED.value,
        "execution_result": "human rejected kinetic action",
        **_audit("hitl.kinetic.t0", "block", "reviewer rejected"),
    }


def timeout_action(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": RunStatus.TIMED_OUT.value,
        "execution_result": "human approval timed out — escalated",
        **_audit("hitl.kinetic.t0", "escalate", "timeout fallback"),
    }


def validate_after_resume(
    state: dict[str, Any], world: WorldState | None = None
) -> dict[str, Any]:
    """Re-check world state after resume — stale finding is a common failure mode."""
    world = world or backends.WORLD
    proposal = parse_proposal(state.get("pending_proposal"))
    decision = parse_decision(state.get("human_decision"))
    if proposal is None or decision is None:
        return {
            "status": RunStatus.FAILED.value,
            "execution_result": "validation missing proposal or decision",
            **_audit("hitl.stale_check", "block", "invalid state"),
        }

    effective = _effective_payload(proposal, decision)

    if proposal.action == ActionKind.GRC_CLOSE_FINDING and effective.grc:
        finding = world.get_finding(effective.grc.finding_id)
        if finding is None:
            return _stale(f"finding {effective.grc.finding_id} not found")
        if finding.status != "open":
            return _stale(f"finding status is {finding.status}, expected open")
        if proposal.world_finding_version is not None and finding.version != proposal.world_finding_version:
            return _stale(
                f"finding version drift: proposed v{proposal.world_finding_version}, "
                f"current v{finding.version}"
            )
        if finding.entity_id != proposal.entity_id:
            return _stale("entity scope mismatch")

    if proposal.action == ActionKind.EMAIL_SEND and effective.email:
        for addr in effective.email.to:
            if not addr.endswith("@bank.internal") and not addr.endswith(
                "@legal.bank.internal"
            ):
                return _stale(f"recipient not allowlisted: {addr}")

    return {
        **_audit("hitl.stale_check", "allow", "world state consistent at execution"),
    }


def _stale(reason: str) -> dict[str, Any]:
    return {
        "status": RunStatus.STALE_BLOCKED.value,
        "execution_result": f"stale state blocked execution: {reason}",
        **_audit("hitl.stale_check", "block", reason),
    }


def _effective_payload(
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


def execute_kinetic(state: dict[str, Any], world: WorldState | None = None) -> dict[str, Any]:
    """Side effects only after approve/edit + stale check — idempotent per proposal_id."""
    world = world or backends.WORLD
    proposal = parse_proposal(state.get("pending_proposal"))
    decision = parse_decision(state.get("human_decision"))
    if proposal is None or decision is None:
        return {"status": RunStatus.FAILED.value, "execution_result": "cannot execute"}

    effective = _effective_payload(proposal, decision)
    dedupe_key = f"executed:{effective.proposal_id}"
    if state.get("execution_result") == dedupe_key:
        return {}

    try:
        if effective.action == ActionKind.GRC_CLOSE_FINDING and effective.grc:
            result = world.close_finding(
                effective.grc.finding_id, effective.grc.comment or "approved close"
            )
        elif effective.action == ActionKind.EMAIL_SEND and effective.email:
            result = world.send_email(
                effective.email.to,
                effective.email.subject,
                effective.email.body,
            )
        else:
            return {"status": RunStatus.FAILED.value, "execution_result": "unknown action"}
    except ValueError as exc:
        return {
            "status": RunStatus.STALE_BLOCKED.value,
            "execution_result": str(exc),
            **_audit("executor.kinetic", "block", str(exc)),
        }

    return {
        "status": RunStatus.COMPLETED.value,
        "execution_result": dedupe_key,
        **_audit("executor.kinetic", "allow", result),
    }


def fail_run(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("execution_result"):
        return {}
    return {
        "status": RunStatus.FAILED.value,
        "execution_result": "workflow failed",
        **_audit("control.fail", "block", "routed to fail"),
    }
