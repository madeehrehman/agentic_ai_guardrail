# Agent-specific threats (beyond chatbot safety)

Chatbot failures produce bad **text**. Agent failures produce bad **actions** — wrong deletes, trades, emails, or unbounded API calls. Phase 0 is about naming those behaviors before writing guard code.

## Core concepts

### Instruction hijacking

Attacker (or poisoned content) overrides the agent’s intended objective. Overlaps **LLM01** (direct/indirect) and **ASI01** (goal hijack). Mitigation: input + retrieval rails, least privilege on tools, external policy — not “stronger system prompt” alone.

### Tool misuse

Model selects a valid tool with wrong parameters, wrong scope, or at the wrong time. Overlaps **LLM06** and **ASI02**. Mitigation: pre-execution schema/allowlist, post-execution inspection, human gate on destructive tools.

### Runaway loops

Agent repeats tool/LLM calls until budget or service limits break. Overlaps **LLM10** and operational **ASI08**. Mitigation: recursion limits, per-run action counters, loop detection, timeouts.

### Blast radius

The **worst irreversible or high-impact action** the agent can take **without** human approval, if manipulated or hallucinating.

**Phase 0 exercise:** For each tool, ask:

1. What is the worst outcome if this runs with attacker-chosen args?  
2. Is it reversible?  
3. Does it need HITL, stricter pre-rail, or removal from the allowlist?

The single highest blast-radius action is what you will gate in **Phase 1**.

## Failure modes checklist

| Mode | Description | Typical OWASP / ASI |
|------|-------------|---------------------|
| Direct injection | Malicious user prompt | LLM01, ASI01 |
| Indirect injection | Poisoned RAG, email, webpage, tool output | LLM01, LLM08, ASI06 |
| Excessive functionality | Tool can do more than required | LLM06, ASI02 |
| Excessive permissions | Service account too powerful | LLM06, ASI03 |
| Excessive autonomy | No confirmation on destructive ops | LLM06, ASI09 |
| Second-order injection | Model output → SQL/shell/HTML | LLM05, ASI05 |
| Stale state after HITL | World changed while human reviewed | Design (Phase 1) |
| Multi-agent compromise | Malicious peer influences planner | ASI07, ASI10 |

## Application vs gateway guardrails

| Concern | Application-level (LangGraph) | Gateway / platform |
|---------|------------------------------|---------------------|
| Tool allowlist per agent | Strong fit | Possible but coarse |
| Human interrupt before trade/delete | Strong fit | Rare at gateway |
| Org-wide PII scanner on all LLM calls | Duplicative if both | Strong fit |
| Per-tenant rate limits | Can complement | Strong fit |

**Phase 0 takeaway:** Know the fork exists; Phase 7 chooses deliberately. Start with in-graph rails for **behavior and authority** on your capstone agent.

## Chatbot vs agent (one table)

| Dimension | Chatbot | Agent |
|-----------|---------|-------|
| Primary failure | Wrong answer | Wrong **action** |
| Untrusted input | User message | User + RAG + **tool results** |
| Safety control | Output filter | Tool rails + HITL + budgets |
| OWASP emphasis | LLM01, 02, 05, 09 | LLM01, **06**, 07, 08, 10 + ASI* |
