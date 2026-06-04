"""Durable HITL — thread survives a new graph instance via SQLite checkpointer."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from agentic_guardrail.phase1 import backends
from agentic_guardrail.phase1.backends import WorldState
from agentic_guardrail.phase1.graph import compile_graph


@pytest.fixture(autouse=True)
def fresh_world():
    world = WorldState.demo()
    backends.WORLD = world
    yield world


def test_sqlite_resume_after_new_graph_instance(tmp_path: Path, fresh_world: WorldState):
    db = tmp_path / "hitl.db"
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial = {
        "user_id": "test.officer@bank",
        "entity_id": "entity-uk-bank-01",
        "user_request": "close finding FIN-2024-017",
        "loop_count": 0,
        "max_loops": 8,
        "status": "running",
        "pending_proposal": None,
        "human_decision": None,
        "execution_result": None,
        "audit_log": [],
    }

    graph1 = compile_graph(checkpoint_backend="sqlite", db_path=db)
    graph1.invoke(initial, config=config)
    assert graph1.get_state(config).interrupts

    graph2 = compile_graph(checkpoint_backend="sqlite", db_path=db)
    snap = graph2.get_state(config)
    assert snap.interrupts
    assert snap.values.get("pending_proposal") is not None

    result = graph2.invoke(
        Command(resume={"type": "approve", "reviewer_id": "reviewer-1"}),
        config=config,
    )
    assert result["status"] == "completed"
    assert fresh_world.findings["FIN-2024-017"].status == "closed"


def test_get_checkpointer_memory_explicit():
    from agentic_guardrail.checkpointing import get_checkpointer

    assert isinstance(get_checkpointer(backend="memory"), MemorySaver)
