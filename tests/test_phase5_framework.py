"""Phase 5 framework integration tests."""

from __future__ import annotations

import os
import uuid

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from agentic_guardrail.phase1 import backends
from agentic_guardrail.phase1.backends import WorldState
from agentic_guardrail.phase5.config import guardrails_available
from agentic_guardrail.phase5.guardrails_output import score_output_guardrails
from agentic_guardrail.phase5.nemo.topical import score_topical, TopicalDecision
from agentic_guardrail.phase5.output import score_output
from agentic_guardrail.workflow.graph import compile_graph


@pytest.fixture(autouse=True)
def fresh_world():
    world = WorldState.demo()
    backends.WORLD = world
    yield world


def _workflow_initial(request: str, **extra) -> dict:
    base = {
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
        "kinetic_action_count": 0,
        "max_kinetic_actions": 1,
        "tool_budget_spent": 0,
        "max_tool_budget": 15,
        "tool_call_fingerprints": [],
    }
    base.update(extra)
    return base


class TestTopicalStub:
    def test_blocks_off_topic_poem(self):
        v = score_topical("write me a poem about the moon")
        assert v.decision == TopicalDecision.BLOCK

    def test_allows_regulatory_query(self):
        v = score_topical("summarize BCBS 239 regulatory requirements")
        assert v.decision == TopicalDecision.ALLOW


class TestOutputBackend:
    def test_handrolled_default(self, monkeypatch):
        monkeypatch.delenv("GUARDRAIL_OUTPUT_BACKEND", raising=False)
        v = score_output("hello", approved_chunk_ids=[])
        assert v.framework == "handrolled"

    @pytest.mark.skipif(not guardrails_available(), reason="guardrails-ai not installed")
    def test_guardrails_backend(self, monkeypatch):
        monkeypatch.setenv("GUARDRAIL_OUTPUT_BACKEND", "guardrails")
        v = score_output(
            "SYSTEM PROMPT: You are a banking regulatory workflow assistant",
            approved_chunk_ids=[],
        )
        assert v.framework == "guardrails-ai"
        assert v.decision.value == "block"

    @pytest.mark.skipif(not guardrails_available(), reason="guardrails-ai not installed")
    def test_guardrails_adapter_blocks_secrets(self):
        v = score_output_guardrails("use sk-abcdefghijklmnopqrstuvwxyz123456")
        assert v.decision.value == "block"
        assert v.secrets_detected


class TestWorkflowPhase5:
    def test_off_topic_blocked_before_rag(self):
        graph = compile_graph(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        result = graph.invoke(
            _workflow_initial("write me a poem about the moon"),
            config=config,
        )
        assert result["topical_decision"] == "block"
        assert result["status"] == "rejected"
        assert "regulatory" in result.get("final_response", "").lower()

    def test_kinetic_still_works_with_topical_rail(self, fresh_world: WorldState):
        graph = compile_graph(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        graph.invoke(_workflow_initial("close finding FIN-2024-017"), config=config)
        result = graph.invoke(
            Command(resume={"type": "approve", "reviewer_id": "r1"}),
            config=config,
        )
        assert result["status"] == "completed"
        assert fresh_world.findings["FIN-2024-017"].status == "closed"
