"""Injection/structure heuristics; PII via Presidio (fallback: regex)."""

from __future__ import annotations

import re
from dataclasses import dataclass

INJECTION_PATTERNS: list[tuple[str, float]] = [
    (r"ignore\s+(all\s+)?(previous|prior)\s+instructions", 0.95),
    (r"disregard\s+(all\s+)?(previous|prior|above)", 0.9),
    (r"reveal\s+(your\s+)?(system\s+)?prompt", 0.95),
    (r"show\s+(me\s+)?(your\s+)?(system\s+)?prompt", 0.85),
    (r"what\s+are\s+your\s+(hidden\s+)?instructions", 0.85),
    (r"you\s+are\s+now\s+(in\s+)?(dan|developer)\s+mode", 0.9),
    (r"do\s+anything\s+now", 0.75),
    (r"bypass\s+(safety|security|guardrails?)", 0.9),
    (r"exfiltrat", 0.85),
    (r"send\s+(all|every)\s+(emails?|data)\s+to", 0.8),
]

DENY_TOPIC_PATTERNS: list[tuple[str, float]] = [
    (r"\b(hack|exploit)\s+(the|our)\s+(bank|core)\b", 0.7),
]

PII_PATTERNS: list[tuple[str, str]] = [
    ("email", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    ("phone", r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    ("ssn", r"\b\d{3}-\d{2}-\d{4}\b"),
    ("account", r"\b(?:IBAN|ACCT|ACCOUNT)[:\s#]*[A-Z0-9]{8,}\b"),
]


@dataclass(frozen=True)
class InjectionScan:
    score: float
    hits: list[str]


@dataclass(frozen=True)
class PiiScan:
    spans: list[tuple[str, int, int, str]]
    token_map: dict[str, str]


def scan_injection(text: str) -> InjectionScan:
    lowered = text.lower()
    score = 0.0
    hits: list[str] = []
    for pattern, weight in INJECTION_PATTERNS + DENY_TOPIC_PATTERNS:
        if re.search(pattern, lowered, re.I):
            score = max(score, weight)
            hits.append(pattern)
    return InjectionScan(score=min(score, 1.0), hits=hits)


def scan_structure(text: str, *, max_chars: int = 8000) -> tuple[float, str]:
    if not text or not text.strip():
        return 1.0, "empty request"
    if len(text) > max_chars:
        return 0.9, f"exceeds max length {max_chars}"
    return 0.0, "ok"


def scan_pii_regex(text: str) -> PiiScan:
    spans: list[tuple[str, int, int, str]] = []
    token_map: dict[str, str] = {}
    counters: dict[str, int] = {}

    for kind, pattern in PII_PATTERNS:
        for match in re.finditer(pattern, text, re.I):
            original = match.group(0)
            counters[kind] = counters.get(kind, 0) + 1
            token = f"<PII_{kind.upper()}_{counters[kind]}>"
            token_map[token] = original
            spans.append((kind, match.start(), match.end(), original))

    spans.sort(key=lambda s: s[1])
    return PiiScan(spans=spans, token_map=token_map)


def scan_pii(text: str, *, backend: str = "auto") -> PiiScan:
    """
    Detect PII for input guard rewrite path.

    backend: ``auto`` (Presidio if installed), ``presidio``, or ``regex``.
    """
    if backend == "regex":
        return scan_pii_regex(text)
    if backend == "presidio":
        from agentic_guardrail.phase2.presidio_pii import scan_pii_presidio

        return scan_pii_presidio(text)
    from agentic_guardrail.phase2.presidio_pii import presidio_available, scan_pii_presidio

    if presidio_available():
        return scan_pii_presidio(text)
    return scan_pii_regex(text)


def apply_pii_tokens(text: str, scan: PiiScan) -> str:
    result = text
    counters: dict[str, int] = {}
    replacements: list[tuple[int, int, str]] = []
    for kind, start, end, _orig in scan.spans:
        counters[kind] = counters.get(kind, 0) + 1
        token = f"<PII_{kind.upper()}_{counters[kind]}>"
        replacements.append((start, end, token))
    for start, end, token in sorted(replacements, key=lambda r: r[0], reverse=True):
        result = result[:start] + token + result[end:]
    return result
