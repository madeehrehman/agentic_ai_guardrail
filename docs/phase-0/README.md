# Phase 0 — Threat model & taxonomy

Study materials for **Phase 0** of the [learning plan](../../guardrails-agentic-ai-langgraph-learning-plan.md). Work through these in order, then complete the [threat model template](./threat-model-template.md).

## Checkpoint (from the learning plan)

You are done when you can:

- Name all ten **OWASP LLM Top 10 (2025)** items from memory
- Explain **direct vs indirect** prompt injection
- Point at your own system’s single **highest blast-radius** action

## Reading order

| # | Document | Purpose |
|---|----------|---------|
| 1 | [Guardrail taxonomy](./guardrail-taxonomy.md) | Map of guardrail types (where checks live) |
| 2 | [OWASP LLM Top 10 (2025)](./owasp-llm-top-10-2025.md) | Primary literature — summaries + mitigations |
| 3 | [OWASP Agentic Top 10 (2026)](./owasp-agentic-top-10-2026.md) | Complementary list for autonomous agents |
| 4 | [OWASP → guardrail mapping](./owasp-to-guardrail-mapping.md) | Which layer addresses which risk |
| 5 | [Agent-specific threats](./agent-specific-threats.md) | Blast radius, loops, app vs gateway |
| 6 | [References](./references.md) | Official PDFs, sites, papers |
| 7 | [Threat model template](./threat-model-template.md) | **Build artifact** — fill in for your system |

## Worked example (banking regulatory)

| Document | Description |
|----------|-------------|
| [Banking regulatory workflow assistant](./threat-models/banking-regulatory-workflow-assistant.md) | Posture **B** (HITL on kinetic actions); RAG + GRC, email, external APIs; autonomy roadmap |

Use this as the reference threat model for Phases 1–4 implementations in this repo, or copy the template for a second system.

## Official sources (download / verify)

- **OWASP Top 10 for LLM Applications 2025** (CC BY-SA 4.0): https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/
- **PDF**: https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf
- **Per-risk pages**: https://genai.owasp.org/llmrisk/ (e.g. `llm01-prompt-injection`)
- **OWASP Top 10 for Agentic Applications 2026**: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

Local summaries in this folder are study aids derived from the official OWASP materials; always verify API names and guidance against current docs before implementation.
