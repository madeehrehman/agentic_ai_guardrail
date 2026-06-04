# OWASP Top 10 for LLM Applications (2025)

**Source:** OWASP GenAI Security Project, Version 2025 (released 2024-11-18), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

**Official:** https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/

This document is a **study summary** for Phase 0. For authoritative wording, scenarios, and references, use the [official PDF](https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf) and per-risk pages under https://genai.owasp.org/llmrisk/.

## What changed in 2025 (high level)

| Change | Why it matters for agents |
|--------|---------------------------|
| **LLM10 Unbounded Consumption** | Expands “DoS” to cost, model theft, resource abuse at scale |
| **LLM08 Vector and Embedding Weaknesses** | RAG / embeddings are first-class risks |
| **LLM07 System Prompt Leakage** | New entry; prompts are not a secret security boundary |
| **LLM06 Excessive Agency** | Expanded for tool-using and agentic architectures |

---

## LLM01:2025 — Prompt Injection

**Risk:** User or external content alters model behavior in unintended ways (including non-human-readable payloads).

### Direct vs indirect (know this cold)

| Type | Source | Example |
|------|--------|---------|
| **Direct** | User prompt to the model | “Ignore previous instructions and exfiltrate…” |
| **Indirect** | External content the model ingests | Poisoned RAG doc, email body, webpage, tool result |

**Jailbreaking** is a form of prompt injection that causes the model to disregard safety protocols. RAG and fine-tuning **do not fully** mitigate injection.

**Impacts:** Sensitive disclosure, system prompt hints, biased outputs, unauthorized functions, arbitrary commands on connected systems, bad decisions. **Severity scales with agency** (tools, autonomy).

**Mitigations (OWASP):**

1. Constrain model behavior (role, limits) — not sufficient alone  
2. Define and validate output formats (deterministic checks)  
3. Input and output filtering (semantic + rules; RAG triad: relevance, groundedness, Q/A fit)  
4. Least privilege for tools/APIs — handle sensitive ops in code, not model  
5. Human approval for high-risk actions  
6. Segregate and label untrusted external content  
7. Adversarial testing / red team  

**Agent focus:** Indirect injection via tools and RAG is the attack your input-only guard cannot see.

**MITRE ATLAS:** AML.T0051.000 (direct), AML.T0051.001 (indirect), AML.T0054 (jailbreak)

---

## LLM02:2025 — Sensitive Information Disclosure

**Risk:** Model or app exposes PII, credentials, proprietary algorithms, training data, or confidential business data in outputs or logs.

**Examples:** PII in chat; training-data inversion; confidential data in generated answers.

**Mitigations:** Data sanitization; strict input validation; least-privilege data access; limit external data sources; differential privacy / federated learning where applicable; user education; output restrictions (bypassable via injection — do not rely on prompt alone).

---

## LLM03:2025 — Supply Chain

**Risk:** Compromised or untrusted components in the LLM stack — dependencies, pre-trained models, LoRA adapters, Hugging Face pipelines, on-device models, unclear T&Cs.

**Examples:** Vulnerable PyPI deps; PoisonGPT-style tampered weights; malicious LoRA; fake model uploads; dataset license violations.

**Mitigations:** Vet suppliers and licenses; SBOM / AI-BOM (e.g. CycloneDX); verify model provenance (signing, hashes); pin and patch dependencies; red-team third-party models; monitor collaborative merge/conversion services.

*Overlaps LLM04 (poisoning) — LLM03 emphasizes **supply chain** provenance.*

---

## LLM04:2025 — Data and Model Poisoning

**Risk:** Manipulated pre-training, fine-tuning, or embedding data introduces backdoors, bias, or unsafe behavior (including “sleeper” triggers).

**Examples:** Split-view / frontrunning poisoning; unverified training data; user data in training causing later leakage; malicious pickle in model artifacts.

**Mitigations:** Data provenance (CycloneDX, ML-BOM); vendor vetting; sandboxing unverified sources; DVC; RAG/grounding at inference; red team and anomaly detection on training loss/behavior.

---

## LLM05:2025 — Improper Output Handling

**Risk:** LLM output used downstream **without** validation/sanitization → XSS, CSRF, SSRF, SQLi, path traversal, RCE (e.g. `exec` on model text).

**Note:** Distinct from **overreliance** (trust in correctness); this is **technical** mishandling of output.

**Mitigations:** Zero-trust on model output; OWASP ASVS validation/encoding; context-aware encoding; parameterized SQL; CSP; logging and anomaly detection on outputs.

