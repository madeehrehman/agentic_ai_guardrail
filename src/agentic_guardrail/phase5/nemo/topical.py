"""Topical / dialog rail — NeMo-shaped stub; swap for RunnableRails when NeMo is installed."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

# Mirrors Colang-style intent: stay on regulatory workflow topics.
ALLOWED_TOPIC_PATTERNS: list[str] = [
    r"\b(bcbs|basel|regulatory|compliance|finding|remediation|grc|liquidity|policy)\b",
    r"\b(close|email|notify|summarize|risk data)\b",
    r"\bFIN-\d{4}-\d+\b",
]

OFF_TOPIC_PATTERNS: list[str] = [
    r"\b(write|compose|draft)\b.+\b(poem|story|joke|song)\b",
    r"\b(crypto|bitcoin|stock tip|gambling)\b",
    r"\b(hack|exploit|bypass)\b.+\b(system|guardrail)\b",
]


class TopicalDecision(StrEnum):
    ALLOW = "allow"
    BLOCK = "block"
    STEER = "steer"


@dataclass(frozen=True)
class TopicalVerdict:
    decision: TopicalDecision
    policy_id: str
    detail: str
    steered_request: str | None = None

    def to_state_patch(self) -> dict:
        patch = {
            "topical_decision": self.decision.value,
            "topical_policy_id": self.policy_id,
            "topical_detail": self.detail,
        }
        if self.steered_request is not None:
            patch["user_request"] = self.steered_request
        return patch


def score_topical(request: str) -> TopicalVerdict:
    """Stub topical rail — replace with NeMo `RunnableRails` on chat-heavy surfaces."""
    text = (request or "").lower()
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, text, re.I):
            return TopicalVerdict(
                decision=TopicalDecision.BLOCK,
                policy_id="dialog.topical.block",
                detail=f"off-topic pattern matched: {pattern}",
            )
    for pattern in ALLOWED_TOPIC_PATTERNS:
        if re.search(pattern, text, re.I):
            return TopicalVerdict(
                decision=TopicalDecision.ALLOW,
                policy_id="dialog.topical.allow",
                detail="request within regulatory workflow topics",
            )
    return TopicalVerdict(
        decision=TopicalDecision.STEER,
        policy_id="dialog.topical.steer",
        detail="request unclear; steering to policy Q&A framing",
        steered_request=(
            "Summarize applicable internal regulatory policy for: " + request.strip()
        ),
    )
