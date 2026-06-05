"""Phase 3 decision contracts — retrieval and output rails."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class GuardDecision(StrEnum):
    ALLOW = "allow"
    BLOCK = "block"
    REWRITE = "rewrite"
    ESCALATE = "escalate"


class RetrievedChunk(BaseModel):
    chunk_id: str
    source: str
    title: str
    text: str
    trust: str = "internal"  # internal | external | untrusted


class RetrievalVerdict(BaseModel):
    decision: GuardDecision
    policy_id: str
    detail: str
    approved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    blocked_chunk_ids: list[str] = Field(default_factory=list)
    injection_score: float = 0.0

    def to_state_patch(self) -> dict[str, Any]:
        return {
            "retrieval_decision": self.decision.value,
            "retrieval_policy_id": self.policy_id,
            "retrieval_detail": self.detail,
            "retrieved_chunks": [c.model_dump() for c in self.approved_chunks],
            "approved_chunks": [c.model_dump() for c in self.approved_chunks],
            "blocked_chunk_ids": self.blocked_chunk_ids,
        }


class OutputVerdict(BaseModel):
    decision: GuardDecision
    policy_id: str
    detail: str
    final_response: str
    leak_detected: bool = False
    secrets_detected: bool = False
    framework: str | None = None  # handrolled | guardrails-ai | layered

    def to_state_patch(self) -> dict[str, Any]:
        patch = {
            "output_guard_decision": self.decision.value,
            "output_guard_policy_id": self.policy_id,
            "output_guard_detail": self.detail,
            "final_response": self.final_response,
        }
        if self.framework:
            patch["output_guard_framework"] = self.framework
        return patch
