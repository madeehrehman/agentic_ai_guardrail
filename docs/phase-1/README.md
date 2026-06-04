# Phase 1 — LangGraph control primitives (HITL)

**Goal:** Human approval gate before the highest blast-radius kinetic actions from the [banking regulatory threat model](../phase-0/threat-models/banking-regulatory-workflow-assistant.md).

**Checkpoint:** Graph pauses on risky action, persists with checkpointer, accepts approve/edit/reject/timeout, re-validates world state after resume, executes idempotently.

## What was built

| Component | Path |
|-----------|------|
| Typed proposals & decisions | `src/agentic_guardrail/phase1/models.py` |
| Mock GRC / email world | `src/agentic_guardrail/phase1/backends.py` |
| Graph nodes + `interrupt()` | `src/agentic_guardrail/phase1/nodes.py` |
| StateGraph wiring | `src/agentic_guardrail/phase1/graph.py` |
| CLI demo | `src/agentic_guardrail/phase1/demo.py` |
| Tests | `tests/test_phase1_hitl.py` |

## Flow

```text
START → receive_request (loop cap)
      → plan (stub: "close finding" | "email")
      → human_gate → interrupt(proposal snapshot)
      → [resume Command] → route: approve/edit → validate (stale check) → execute
                        → reject / timeout → END
```

### Design choices (aligned with learning plan)

1. **State as control surface** — Pydantic models for proposals/decisions; LangGraph `State` TypedDict with append-only `audit_log`.
2. **Bounded loops** — `max_loops` in `receive_request`.
3. **Checkpointer** — **SQLite by default** (`.data/checkpoints.db`); `MemorySaver` for unit tests. Survives process restart on same `thread_id`.
4. **`interrupt()` inside `human_gate`** — proposal snapshot before pause; no writes before interrupt.
5. **Idempotency** — execution deduped by `proposal_id`; validate/execute only after resume.
6. **Stale-state check** — GRC finding `version`/`status` re-read after resume (simulates another user closing the finding during review).
7. **T0 actions** — `grc_close_finding`, `email_send` (highest blast-radius from threat model).

## Run locally

```powershell
cd c:\Users\madaz\workspace\code\git\agentic_ai_guardrail
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest tests/test_phase1_hitl.py -q
```

### Interactive demo

```powershell
# GRC close (will prompt for approve/reject/edit/timeout)
.\.venv\Scripts\python.exe -m agentic_guardrail.phase1.demo "close finding FIN-2024-017"

# Email send
.\.venv\Scripts\python.exe -m agentic_guardrail.phase1.demo "email notify compliance"

# Non-interactive (CI-style)
.\.venv\Scripts\python.exe -m agentic_guardrail.phase1.demo "close finding FIN-2024-017" --auto-approve
```

### Checkpointer (SQLite)

```powershell
# Default: persists under .data/checkpoints.db
python -m agentic_guardrail.phase1.demo "close finding FIN-2024-017"

# In-memory only (like tests)
$env:GUARDRAIL_CHECKPOINT = "memory"
```

```python
from agentic_guardrail.checkpointing import get_checkpointer
# get_checkpointer(backend="sqlite")  # default
# get_checkpointer(backend="memory")  # tests / ephemeral
```

### Programmatic resume

```python
from langgraph.types import Command
from agentic_guardrail.phase1.graph import compile_graph

graph = compile_graph()  # SQLite unless GUARDRAIL_CHECKPOINT=memory
config = {"configurable": {"thread_id": "case-123"}}
graph.invoke({...initial state...}, config=config)

# Human reviews interrupt payload from graph.get_state(config).interrupts
graph.invoke(
    Command(resume={"type": "approve", "reviewer_id": "compliance.lead"}),
    config=config,
)
```

## Audit events

Each node appends `{policy_id, decision, detail}` to `audit_log` using the guardrail decision vocabulary: `allow | block | rewrite | escalate`.

## Phase 2+ handoff

| Next phase | Hook |
|------------|------|
| Phase 2 | Done — `workflow/graph.py` runs `input_guard` before `receive_request` |
| Phase 3 | Add RAG + `retrieval_rail` before planner context |
| Phase 4 | Replace raw `execute_kinetic` with `guarded_tool` wrapper + budgets |

## You're done when

- [x] Run demo and complete approve + reject paths manually  
- [x] Run `pytest` green — `tests/test_phase1_hitl.py` + `tests/test_phase1_sqlite_checkpoint.py`  
- [x] Read `human_approval_gate` and explain idempotency before `interrupt()`  
- [x] Stale path — covered by `test_stale_finding_blocked_after_resume`  

**Phase 1 checkpoint: complete.**
