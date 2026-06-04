"""Input guard decision contract — allow | block | rewrite | escalate."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class GuardDecision(StrEnum):
    ALLOW = "allow"
    BLOCK = "block"
    REWRITE = "rewrite"
    ESCALATE = "escalate"


class PiiSpan(BaseModel):
    kind: str
    start: int
    end: int
    token: str


class InputGuardScores(BaseModel):
    injection: float = 0.0
    structural: float = 0.0
    policy: float = 0.0
    pii_count: int = 0


class InputGuardVerdict(BaseModel):
    decision: GuardDecision
    policy_id: str
    detail: str
    scores: InputGuardScores = Field(default_factory=InputGuardScores)
    sanitized_text: str | None = None
    pii_spans: list[PiiSpan] = Field(default_factory=list)
    pii_token_map: dict[str, str] = Field(default_factory=dict)
    refusal_message: str | None = None

    def to_state_patch(self) -> dict[str, Any]:
        return {
            "input_guard_decision": self.decision.value,
            "input_guard_policy_id": self.policy_id,
            "input_guard_detail": self.detail,
            "input_guard_scores": self.scores.model_dump(),
            "pii_token_map": self.pii_token_map,
            "refusal_message": self.refusal_message,
        }
