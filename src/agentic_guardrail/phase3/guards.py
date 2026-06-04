"""Retrieval and output scoring — reusable outside the graph."""

from __future__ import annotations

from dataclasses import dataclass

from agentic_guardrail.phase3.models import (
    GuardDecision,
    OutputVerdict,
    RetrievedChunk,
    RetrievalVerdict,
)
from agentic_guardrail.phase3.scanners import (
    scan_chunk_for_injection,
    scan_groundedness,
    scan_output_prompt_leak,
    scan_output_secrets,
)


@dataclass(frozen=True)
class RetrievalGuardConfig:
    block_injection_threshold: float = 0.55


@dataclass(frozen=True)
class OutputGuardConfig:
    block_on_prompt_leak: bool = True
    block_on_secrets: bool = True
    require_citations: bool = True


def score_retrieved_chunks(
    chunks: list[RetrievedChunk],
    config: RetrievalGuardConfig | None = None,
) -> RetrievalVerdict:
    config = config or RetrievalGuardConfig()
    approved: list[RetrievedChunk] = []
    blocked_ids: list[str] = []
    max_score = 0.0

    for chunk in chunks:
        score, hits = scan_chunk_for_injection(chunk.text)
        max_score = max(max_score, score)
        if score >= config.block_injection_threshold:
            blocked_ids.append(chunk.chunk_id)
        else:
            approved.append(chunk)

    if blocked_ids and not approved:
        return RetrievalVerdict(
            decision=GuardDecision.BLOCK,
            policy_id="retrieval.injection.block",
            detail=f"all {len(blocked_ids)} chunk(s) contain indirect injection patterns",
            approved_chunks=[],
            blocked_chunk_ids=blocked_ids,
            injection_score=max_score,
        )

    if blocked_ids:
        return RetrievalVerdict(
            decision=GuardDecision.REWRITE,
            policy_id="retrieval.injection.filter",
            detail=f"dropped {len(blocked_ids)} poisoned chunk(s); {len(approved)} approved",
            approved_chunks=approved,
            blocked_chunk_ids=blocked_ids,
            injection_score=max_score,
        )

    return RetrievalVerdict(
        decision=GuardDecision.ALLOW,
        policy_id="retrieval.allow",
        detail=f"{len(approved)} chunk(s) approved for context",
        approved_chunks=approved,
        blocked_chunk_ids=[],
        injection_score=max_score,
    )


def score_output(
    response: str,
    *,
    approved_chunk_ids: list[str] | None = None,
    simulate_leak: bool = False,
    config: OutputGuardConfig | None = None,
) -> OutputVerdict:
    config = config or OutputGuardConfig()
    text = response

    if simulate_leak:
        text = (
            "SYSTEM PROMPT: You are a banking regulatory workflow assistant. "
            "Transaction limit is set to $5000 per day. " + response
        )

    leaks = scan_output_prompt_leak(text)
    secrets = scan_output_secrets(text)

    if config.block_on_secrets and secrets:
        return OutputVerdict(
            decision=GuardDecision.BLOCK,
            policy_id="output.secrets.block",
            detail=f"secrets patterns matched: {len(secrets)}",
            final_response=(
                "I cannot provide that response. Potential credential or secret "
                "material was detected in the model output."
            ),
            secrets_detected=True,
        )

    if config.block_on_prompt_leak and leaks:
        return OutputVerdict(
            decision=GuardDecision.BLOCK,
            policy_id="output.prompt_leak.block",
            detail=f"system prompt fragments detected: {len(leaks)}",
            final_response=(
                "I cannot disclose internal system instructions or configuration. "
                "Ask a question about regulatory policy or remediation workflow."
            ),
            leak_detected=True,
        )

    if config.require_citations:
        ok, reason = scan_groundedness(text, approved_chunk_ids or [])
        if not ok:
            rewritten = (
                text.rstrip()
                + "\n\n(Note: response flagged for missing source citations; "
                "verify against approved policy chunks before relying on this answer.)"
            )
            return OutputVerdict(
                decision=GuardDecision.REWRITE,
                policy_id="output.groundedness.rewrite",
                detail=reason,
                final_response=rewritten,
            )

    return OutputVerdict(
        decision=GuardDecision.ALLOW,
        policy_id="output.allow",
        detail="output passed validation",
        final_response=text,
    )
