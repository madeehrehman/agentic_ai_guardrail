"""Aggregate scanners into a single input guard verdict."""

from __future__ import annotations

from dataclasses import dataclass

from agentic_guardrail.phase2.models import (
    GuardDecision,
    InputGuardScores,
    InputGuardVerdict,
    PiiSpan,
)
from agentic_guardrail.phase2.scanners import (
    apply_pii_tokens,
    scan_injection,
    scan_pii,
    scan_structure,
)


@dataclass(frozen=True)
class InputGuardConfig:
    block_injection_threshold: float = 0.85
    escalate_injection_threshold: float = 0.55
    max_chars: int = 8000


def score_user_input(text: str, config: InputGuardConfig | None = None) -> InputGuardVerdict:
    config = config or InputGuardConfig()

    injection = scan_injection(text)
    structural_score, structural_detail = scan_structure(text, max_chars=config.max_chars)
    pii = scan_pii(text)

    scores = InputGuardScores(
        injection=injection.score,
        structural=structural_score,
        policy=0.0,
        pii_count=len(pii.spans),
    )

    if structural_score >= 0.9:
        return InputGuardVerdict(
            decision=GuardDecision.BLOCK,
            policy_id="input.structural",
            detail=structural_detail,
            scores=scores,
            refusal_message="Your request could not be processed (policy: input size/format).",
        )

    if injection.score >= config.block_injection_threshold:
        return InputGuardVerdict(
            decision=GuardDecision.BLOCK,
            policy_id="input.injection.block",
            detail=f"prompt injection indicators: {len(injection.hits)} hit(s)",
            scores=scores,
            refusal_message=(
                "Your request was blocked by the input safety policy. "
                "If this is a legitimate compliance query, rephrase without override instructions."
            ),
        )

    if injection.score >= config.escalate_injection_threshold:
        return InputGuardVerdict(
            decision=GuardDecision.ESCALATE,
            policy_id="input.injection.escalate",
            detail=f"suspicious input (score={injection.score:.2f}) — security review required",
            scores=scores,
            sanitized_text=text,
        )

    if pii.spans:
        sanitized = apply_pii_tokens(text, pii)
        return InputGuardVerdict(
            decision=GuardDecision.REWRITE,
            policy_id="input.pii.tokenize",
            detail=f"tokenized {len(pii.spans)} PII span(s) before agent processing",
            scores=scores,
            sanitized_text=sanitized,
            pii_spans=[
                PiiSpan(kind=k, start=s, end=e, token=f"<PII_{k.upper()}>")
                for k, s, e, _ in pii.spans
            ],
            pii_token_map=pii.token_map,
        )

    return InputGuardVerdict(
        decision=GuardDecision.ALLOW,
        policy_id="input.allow",
        detail="input passed guard checks",
        scores=scores,
        sanitized_text=text,
    )
