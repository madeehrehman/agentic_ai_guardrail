"""Phase 5 framework toggles (env-driven, safe defaults for CI)."""

from __future__ import annotations

import os
from enum import StrEnum


class OutputBackend(StrEnum):
    HANDROLLED = "handrolled"
    GUARDRAILS = "guardrails"
    LAYERED = "layered"  # Guardrails AI validators, then hand-rolled fallbacks


class TopicalBackend(StrEnum):
    OFF = "off"
    STUB = "stub"  # Colang-like topical rules without NeMo install
    NEMO = "nemo"  # Requires nemoguardrails + config path


def output_backend() -> OutputBackend:
    raw = (os.environ.get("GUARDRAIL_OUTPUT_BACKEND") or "handrolled").lower()
    try:
        return OutputBackend(raw)
    except ValueError:
        return OutputBackend.HANDROLLED


def topical_backend() -> TopicalBackend:
    raw = (os.environ.get("GUARDRAIL_TOPICAL_BACKEND") or "stub").lower()
    try:
        return TopicalBackend(raw)
    except ValueError:
        return TopicalBackend.STUB


def nemo_config_path() -> str | None:
    return os.environ.get("GUARDRAIL_NEMO_CONFIG_PATH")


def guardrails_available() -> bool:
    try:
        import guardrails  # noqa: F401

        return True
    except ImportError:
        return False
