# Phase 0 — References and literature

Primary sources for threat modeling and taxonomy. Prefer these over third-party summaries when details matter.

## OWASP GenAI (authoritative)

| Resource | URL |
|----------|-----|
| OWASP GenAI Security Project | https://genai.owasp.org/ |
| **Top 10 for LLM Applications 2025** (landing) | https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/ |
| **LLM Top 10 PDF (v2025)** | https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf |
| Per-risk pages (LLM01–LLM10) | https://genai.owasp.org/llmrisk/ |
| GitHub project | https://github.com/OWASP/www-project-top-10-for-large-language-model-applications |
| Release tag 2025 | https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/releases/tag/2024 |
| **Top 10 for Agentic Applications 2026** | https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ |

**License:** OWASP LLM Top 10 v2025 is [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Summaries in this repo attribute OWASP and do not replace the official document.

## Threat modeling (cited in OWASP LLM01)

| Resource | URL |
|----------|-----|
| Threat Modeling LLM Applications (AI Village) | Referenced in OWASP LLM01 reference list — search OWASP PDF § LLM01 for current link |
| Reducing Impact of Prompt Injection Through Design (Kudelski) | OWASP LLM01 references |
| NIST Adversarial ML Taxonomy | https://csrc.nist.gov/projects/adversarial-machine-learning |

## MITRE ATLAS (mapped in OWASP entries)

| Technique | ID |
|-----------|-----|
| LLM Prompt Injection: Direct | AML.T0051.000 |
| LLM Prompt Injection: Indirect | AML.T0051.001 |
| LLM Jailbreak Injection: Direct | AML.T0054 |
| ML Supply Chain Compromise | MITRE ATLAS (see LLM03) |
| Uncontrolled Resource Consumption | CWE-400 (LLM10) |

Atlas portal: https://atlas.mitre.org/

## Seminal papers / posts (from OWASP bibliographies)

| Topic | Reference |
|-------|-----------|
| Indirect prompt injection | Greshake et al., *Not what you've signed up for* — [arXiv](https://arxiv.org/abs/2302.12173) |
| Inject My PDF / resume attacks | Kai Greshake — inject-my-pdf |
| Excessive agency / confused deputy | Embrace the Red; Twilio *Rogue Agents* (OWASP LLM06 refs) |
| System prompt leakage | OWASP LLM07; community leak corpora (see official refs) |
| Poisoned models | PoisonGPT (Mithril Security); OWASP LLM03/04 scenarios |
| Sleeper agents | Anthropic arXiv:2401.05566 (OWASP LLM04) |

## Related OWASP / security standards

| Standard | Use in guardrails work |
|----------|------------------------|
| OWASP ASVS | Input/output validation (LLM05, LLM06) |
| OWASP CycloneDX / BOM | Supply chain, AI-BOM (LLM03) |
| NIST AI RMF | Governance framing (LLM04 related frameworks) |

## Production safety layers (learning plan)

Map each OWASP item to concrete guardrail layers using [owasp-to-guardrail-mapping.md](./owasp-to-guardrail-mapping.md). As you adopt frameworks in Phase 5, add vendor docs here (NeMo, Guardrails AI, LLM Guard) — verify versions at implementation time.

## How to add the PDF to your machine (optional)

The project does **not** vendor the 8MB PDF in git. Download locally:

```powershell
Invoke-WebRequest -Uri "https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf" -OutFile "docs/phase-0/literature/OWASP-Top-10-for-LLMs-v2025.pdf"
```

Add `docs/phase-0/literature/*.pdf` to `.gitignore` if you keep local copies only.
