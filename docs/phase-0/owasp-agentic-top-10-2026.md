# OWASP Top 10 for Agentic Applications (2026)

**Source:** OWASP GenAI Security Project (announced December 2025).

**Official:** https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

This list **complements** the [LLM Top 10 (2025)](./owasp-llm-top-10-2025.md). It describes what happens when LLM weaknesses gain **autonomy, memory, tools, and delegation** — failures become **kinetic** (actions), not only informational (text).

Use both taxonomies in Phase 0: LLM Top 10 for model/app surfaces; Agentic Top 10 for multi-step workflows and tool orchestration.

---

## The ten risks (ASI01–ASI10)

| ID | Name | Summary |
|----|------|---------|
| **ASI01** | Agent Goal Hijack | Adversary redirects plan/objectives via malicious content (extends prompt injection) |
| **ASI02** | Tool Misuse and Exploitation | Legitimate tools used in unsafe or unauthorized ways |
| **ASI03** | Identity and Privilege Abuse | Agent inherits, shares, or escalates credentials incorrectly |
| **ASI04** | Agentic Supply Chain Vulnerabilities | Compromised tools, MCP servers, plugins, agent packages |
| **ASI05** | Unexpected Code Execution | Generated or invoked code crosses trust boundaries |
| **ASI06** | Memory and Context Poisoning | Persistent memory, RAG, or context stores manipulated |
| **ASI07** | Insecure Inter-Agent Communication | Spoofing, replay, lack of auth between agents |
| **ASI08** | Cascading Failures | Small errors propagate across planning and execution |
| **ASI09** | Human–Agent Trust Exploitation | Over-trust in agent recommendations or UI |
| **ASI10** | Rogue Agents | Compromised or drifted agents acting harmfully while appearing normal |

---

## Relationship to LLM Top 10 (selected mappings)

| Agentic (2026) | Related LLM (2025) |
|----------------|-------------------|
| ASI01 Goal Hijack | LLM01 Prompt Injection |
| ASI02 Tool Misuse | LLM06 Excessive Agency |
| ASI03 Identity / Privilege | LLM06 Excessive Agency |
| ASI04 Agentic Supply Chain | LLM03 Supply Chain |
| ASI05 Unexpected Code Execution | LLM01, LLM05 Improper Output Handling |
| ASI06 Memory / Context Poisoning | LLM04 Poisoning, LLM08 Vectors |
| ASI08 Cascading Failures | LLM09 Misinformation (plus operational design) |
| ASI10 Rogue Agents | LLM06, supply chain, monitoring |

Your LangGraph learning path still anchors on **LLM01 / LLM06 / LLM07** first; map agentic IDs when you design multi-agent or long-running memory systems.

---

## Design lens (from OWASP messaging)

- Agents **plan**, **persist state**, **call tools**, and **act** — threat models must include blast radius per tool, not only prompt/response.  
- A single compromise can **cascade** across workflows (ASI08).  
- **Human gates** address ASI09 and high-impact ASI02 paths when automation is unsafe.

For mitigations and incident examples, read the full agentic publication on genai.owasp.org when implementing Phase 4+.
