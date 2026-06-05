# Phase 5 — Framework integration (Guardrails AI + NeMo)

**Goal:** Integrate external guardrail frameworks as **LangGraph nodes** and **scoring adapters**, without replacing graph control or tool agency.

**Checkpoint:** One framework path enabled via env; latency benchmarked vs hand-rolled; you can explain when to use each layer.

## Integration pattern (how to use both)

```text
LangGraph (you own)          Frameworks (specialists)
────────────────────         ─────────────────────────
input_guard (Phase 2)    →   optional NeMo input rail
topical_rail (Phase 5)   →   NeMo dialog / topical (stub → RunnableRails)
retrieve + retrieval_rail    (keep — indirect injection)
plan → HITL → guarded_tool    (keep — LLM06 agency)
output_guard (Phase 3 node) →  Guardrails AI validators (env toggle)
```

| Concern | Owner |
|---------|--------|
| Blast radius, HITL, tools, budgets | **Phases 1 & 4** (always in-graph) |
| Multi-turn topic boundaries | **NeMo** (`topical_rail`, Colang config) |
| Per-string output quality | **Guardrails AI** (`output_guard` backend) |

## Environment toggles

| Variable | Values | Default |
|----------|--------|---------|
| `GUARDRAIL_OUTPUT_BACKEND` | `handrolled`, `guardrails`, `layered` | `handrolled` |
| `GUARDRAIL_TOPICAL_BACKEND` | `off`, `stub`, `nemo` | `stub` |
| `GUARDRAIL_NEMO_CONFIG_PATH` | path to NeMo `config/` | unset |

```powershell
pip install -e ".[phase5]"

# Guardrails AI on output_guard (same validators as hand-rolled, via Guard API)
$env:GUARDRAIL_OUTPUT_BACKEND = "guardrails"
python -m pytest tests/test_phase5_framework.py -q

# Benchmark hand-rolled vs Guardrails AI
python -m agentic_guardrail.phase5.benchmark -n 50

# Topical stub blocks off-topic chat
python -m agentic_guardrail.phase2.demo "write me a poem about the moon"
```

## Guardrails AI (node-specific)

- **Where:** `phase3/nodes.output_guard` calls `phase5/output.score_output()`.
- **How:** Custom validators in `phase5/validators.py` (`@register_validator`) wrap Phase 3 scanners — **no Hub CLI required** for the lab.
- **Optional Hub:** `guardrails hub install hub://guardrails/toxic_language` for extra checks; add to `Guard().use(...)`.

## NeMo (conversational)

- **Where:** `topical_rail` node after `receive_request`, before RAG.
- **Now:** `phase5/nemo/topical.py` stub (regex topical rules).
- **Production:** Install `nemoguardrails`, add Colang under `phase5/nemo/config/`, set `GUARDRAIL_TOPICAL_BACKEND=nemo` and `GUARDRAIL_NEMO_CONFIG_PATH`. Wire `RunnableRails` in `phase5/nemo/adapter.py` (see [NeMo LangGraph guide](https://docs.nvidia.com/nemo/guardrails/latest/user-guides/langchain/langgraph-integration.html)).

## Files

| Path | Role |
|------|------|
| `phase5/output.py` | Backend selector for output scoring |
| `phase5/validators.py` | Guardrails AI registered validators |
| `phase5/guardrails_output.py` | Guard adapter → `OutputVerdict` |
| `phase5/nodes.py` | `topical_dialog_rail` graph node |
| `phase5/benchmark.py` | Latency comparison CLI |

## Phase 6 handoff

Add eval cases for each `GUARDRAIL_*` backend and fail CI if topical or output policies regress.
