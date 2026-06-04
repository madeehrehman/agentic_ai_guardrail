# Threat model template (Phase 0 build)

**Instructions:** Copy this file or fill it in place. Target **one page** when printed. No code required — this artifact drives Phases 1–7.

Replace bracketed placeholders. Delete optional sections if not applicable.

---

## 1. System overview

| Field | Your answer |
|-------|-------------|
| **System name** | [e.g. Legal RAG assistant / Trading research agent] |
| **Purpose** | [What business outcome does it serve?] |
| **Architecture sketch** | [User → LangGraph → LLM → tools/RAG → downstream systems] |
| **Autonomy level** | [Suggest-only / tool calls with approval / fully autonomous steps] |

## 2. Assets and trust boundaries

| Asset | Sensitivity | Who must not access? |
|-------|-------------|----------------------|
| [User documents / market data / PII] | | |
| [API keys / DB credentials] | | |
| [System prompts / policy config] | | |
| [Model outputs / audit logs] | | |

**Trust boundaries:** [e.g. Internet user → app → internal DB → third-party LLM API]

## 3. Tools and blast radius

List every tool or integration the agent (or sub-agents) can invoke.

| Tool / integration | Intended use | Worst irreversible or high-impact action | Reversible? | Blast radius (L/M/H) |
|--------------------|--------------|------------------------------------------|-------------|----------------------|
| [read_email] | | | | |
| [send_email] | | | | |
| [sql_query] | | | | |
| [place_order] | | | | |
| [delete_resource] | | | | |

**Single highest blast-radius action:** [One sentence — this is your Phase 1 HITL candidate]

## 4. OWASP LLM Top 10 mapping

For each row, note *how* it could manifest in **your** system (one line) and planned guardrail layer (from [taxonomy](./guardrail-taxonomy.md)).

| ID | Applicable? (Y/N) | How it manifests here | Planned guardrail layer |
|----|-------------------|------------------------|-------------------------|
| LLM01 Prompt Injection | | | |
| LLM02 Sensitive Info Disclosure | | | |
| LLM03 Supply Chain | | | |
| LLM04 Data / Model Poisoning | | | |
| LLM05 Improper Output Handling | | | |
| LLM06 Excessive Agency | | | |
| LLM07 System Prompt Leakage | | | |
| LLM08 Vector / Embedding | | | |
| LLM09 Misinformation | | | |
| LLM10 Unbounded Consumption | | | |

## 5. Agentic risks (optional, if multi-step / memory / multi-agent)

| ID | Applicable? | Notes |
|----|-------------|-------|
| ASI01 Goal Hijack | | |
| ASI02 Tool Misuse | | |
| ASI03 Identity / Privilege | | |
| ASI06 Memory Poisoning | | |
| ASI08 Cascading Failures | | |
| ASI10 Rogue Agents | | |

## 6. Direct vs indirect injection (your system)

| Attack path | Example in your system | Current control | Gap |
|-------------|------------------------|-----------------|-----|
| **Direct** | [Malicious user prompt] | | |
| **Indirect** | [Poisoned doc in RAG / malicious email / tool JSON] | | |

## 7. Priority mitigations (Phase 0 → 1 handoff)

| Priority | Risk | Mitigation | Phase |
|----------|------|------------|-------|
| P0 | [Highest blast radius] | Human gate + checkpointer | 1 |
| P1 | [LLM01 indirect via RAG] | Retrieval rail | 3 |
| P2 | [LLM06 tool scope] | Pre/post tool wrapper | 4 |

## 8. Sign-off (checkpoint)

- [ ] I can name all ten OWASP LLM items from memory  
- [ ] I can explain direct vs indirect injection with examples from this system  
- [ ] I have identified the single highest blast-radius action  

**Author / date:** [Name, date]
