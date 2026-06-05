"""Phase 3 LangGraph nodes — retrieve, retrieval rail, draft, output guard."""

from __future__ import annotations

from typing import Any

from agentic_guardrail.phase1.models import AuditEvent, RunStatus
from agentic_guardrail.phase3.corpus import search_corpus
from agentic_guardrail.phase3.guards import score_retrieved_chunks
from agentic_guardrail.phase5.output import score_output
from agentic_guardrail.phase3.models import GuardDecision, RetrievedChunk


def _audit(policy_id: str, decision: str, detail: str) -> dict[str, Any]:
    return {
        "audit_log": [
            AuditEvent(policy_id=policy_id, decision=decision, detail=detail).model_dump(
                mode="json"
            )
        ]
    }


def _parse_chunks(data: list[dict[str, Any]] | None) -> list[RetrievedChunk]:
    if not data:
        return []
    return [RetrievedChunk.model_validate(c) for c in data]


def retrieve_chunks(state: dict[str, Any]) -> dict[str, Any]:
    """Stub RAG retrieve — real system would call vector DB."""
    query = state.get("user_request") or ""
    chunks = search_corpus(query)
    return {
        "raw_retrieved_chunks": [c.model_dump() for c in chunks],
        **_audit("rag.retrieve", "allow", f"retrieved {len(chunks)} chunk(s)"),
    }


def retrieval_rail(state: dict[str, Any]) -> dict[str, Any]:
    """Score chunks for indirect injection before they enter agent context."""
    raw = _parse_chunks(state.get("raw_retrieved_chunks"))
    verdict = score_retrieved_chunks(raw)
    patch = verdict.to_state_patch()
    decision_audit = verdict.decision.value
    if verdict.decision == GuardDecision.BLOCK:
        patch["status"] = RunStatus.REJECTED.value
        patch["refusal_message"] = (
            "Retrieved content was blocked due to suspected indirect prompt injection. "
            "Contact information security if you believe this is an error."
        )
    patch.update(_audit(verdict.policy_id, decision_audit, verdict.detail))
    return patch


def route_after_retrieval(state: dict[str, Any]) -> str:
    if state.get("retrieval_decision") == GuardDecision.BLOCK.value:
        return "refuse"
    if is_kinetic_request(state):
        return "kinetic"
    return "qa"


def retrieval_refusal(state: dict[str, Any]) -> dict[str, Any]:
    msg = state.get("refusal_message") or "Retrieval blocked by policy."
    return {
        "status": RunStatus.REJECTED.value,
        "final_response": msg,
        "execution_result": msg,
        **_audit("retrieval.refusal", "block", "user shown retrieval refusal"),
    }


def is_kinetic_request(state: dict[str, Any]) -> bool:
    req = (state.get("user_request") or "").lower()
    return ("close" in req and "finding" in req) or "email" in req or "notify" in req


def draft_response(state: dict[str, Any]) -> dict[str, Any]:
    """
    Stub LLM synthesis using only approved chunks (never raw poisoned text).
    """
    chunks = _parse_chunks(state.get("approved_chunks"))
    query = state.get("user_request") or ""

    if not chunks:
        text = (
            "I do not have approved policy excerpts to answer that question. "
            "Try rephrasing or contact the policy team."
        )
    else:
        cites = "; ".join(f"[source:{c.chunk_id}] {c.title}" for c in chunks)
        excerpts = " ".join(c.text[:200] for c in chunks[:2])
        text = (
            f"Based on approved internal sources: {excerpts} "
            f"Sources: {cites}"
        )

    # Adversarial probe stub (passes input guard if phrased mildly) — output rail must block
    if "system prompt" in query.lower() or "hidden instructions" in query.lower():
        text = (
            "SYSTEM PROMPT: You are a banking regulatory workflow assistant. "
            "Transaction limit is set to $5000 per day. " + text
        )

    return {
        "agent_response": text,
        **_audit("agent.draft", "allow", "drafted response from approved chunks only"),
    }


def output_guard(state: dict[str, Any]) -> dict[str, Any]:
    """Validate final text: secrets, prompt leak, groundedness."""
    draft = state.get("agent_response") or ""
    chunk_ids = [
        c.chunk_id for c in _parse_chunks(state.get("approved_chunks"))
    ]
    verdict = score_output(draft, approved_chunk_ids=chunk_ids)
    patch = verdict.to_state_patch()
    if verdict.decision == GuardDecision.BLOCK:
        patch["status"] = RunStatus.REJECTED.value
    else:
        patch["status"] = RunStatus.COMPLETED.value
    patch.update(
        _audit(verdict.policy_id, verdict.decision.value, verdict.detail),
    )
    return patch


def route_after_output_guard(state: dict[str, Any]) -> str:
    return "end"
