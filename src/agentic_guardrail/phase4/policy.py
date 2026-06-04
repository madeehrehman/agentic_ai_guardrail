"""Pre-execution policy: allowlist, schema, scope, budget."""

from __future__ import annotations

from typing import Any

from agentic_guardrail.phase1.models import (
    ActionKind,
    HumanDecision,
    HumanDecisionType,
    KineticProposal,
    parse_decision,
    parse_proposal,
)
from agentic_guardrail.phase4.models import (
    ToolAuthorizationVerdict,
    ToolGuardDecision,
    ToolScopePolicy,
    proposal_fingerprint,
)
from agentic_guardrail.phase4.loop_detect import detect_tool_loop_anomaly

REGULATORY_WORKFLOW_SCOPE = ToolScopePolicy(
    allowed_entity_ids={"entity-uk-bank-01"},
    allowed_finding_ids={"FIN-2024-017"},
)


def _effective_proposal(
    proposal: KineticProposal, decision: HumanDecision | None
) -> KineticProposal:
    if decision is None or decision.type != HumanDecisionType.EDIT:
        return proposal
    data = proposal.model_dump()
    if decision.edited_grc:
        data["grc"] = decision.edited_grc.model_dump()
    if decision.edited_email:
        data["email"] = decision.edited_email.model_dump()
    return KineticProposal.model_validate(data)


def authorize_tool_call(
    state: dict[str, Any],
    *,
    policy: ToolScopePolicy = REGULATORY_WORKFLOW_SCOPE,
    at_plan_stage: bool = False,
) -> ToolAuthorizationVerdict:
    """
    Pre-execution rail: scope, budget, loop anomaly, HITL routing hint.

    When ``at_plan_stage`` is True, only scope/HITL checks run (no budget debit yet).
    """
    proposal = parse_proposal(state.get("pending_proposal"))
    if proposal is None:
        return ToolAuthorizationVerdict(
            decision=ToolGuardDecision.BLOCK,
            policy_id="tool.pre.scope",
            detail="missing kinetic proposal",
        )

    decision = parse_decision(state.get("human_decision"))
    effective = _effective_proposal(proposal, decision)

    if effective.action not in policy.allowed_actions:
        return ToolAuthorizationVerdict(
            decision=ToolGuardDecision.BLOCK,
            policy_id="tool.pre.allowlist",
            detail=f"action {effective.action.value} not in agent allowlist",
            fingerprint=proposal_fingerprint(effective),
        )

    if policy.allowed_entity_ids and effective.entity_id not in policy.allowed_entity_ids:
        return ToolAuthorizationVerdict(
            decision=ToolGuardDecision.BLOCK,
            policy_id="tool.pre.scope",
            detail=f"entity {effective.entity_id} out of scope for {policy.agent_role}",
            fingerprint=proposal_fingerprint(effective),
        )

    if effective.action == ActionKind.GRC_CLOSE_FINDING and effective.grc:
        if (
            policy.allowed_finding_ids
            and effective.grc.finding_id not in policy.allowed_finding_ids
        ):
            return ToolAuthorizationVerdict(
                decision=ToolGuardDecision.BLOCK,
                policy_id="tool.pre.scope",
                detail=f"finding {effective.grc.finding_id} not authorized for this agent",
                fingerprint=proposal_fingerprint(effective),
            )

    if effective.action == ActionKind.EMAIL_SEND and effective.email:
        if len(effective.email.to) > policy.max_recipient_count:
            return ToolAuthorizationVerdict(
                decision=ToolGuardDecision.BLOCK,
                policy_id="tool.pre.schema",
                detail="recipient count exceeds limit",
                fingerprint=proposal_fingerprint(effective),
            )
        for addr in effective.email.to:
            if not addr.endswith("@bank.internal") and not addr.endswith(
                "@legal.bank.internal"
            ):
                return ToolAuthorizationVerdict(
                    decision=ToolGuardDecision.BLOCK,
                    policy_id="tool.pre.scope",
                    detail=f"recipient not allowlisted: {addr}",
                    fingerprint=proposal_fingerprint(effective),
                )

    if effective.action in policy.require_hitl_for:
        if at_plan_stage:
            return ToolAuthorizationVerdict(
                decision=ToolGuardDecision.ESCALATE,
                policy_id="tool.pre.hitl_required",
                detail=f"{effective.action.value} requires human approval (Phase 1 gate)",
                fingerprint=proposal_fingerprint(effective),
            )
        if decision is None or decision.type not in (
            HumanDecisionType.APPROVE,
            HumanDecisionType.EDIT,
        ):
            return ToolAuthorizationVerdict(
                decision=ToolGuardDecision.BLOCK,
                policy_id="tool.pre.hitl_required",
                detail="destructive action blocked without approve/edit decision",
                fingerprint=proposal_fingerprint(effective),
            )

    fingerprint = proposal_fingerprint(effective)
    history = list(state.get("tool_call_fingerprints") or [])
    anomaly = detect_tool_loop_anomaly(history, fingerprint)
    if anomaly:
        return ToolAuthorizationVerdict(
            decision=ToolGuardDecision.BLOCK,
            policy_id="tool.loop.anomaly",
            detail=anomaly,
            fingerprint=fingerprint,
        )

    if not at_plan_stage:
        max_actions = state.get("max_kinetic_actions", 1)
        action_count = state.get("kinetic_action_count", 0)
        if action_count >= max_actions:
            return ToolAuthorizationVerdict(
                decision=ToolGuardDecision.BLOCK,
                policy_id="tool.budget.actions",
                detail=f"kinetic action cap reached ({max_actions} per run)",
                fingerprint=fingerprint,
            )

        cost = policy.action_budget_cost.get(effective.action, 1)
        spent = state.get("tool_budget_spent", 0)
        max_budget = state.get("max_tool_budget", 15)
        if spent + cost > max_budget:
            return ToolAuthorizationVerdict(
                decision=ToolGuardDecision.BLOCK,
                policy_id="tool.budget.cost",
                detail=f"tool budget exceeded ({spent}+{cost} > {max_budget})",
                fingerprint=fingerprint,
            )

    return ToolAuthorizationVerdict(
        decision=ToolGuardDecision.ALLOW,
        policy_id="tool.pre.allow",
        detail="tool call authorized",
        fingerprint=fingerprint,
    )
