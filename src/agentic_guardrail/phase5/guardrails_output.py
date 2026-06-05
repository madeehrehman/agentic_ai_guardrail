"""Guardrails AI adapter for Phase 3 output scoring."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from guardrails import Guard
from guardrails.types.on_fail import OnFailAction

from agentic_guardrail.phase3.guards import score_output as handrolled_score_output
from agentic_guardrail.phase3.models import GuardDecision, OutputVerdict
from agentic_guardrail.phase5.validators import (
    RegulatoryGroundedness,
    RegulatoryNoPromptLeak,
    RegulatoryNoSecrets,
)


REFUSAL_SECRETS = (
    "I cannot provide that response. Potential credential or secret "
    "material was detected in the model output."
)
REFUSAL_LEAK = (
    "I cannot disclose internal system instructions or configuration. "
    "Ask a question about regulatory policy or remediation workflow."
)


@lru_cache(maxsize=1)
def _output_guard() -> Guard:
    return Guard().use(
        RegulatoryNoSecrets(on_fail=OnFailAction.EXCEPTION),
        RegulatoryNoPromptLeak(on_fail=OnFailAction.EXCEPTION),
        RegulatoryGroundedness(on_fail=OnFailAction.EXCEPTION),
    )


def score_output_guardrails(
    response: str,
    *,
    approved_chunk_ids: list[str] | None = None,
    simulate_leak: bool = False,
) -> OutputVerdict:
    text = response
    if simulate_leak:
        text = (
            "SYSTEM PROMPT: You are a banking regulatory workflow assistant. "
            "Transaction limit is set to $5000 per day. " + response
        )

    metadata = {"approved_chunk_ids": approved_chunk_ids or []}
    guard = _output_guard()
    try:
        outcome = guard.validate(text, metadata=metadata)
        validated = outcome.validated_output
        out_text = validated if isinstance(validated, str) else text
        return OutputVerdict(
            decision=GuardDecision.ALLOW,
            policy_id="output.guardrails.allow",
            detail="Guardrails AI validators passed",
            final_response=out_text,
            framework="guardrails-ai",
        )
    except Exception as exc:
        policy_id = "output.guardrails.block"
        rewrite = False
        detail = str(exc)
        if "secrets" in detail.lower() or "secret" in detail.lower():
            policy_id = "output.secrets.block"
        elif "prompt" in detail.lower() and "fragment" in detail.lower():
            policy_id = "output.prompt_leak.block"
        elif "citation" in detail.lower() or "groundedness" in detail.lower():
            policy_id = "output.groundedness.rewrite"
            rewrite = True

        if "secrets" in policy_id:
            return OutputVerdict(
                decision=GuardDecision.BLOCK,
                policy_id=policy_id,
                detail=detail,
                final_response=REFUSAL_SECRETS,
                secrets_detected=True,
                framework="guardrails-ai",
            )
        if "prompt_leak" in policy_id:
            return OutputVerdict(
                decision=GuardDecision.BLOCK,
                policy_id=policy_id,
                detail=detail,
                final_response=REFUSAL_LEAK,
                leak_detected=True,
                framework="guardrails-ai",
            )
        if rewrite or "groundedness" in policy_id:
            rewritten = (
                text.rstrip()
                + "\n\n(Note: response flagged for missing source citations; "
                "verify against approved policy chunks before relying on this answer.)"
            )
            return OutputVerdict(
                decision=GuardDecision.REWRITE,
                policy_id=policy_id,
                detail=detail,
                final_response=rewritten,
                framework="guardrails-ai",
            )

        return OutputVerdict(
            decision=GuardDecision.BLOCK,
            policy_id=policy_id,
            detail=detail,
            final_response="Output blocked by Guardrails AI policy.",
            framework="guardrails-ai",
        )


def score_output_layered(
    response: str,
    *,
    approved_chunk_ids: list[str] | None = None,
    simulate_leak: bool = False,
    **kwargs: Any,
) -> OutputVerdict:
    """Run Guardrails validators, then hand-rolled checks for parity with Phase 3 tests."""
    first = score_output_guardrails(
        response,
        approved_chunk_ids=approved_chunk_ids,
        simulate_leak=simulate_leak,
    )
    if first.decision != GuardDecision.ALLOW:
        return first
    second = handrolled_score_output(
        first.final_response,
        approved_chunk_ids=approved_chunk_ids,
        simulate_leak=False,
        **kwargs,
    )
    if second.decision == GuardDecision.ALLOW:
        second.framework = "layered"
    return second
