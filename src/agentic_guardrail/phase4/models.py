"""Phase 4 tool-call guard models."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

from agentic_guardrail.phase1.models import ActionKind, KineticProposal


class ToolGuardDecision(StrEnum):
    ALLOW = "allow"
    BLOCK = "block"
    ESCALATE = "escalate"


class ToolAuthorizationVerdict(BaseModel):
    decision: ToolGuardDecision
    policy_id: str
    detail: str
    fingerprint: str | None = None

    def to_state_patch(self) -> dict[str, Any]:
        return {
            "tool_authorization_decision": self.decision.value,
            "tool_authorization_policy_id": self.policy_id,
            "tool_authorization_detail": self.detail,
        }


class PostToolVerdict(BaseModel):
    decision: ToolGuardDecision
    policy_id: str
    detail: str
    sanitized_result: str | None = None

    def to_state_patch(self) -> dict[str, Any]:
        patch: dict[str, Any] = {
            "post_tool_decision": self.decision.value,
            "post_tool_policy_id": self.policy_id,
            "post_tool_detail": self.detail,
        }
        if self.sanitized_result is not None:
            patch["tool_result"] = self.sanitized_result
        return patch


class ToolScopePolicy(BaseModel):
    """Least-privilege capability contract for the regulatory workflow agent."""

    agent_role: str = "regulatory_workflow"
    allowed_actions: set[ActionKind] = Field(
        default_factory=lambda: {ActionKind.GRC_CLOSE_FINDING, ActionKind.EMAIL_SEND}
    )
    require_hitl_for: set[ActionKind] = Field(
        default_factory=lambda: {ActionKind.GRC_CLOSE_FINDING, ActionKind.EMAIL_SEND}
    )
    allowed_entity_ids: set[str] | None = None
    allowed_finding_ids: set[str] | None = Field(
        default_factory=lambda: {"FIN-2024-017"}
    )
    action_budget_cost: dict[ActionKind, int] = Field(
        default_factory=lambda: {
            ActionKind.GRC_CLOSE_FINDING: 10,
            ActionKind.EMAIL_SEND: 3,
        }
    )
    max_recipient_count: int = 5


def proposal_fingerprint(proposal: KineticProposal) -> str:
    if proposal.action == ActionKind.GRC_CLOSE_FINDING and proposal.grc:
        return f"{proposal.action.value}:{proposal.entity_id}:{proposal.grc.finding_id}"
    if proposal.action == ActionKind.EMAIL_SEND and proposal.email:
        recipients = ",".join(sorted(proposal.email.to))
        return f"{proposal.action.value}:{proposal.entity_id}:{recipients}"
    return f"{proposal.action.value}:{proposal.entity_id}"
