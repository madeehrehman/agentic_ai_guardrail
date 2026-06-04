"""Typed state and approval contracts for Phase 1 HITL."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Annotated, Any, Literal, TypedDict
from uuid import uuid4

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ActionKind(StrEnum):
    GRC_CLOSE_FINDING = "grc_close_finding"
    EMAIL_SEND = "email_send"


class RunStatus(StrEnum):
    RUNNING = "running"
    AWAITING_HUMAN = "awaiting_human"
    COMPLETED = "completed"
    REJECTED = "rejected"
    STALE_BLOCKED = "stale_blocked"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


class HumanDecisionType(StrEnum):
    APPROVE = "approve"
    EDIT = "edit"
    REJECT = "reject"
    TIMEOUT = "timeout"


class GrcClosePayload(BaseModel):
    finding_id: str
    comment: str = ""
    expected_status: str = "open"


class EmailSendPayload(BaseModel):
    to: list[str]
    subject: str
    body: str
    internal_only: bool = True


class KineticProposal(BaseModel):
    """Immutable snapshot shown to the reviewer at interrupt."""

    proposal_id: str = Field(default_factory=lambda: str(uuid4()))
    action: ActionKind
    rationale: str
    requested_by: str
    entity_id: str
    captured_at: datetime = Field(default_factory=_utc_now)
    grc: GrcClosePayload | None = None
    email: EmailSendPayload | None = None
    world_finding_version: int | None = None

    def model_post_init(self, __context: Any) -> None:
        if self.action == ActionKind.GRC_CLOSE_FINDING and self.grc is None:
            raise ValueError("grc payload required for grc_close_finding")
        if self.action == ActionKind.EMAIL_SEND and self.email is None:
            raise ValueError("email payload required for email_send")


class InterruptPayload(BaseModel):
    """Surfaced to the client when the graph interrupts."""

    policy_id: str = "hitl.kinetic.t0"
    message: str
    proposal: KineticProposal
    allowed_decisions: list[HumanDecisionType] = Field(
        default_factory=lambda: [
            HumanDecisionType.APPROVE,
            HumanDecisionType.EDIT,
            HumanDecisionType.REJECT,
        ]
    )
    timeout_seconds: int = 86400


class HumanDecision(BaseModel):
    type: HumanDecisionType
    reviewer_id: str
    decided_at: datetime = Field(default_factory=_utc_now)
    edited_grc: GrcClosePayload | None = None
    edited_email: EmailSendPayload | None = None
    comment: str = ""


class AuditEvent(BaseModel):
    at: datetime = Field(default_factory=_utc_now)
    policy_id: str
    decision: Literal["allow", "block", "rewrite", "escalate"]
    detail: str


def merge_audit(
    left: list[dict[str, Any]] | None, right: list[dict[str, Any]] | None
) -> list[dict[str, Any]]:
    if not left:
        return right or []
    if not right:
        return left
    return [*left, *right]


class State(TypedDict):
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


def parse_proposal(data: dict[str, Any] | None) -> KineticProposal | None:
    if not data:
        return None
    return KineticProposal.model_validate(data)


def parse_decision(data: dict[str, Any] | None) -> HumanDecision | None:
    if not data:
        return None
    return HumanDecision.model_validate(data)
