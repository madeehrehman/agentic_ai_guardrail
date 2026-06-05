"""Project validators registered for Guardrails AI (no Hub CLI required)."""

from __future__ import annotations

from typing import Any

from guardrails.validator_base import Validator, register_validator
from guardrails_ai.types import FailResult, PassResult

from agentic_guardrail.phase3.scanners import (
    scan_groundedness,
    scan_output_prompt_leak,
    scan_output_secrets,
)


@register_validator(name="regulatory/no_secrets", data_type="string")
class RegulatoryNoSecrets(Validator):
    """Block API keys and private key material in model output."""

    def _validate(self, value: Any, metadata: dict[str, Any]) -> PassResult | FailResult:
        hits = scan_output_secrets(str(value))
        if hits:
            return FailResult(
                error_message=f"secrets patterns matched: {len(hits)}",
                metadata={"policy_id": "output.secrets.block"},
            )
        return PassResult()


@register_validator(name="regulatory/no_prompt_leak", data_type="string")
class RegulatoryNoPromptLeak(Validator):
    """LLM07 — block known system-prompt fragments in user-facing output."""

    def _validate(self, value: Any, metadata: dict[str, Any]) -> PassResult | FailResult:
        leaks = scan_output_prompt_leak(str(value))
        if leaks:
            return FailResult(
                error_message=f"system prompt fragments detected: {len(leaks)}",
                metadata={"policy_id": "output.prompt_leak.block"},
            )
        return PassResult()


@register_validator(name="regulatory/groundedness", data_type="string")
class RegulatoryGroundedness(Validator):
    """Require [source:chunk_id] citations on longer regulatory answers."""

    def _validate(self, value: Any, metadata: dict[str, Any]) -> PassResult | FailResult:
        chunk_ids = metadata.get("approved_chunk_ids") or []
        ok, reason = scan_groundedness(str(value), chunk_ids)
        if ok:
            return PassResult()
        return FailResult(
            error_message=reason,
            metadata={"policy_id": "output.groundedness.rewrite", "rewrite": True},
        )