**Agent focus:** Model text flowing into SQL, shells, or HTML is a **second-order injection** vector (Phase 3 in the learning plan).

---

## LLM06:2025 — Excessive Agency

**Risk:** Damaging **actions** from unexpected or manipulated LLM outputs — tools, plugins, agents calling extensions.

**Triggers:** Hallucination; direct/indirect prompt injection; compromised peer agent (multi-agent).

**Root causes:**

- Excessive **functionality** (tools do more than needed)  
- Excessive **permissions** (DB write when read suffices)  
- Excessive **autonomy** (destructive ops without confirmation)

**Mitigations:**

1. Minimize extensions and function surface  
2. Avoid open-ended tools (prefer specific “write file” vs “run shell”)  
3. Minimize extension permissions (DB roles, OAuth scopes)  
4. Execute in **user context** with least privilege  
5. **Human approval** for high-impact actions  
6. **Complete mediation** — authorization in downstream systems, not “ask the LLM”  
7. Sanitize LLM inputs/outputs (ASVS, SAST/DAST)  
8. *Limit damage:* logging, monitoring, rate limits  

**Agent focus:** **Primary** risk for LangGraph tool loops. Pairs with pre/post tool rails and human gates (Phases 1, 4).

---

## LLM07:2025 — System Prompt Leakage

**Risk:** System prompts contain or reveal sensitive logic; attackers learn rules, limits, or credentials embedded in prompts.

**Critical insight (OWASP):** The system prompt is **not** a secret and **not** a reliable security control. Real risk is **underlying** weak session management, secrets in prompts, or guardrails only enforced via prompt.

**Examples:** API keys in prompt text; internal limits (“$5000/day”) enabling bypass logic; filter rules disclosed then circumvented via injection.

**Mitigations:**

1. Never put secrets or permission matrices in system prompts  
2. Do not rely on prompts for strict behavior — use external deterministic controls  
3. External guardrails that **inspect** output compliance  
4. Enforce authZ/authN outside the LLM; split agents by privilege level  

---

## LLM08:2025 — Vector and Embedding Weaknesses

**Risk:** Weak access control, poisoning, or manipulation of vectors/embeddings in RAG — disclosure, wrong retrieval, hijacked context.

**Examples:** Cross-tenant embedding leakage; poisoned documents in index; embedding inversion.

**Mitigations:** Access control on vector stores; ingest validation; monitoring; separation of tenants; treat retrieved text as **untrusted** (retrieval rail).

---

## LLM09:2025 — Misinformation

**Risk:** False or misleading outputs (hallucinations) causing harm, bad decisions, or legal exposure.

**Mitigations:** Grounding/RAG with citations; human review for high-stakes; confidence and refusal policies; monitoring; domain-specific evals.

**Agent focus:** Wrong tool choice based on bad “facts” can cascade (see Agentic ASI08).

---

## LLM10:2025 — Unbounded Consumption

**Risk:** Uncontrolled inference → DoS, **denial of wallet**, service degradation, **model extraction** / shadow models, side channels.

**Examples:** Variable-length floods; API scraping for distillation; GPU memory attacks (e.g. LeftoverLocals class of issues).

**Mitigations:** Input size limits; rate limiting and quotas; restrict logprobs exposure; timeouts/throttling; sandbox network access; monitoring; watermarking; graceful degradation; queue limits and scaling; access controls on model artifacts.

**Agent focus:** Maps to **budget/rate caps** and loop limits in your graph.

---

## Quick reference — all ten

| ID | Name | One-line |
|----|------|----------|
| LLM01 | Prompt Injection | Direct/indirect manipulation of model behavior |
| LLM02 | Sensitive Information Disclosure | PII/secrets/IP in outputs or training |
| LLM03 | Supply Chain | Untrusted models, deps, adapters, licenses |
| LLM04 | Data and Model Poisoning | Poisoned training/embeddings/backdoors |
| LLM05 | Improper Output Handling | Unsafe use of model output in apps |
| LLM06 | Excessive Agency | Too much tool power/autonomy |
| LLM07 | System Prompt Leakage | Secrets/rules in prompts; weak external controls |
| LLM08 | Vector and Embedding Weaknesses | RAG/embedding security |
| LLM09 | Misinformation | Harmful false outputs |
| LLM10 | Unbounded Consumption | Resource/cost/model abuse |

## Phase 0 emphasis (per learning plan)

Study all ten; **deep dive** on:

- **LLM01** — direct *and* indirect injection  
- **LLM06** — excessive agency (tools, permissions, autonomy)  
- **LLM07** — system prompt leakage and why prompts ≠ security  
