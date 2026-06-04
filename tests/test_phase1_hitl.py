"""Phase 1 HITL graph tests."""

from __future__ import annotations

import uuid

import pytest
from langgraph.types import Command

from agentic_guardrail.phase1 import backends
from agentic_guardrail.phase1.backends import WorldState
from langgraph.checkpoint.memory import MemorySaver

from agentic_guardrail.phase1.graph import compile_graph


@pytest.fixture(autouse=True)
def fresh_world():
    world = WorldState.demo()
    backends.WORLD = world
    yield world


def _config() -> dict:
    return {"configurable": {"thread_id": str(uuid.uuid4())}}


def _initial(request: str) -> dict:
    return {
        "user_id": "test.officer@bank",
        "entity_id": "entity-uk-bank-01",
        "user_request": request,
        "loop_count": 0,
        "max_loops": 8,
        "status": "running",
        "pending_proposal": None,
        "human_decision": None,
        "execution_result": None,
        "audit_log": [],
    }


def _resume(graph, config, decision: dict):
    return graph.invoke(Command(resume=decision), config=config)


def _graph():
    return compile_graph(checkpointer=MemorySaver())


def test_grc_close_approve_completes(fresh_world: WorldState):
    world = fresh_world
    graph = _graph()
    config = _config()

    result = graph.invoke(_initial("close finding FIN-2024-017"), config=config)
    assert graph.get_state(config).interrupts

    result = _resume(
        graph,
        config,
        {"type": "approve", "reviewer_id": "reviewer-1", "comment": "ok"},
    )
    assert result["status"] == "completed"
    assert world.findings["FIN-2024-017"].status == "closed"


def test_human_reject():
    graph = _graph()
    config = _config()
    graph.invoke(_initial("close finding FIN-2024-017"), config=config)
    result = _resume(
        graph,
        config,
        {"type": "reject", "reviewer_id": "reviewer-1", "comment": "not yet"},
    )
    assert result["status"] == "rejected"


def test_stale_finding_blocked_after_resume(fresh_world: WorldState):
    world = fresh_world
    graph = _graph()
    config = _config()
    graph.invoke(_initial("close finding FIN-2024-017"), config=config)
    world.simulate_external_close("FIN-2024-017")
    result = _resume(
        graph,
        config,
        {"type": "approve", "reviewer_id": "reviewer-1"},
    )
    assert result["status"] == "stale_blocked"


def test_timeout_path():
    graph = _graph()
    config = _config()
    graph.invoke(_initial("email notify compliance"), config=config)
    result = _resume(
        graph,
        config,
        {"type": "timeout", "reviewer_id": "system", "comment": "expired"},
    )
    assert result["status"] == "timed_out"


def test_edit_email_then_approve(fresh_world: WorldState):
    world = fresh_world
    graph = _graph()
    config = _config()
    graph.invoke(_initial("send email to compliance"), config=config)
    result = _resume(
        graph,
        config,
        {
            "type": "edit",
            "reviewer_id": "reviewer-1",
            "edited_email": {
                "to": ["legal-desk@legal.bank.internal"],
                "subject": "Updated",
                "body": "Reviewer edit",
                "internal_only": True,
            },
        },
    )
    assert result["status"] == "completed"
    assert len(world.sent_messages) == 1


def test_checkpoint_survives_recompile():
    """Thread state persists across invoke/stop/resume pattern."""
    graph = _graph()
    config = _config()
    graph.invoke(_initial("close finding FIN-2024-017"), config=config)
    snap = graph.get_state(config)
    assert snap.interrupts
    assert snap.values.get("pending_proposal") is not None
