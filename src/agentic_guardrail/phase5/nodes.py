"""Phase 5 LangGraph nodes — topical dialog rail (NeMo-shaped)."""

from __future__ import annotations

from typing import Any

from agentic_guardrail.phase1.models import AuditEvent, RunStatus
from agentic_guardrail.phase5.config import TopicalBackend, topical_backend
from agentic_guardrail.phase5.nemo.adapter import score_topical_nemo
from agentic_guardrail.phase5.nemo.topical import TopicalDecision, score_topical


def _audit(policy_id: str, decision: str, detail: str) -> dict[str, Any]:
    return {
        "audit_log": [
            AuditEvent(policy_id=policy_id, decision=decision, detail=detail).model_dump(
                mode="json"
            )
        ]
    }


def topical_dialog_rail(state: dict[str, Any]) -> dict[str, Any]:
    """Multi-turn topical boundary (stub or NeMo). Skipped when backend is ``off``."""
    if topical_backend() == TopicalBackend.OFF:
        return _audit("dialog.topical", "allow", "topical rail disabled")

    request = state.get("user_request") or ""
    if topical_backend() == TopicalBackend.NEMO:
        verdict = score_topical_nemo(request)
    else:
        verdict = score_topical(request)

    patch = verdict.to_state_patch()
    if verdict.decision == TopicalDecision.BLOCK:
        patch["status"] = RunStatus.REJECTED.value
        patch["refusal_message"] = (
            "This assistant only supports banking regulatory workflow and policy questions. "
            "Rephrase your request in that context."
        )
        patch["final_response"] = patch["refusal_message"]
    audit_decision = (
        "rewrite" if verdict.decision == TopicalDecision.STEER else verdict.decision.value
    )
    patch.update(_audit(verdict.policy_id, audit_decision, verdict.detail))
    return patch


def route_after_topical(state: dict[str, Any]) -> str:
    if state.get("topical_decision") == TopicalDecision.BLOCK.value:
        return "refuse"
    return "continue"
