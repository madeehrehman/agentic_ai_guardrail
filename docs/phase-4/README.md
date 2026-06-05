# Phase 4 — Tool-call & agency guardrails

**Goal:** Govern what the agent is allowed to do — pre/post execution validation, least privilege, budgets, loop detection, HITL for destructive tools.

**Checkpoint:** Out-of-scope tool blocked pre-execution; runaway loop/budget halted; destructive kinetic action routed through human approval — all logged.

## Flow (kinetic path)

```text
… → plan → pre_authorize (scope + HITL escalate)
         ├─ block → fail → END
         └─ escalate → human_gate → validate → authorize_tool (budget + loop)
                ├─ block → END
                └─ allow → execute (guarded_tool + post-exec scan) → END
```

Phase 3 retrieval rail still runs before `plan` on all requests.

## Components

| Module | Role |
|--------|------|
| `phase4/policy.py` | Allowlist, entity/finding scope, budget, HITL requirement |
| `phase4/guarded_tool.py` | `guarded_tool()` — execute + post-result injection scan |
| `phase4/loop_detect.py` | Repeated / oscillating tool fingerprints |
| `phase4/nodes.py` | `pre_authorize`, `authorize_tool`, `execute_guarded` |

## Policies

| Policy id | When |
|-----------|------|
| `tool.pre.allowlist` | Action not in agent capability set |
| `tool.pre.scope` | Wrong entity, finding, or email recipient |
| `tool.pre.hitl_required` | Destructive tool → Phase 1 human gate |
| `tool.budget.cost` | Per-run tool budget exceeded |
| `tool.budget.actions` | Max kinetic actions per run |
| `tool.loop.anomaly` | Repeated identical tool signature |
| `tool.post.injection` | Poisoned content in tool result |

Default budgets: `max_kinetic_actions=1`, `max_tool_budget=15` (GRC close costs 10, email costs 3).

## Run

```powershell
python -m pytest tests/test_phase4_tool_guards.py tests/ -q

# Happy path (pre-auth → HITL → guarded execute)
python -m agentic_guardrail.phase2.demo "close finding FIN-2024-017" --auto-approve

# Budget block (set in test; demo uses defaults)
```

## Phase 5 handoff

Phase 5 integrates Guardrails AI (`GUARDRAIL_OUTPUT_BACKEND`) and topical rail (`GUARDRAIL_TOPICAL_BACKEND`); keep `guarded_tool` as the agency layer.
