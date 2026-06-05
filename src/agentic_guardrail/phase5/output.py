"""Unified output scoring — selects hand-rolled vs Guardrails AI backend."""

from __future__ import annotations

from agentic_guardrail.phase3.guards import score_output as handrolled_score_output
from agentic_guardrail.phase3.models import OutputVerdict
from agentic_guardrail.phase5.config import OutputBackend, guardrails_available, output_backend


def score_output(
    response: str,
    *,
    approved_chunk_ids: list[str] | None = None,
    simulate_leak: bool = False,
    **kwargs,
) -> OutputVerdict:
    backend = output_backend()
    if backend == OutputBackend.HANDROLLED or not guardrails_available():
        verdict = handrolled_score_output(
            response,
            approved_chunk_ids=approved_chunk_ids,
            simulate_leak=simulate_leak,
            **kwargs,
        )
        verdict.framework = "handrolled"
        return verdict

    from agentic_guardrail.phase5.guardrails_output import (
        score_output_guardrails,
        score_output_layered,
    )

    if backend == OutputBackend.GUARDRAILS:
        return score_output_guardrails(
            response,
            approved_chunk_ids=approved_chunk_ids,
            simulate_leak=simulate_leak,
        )
    return score_output_layered(
        response,
        approved_chunk_ids=approved_chunk_ids,
        simulate_leak=simulate_leak,
        **kwargs,
    )
