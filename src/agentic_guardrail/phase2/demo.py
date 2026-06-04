"""CLI demo — Phase 2 input guard + Phase 1 kinetic HITL."""

from __future__ import annotations

import argparse
import json

from agentic_guardrail.phase1.demo import run_session as _run_phase1


def main() -> None:
    parser = argparse.ArgumentParser(description="Regulatory workflow demo (Phase 1+2)")
    parser.add_argument("request", nargs="?", default="close finding FIN-2024-017")
    parser.add_argument("--auto-approve", action="store_true")
    parser.add_argument(
        "--phase1-only",
        action="store_true",
        help="Skip input guard (Phase 1 graph only)",
    )
    args = parser.parse_args()

    if args.phase1_only:
        _run_phase1(args.request, auto_approve=args.auto_approve)
        return

    import uuid

    from langgraph.types import Command

    from agentic_guardrail.phase1.demo import _prompt_decision
    from agentic_guardrail.workflow.graph import compile_graph

    graph = compile_graph()
    tid = str(uuid.uuid4())
    config = {"configurable": {"thread_id": tid}}
    initial = {
        "user_id": "compliance.officer@bank",
        "entity_id": "entity-uk-bank-01",
        "user_request": args.request,
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
        intr = snap.interrupts[0].value
        if intr.get("policy_id", "").startswith("input."):
            print("\n=== INPUT ESCALATION REVIEW ===")
        else:
            print("\n=== KINETIC ACTION APPROVAL (T0) ===")
        print(json.dumps(intr, indent=2, default=str))
        resume = (
            {"type": "approve", "reviewer_id": "demo.auto"}
            if args.auto_approve
            else _prompt_decision()
        )
        result = graph.invoke(Command(resume=resume), config=config)

    print("\n=== FINAL STATE ===")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
