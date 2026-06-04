"""Microsoft Presidio PII detection — local analyzer, reversible-style tokens."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

from agentic_guardrail.phase2.scanners import PiiScan, apply_pii_tokens

if TYPE_CHECKING:
    from presidio_analyzer import AnalyzerEngine

logger = logging.getLogger(__name__)

# Presidio entity → token prefix (banking-relevant subset)
# Entity types that trigger input rewrite (exclude LOCATION/PERSON — noisy in reg text)
PII_ENTITY_TYPES: list[str] = [
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "US_SSN",
    "US_BANK_NUMBER",
    "CREDIT_CARD",
    "IBAN_CODE",
    "IP_ADDRESS",
    "US_DRIVER_LICENSE",
    "US_PASSPORT",
    "MEDICAL_LICENSE",
    "URL",
]

ENTITY_TO_KIND: dict[str, str] = {
    "EMAIL_ADDRESS": "email",
    "PHONE_NUMBER": "phone",
    "US_SSN": "ssn",
    "US_BANK_NUMBER": "account",
    "CREDIT_CARD": "card",
    "IBAN_CODE": "iban",
    "IP_ADDRESS": "ip",
    "US_DRIVER_LICENSE": "id",
    "US_PASSPORT": "id",
    "MEDICAL_LICENSE": "medical",
    "URL": "url",
}

SPACY_MODEL = "en_core_web_sm"
DEFAULT_LANGUAGE = "en"


@lru_cache(maxsize=1)
def _analyzer() -> AnalyzerEngine:
    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer.nlp_engine import NlpEngineProvider

    provider = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": SPACY_MODEL}],
        }
    )
    nlp_engine = provider.create_engine()
    return AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=[DEFAULT_LANGUAGE])


def presidio_available() -> bool:
    """True if Presidio and the configured spaCy model are loadable."""
    try:
        import spacy  # noqa: F401

        spacy.load(SPACY_MODEL)
        from presidio_analyzer import AnalyzerEngine  # noqa: F401

        return True
    except Exception as exc:
        logger.debug("Presidio unavailable: %s", exc)
        return False


def scan_pii_presidio(
    text: str,
    *,
    language: str = DEFAULT_LANGUAGE,
    score_threshold: float = 0.35,
) -> PiiScan:
    """
    Detect PII with Presidio; emit <PII_KIND_N> tokens and reversible map.

    Overlapping spans are merged by taking higher score per character (simple dedupe:
    drop spans fully contained in a longer span).
    """
    analyzer = _analyzer()
    results = analyzer.analyze(
        text=text,
        language=language,
        entities=PII_ENTITY_TYPES,
        score_threshold=score_threshold,
    )

    raw: list[tuple[str, int, int, str, float]] = []
    for r in results:
        kind = ENTITY_TO_KIND.get(r.entity_type, r.entity_type.lower())
        raw.append((kind, r.start, r.end, text[r.start : r.end], r.score))

    spans = _dedupe_spans(raw)
    token_map: dict[str, str] = {}
    counters: dict[str, int] = {}
    out_spans: list[tuple[str, int, int, str]] = []

    for kind, start, end, original, _score in sorted(spans, key=lambda s: s[1]):
        counters[kind] = counters.get(kind, 0) + 1
        token = f"<PII_{kind.upper()}_{counters[kind]}>"
        token_map[token] = original
        out_spans.append((kind, start, end, original))

    scan = PiiScan(spans=out_spans, token_map=token_map)
    return scan


def anonymize_with_presidio(text: str, scan: PiiScan) -> str:
    """Apply token placeholders (same contract as regex path)."""
    return apply_pii_tokens(text, scan)


def _dedupe_spans(
    raw: list[tuple[str, int, int, str, float]],
) -> list[tuple[str, int, int, str, float]]:
    if not raw:
        return []
    ordered = sorted(raw, key=lambda s: (s[1], -(s[2] - s[1])))
    kept: list[tuple[str, int, int, str, float]] = []
    for candidate in ordered:
        c_start, c_end = candidate[1], candidate[2]
        if any(c_start >= k[1] and c_end <= k[2] for k in kept):
            continue
        kept.append(candidate)
    return sorted(kept, key=lambda s: s[1])
