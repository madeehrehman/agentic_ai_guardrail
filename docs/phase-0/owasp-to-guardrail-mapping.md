# OWASP LLM Top 10 → guardrail layers

Maps each **LLM01–LLM10 (2025)** item to the [guardrail taxonomy](./guardrail-taxonomy.md). No single layer is sufficient — **defense in depth**.

| OWASP | Primary guardrail layers | Secondary / supporting |
|-------|--------------------------|-------------------------|
| **LLM01** Prompt Injection | Input validation; retrieval rails; output filtering | Dialog rails; segregate untrusted content; human gate on privileged actions |
| **LLM02** Sensitive Information Disclosure | PII detect/redact (input & output); output validation | Access control on data sources; sanitization before training/logging |
| **LLM03** Supply Chain | (Mostly SDLC/MLOps — outside runtime graph) | Audit; version pinning; SBOM; vet third-party models/tools in agent registry |
| **LLM04** Data / Model Poisoning | Retrieval rails; ingest validation for RAG | MLOps monitoring; sandbox training pipelines |
| **LLM05** Improper Output Handling | Output sanitization; output validation | Treat model as untrusted user; ASVS encoding; no raw SQL/shell from LLM |
| **LLM06** Excessive Agency | Pre-tool rails; post-tool rails; scope/authority; human gate | Minimize tools; budget/rate caps; complete mediation in downstream APIs |
| **LLM07** System Prompt Leakage | Output filter (leak patterns); external authZ (not prompt) | Never store secrets in prompts; guardrails outside LLM |
| **LLM08** Vector / Embedding | Retrieval rails; access control on vector DB | Tenant isolation; ingest scanning |
| **LLM09** Misinformation | Output validation (groundedness); retrieval rails | Human review for high-stakes; citations |
| **LLM10** Unbounded Consumption | Budget/rate caps; loop/anomaly detection | Input size limits; gateway quotas; graceful degradation |

## Agentic emphasis (learning plan phases)

| Priority OWASP | Why | First implementation phase |
|----------------|-----|----------------------------|
| LLM01 | Direct + indirect injection | Phase 2 (input), Phase 3 (retrieval) |
| LLM06 | Tool misuse, autonomy | Phase 4 (tool rails), Phase 1 (HITL) |
| LLM07 | Prompt leakage ≠ security boundary | Phase 3 (output), external authZ |

## Decision contract (all layers)

Every rail should record in state/trace:

- **Decision:** allow | block | rewrite | escalate  
- **Policy id / reason** (for audit: “blocked by policy X at time T”)  
- **Evidence** (scores, matched rules) for Phase 6 evals  

## Gateway vs application (Phase 0 awareness)

| Layer type | Good for |
|------------|----------|
| **Gateway** | Baseline LLM01/02 filtering, LLM10 rate limits, org-wide logging |
| **In-graph (LangGraph)** | LLM06 tool policy, LLM01 retrieval segregation, blast-radius HITL, domain-specific rails |

Phase 7 ADR should justify placement per risk for your fleet.
