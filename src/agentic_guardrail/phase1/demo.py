"""Interactive CLI demo for Phase 1 HITL (banking regulatory workflow assistant)."""

from __future__ import annotations

import json
import uuid
from typing import Any

from langgraph.types import Command

from agentic_guardrail.phase1.graph import compile_graph
from agentic_guardrail.phase1.models import HumanDecisionType


def _print_interrupt(interrupts: tuple[Any, ...]) -> dict[str, Any]:
    value = interrupts[0].value
    print("\n=== HUMAN APPROVAL REQUIRED (T0 kinetic) ===")
    print(json.dumps(value, indent=2, default=str))
    print("\nOptions: approve | reject | edit | timeout")
    return value


def _prompt_decision() -> dict[str, Any]:
    choice = input("Decision [approve/reject/edit/timeout]: ").strip().lower()
    reviewer = input("Reviewer id: ").strip() or "compliance.reviewer@bank"

    if choice == "timeout":
        return {"type": "timeout", "reviewer_id": "system", "comment": "demo timeout"}

    if choice == "reject":
        return {
            "type": "reject",
            "reviewer_id": reviewer,
            "comment": input("Comment (optional): ").strip(),
        }

    if choice == "edit":
        print("Edit mode: adjust GRC comment or email 'to' (comma-separated).")
        base = {
            "type": "edit",
            "reviewer_id": reviewer,
            "comment": input("Comment: ").strip(),
        }
        grc_comment = input("New GRC close comment (blank=keep): ").strip()
        if grc_comment:
            base["edited_grc"] = {
                "finding_id": "FIN-2024-017",
                "comment": grc_comment,
                "expected_status": "open",
            }
        new_to = input("Email to override (blank=keep): ").strip()
        if new_to:
            base["edited_email"] = {
                "to": [a.strip() for a in new_to.split(",")],
                "subject": "Regulatory workflow notification",
                "body": "Edited by reviewer.",
                "internal_only": True,
            }
        return base

    return {
        "type": "approve",
        "reviewer_id": reviewer,
        "comment": input("Comment (optional): ").strip(),
    }


def run_session(
    user_request: str,
    *,
    user_id: str = "compliance.officer@bank",
    thread_id: str | None = None,
    auto_approve: bool = False,
) -> dict[str, Any]:
    graph = compile_graph()
    tid = thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": tid}}

    initial = {
        "user_id": user_id,
        "entity_id": "entity-uk-bank-01",
        "user_request": user_request,
        "loop_count": 0,
        "max_loops": 8,
        "status": "running",
        "pending_proposal": None,
        "human_decision": None,
        "execution_result": None,
        "audit_log": [],
    }

    result = graph.invoke(initial, config=config)

    while True:
        snap = graph.get_state(config)
        if not snap.interrupts:
            break
        _print_interrupt(snap.interrupts)
        resume = (
            {"type": "approve", "reviewer_id": "demo.auto", "comment": "auto"}
            if auto_approve
            else _prompt_decision()
        )
        result = graph.invoke(Command(resume=resume), config=config)

    print("\n=== FINAL STATE ===")
    print(json.dumps(result, indent=2, default=str))
    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Phase 1 regulatory HITL demo")
    parser.add_argument(
        "request",
        nargs="?",
        default="close finding FIN-2024-017 after remediation",
        help="User request text",
    )
    parser.add_argument("--auto-approve", action="store_true", help="Skip prompt")
    args = parser.parse_args()
    run_session(args.request, auto_approve=args.auto_approve)


if __name__ == "__main__":
    main()
