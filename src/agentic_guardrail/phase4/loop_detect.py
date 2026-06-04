"""Detect repeated or oscillating tool-call fingerprints."""

from __future__ import annotations

# Same call signature repeated this many times → halt (runaway / hijack loop)
MAX_IDENTICAL_REPEATS = 2


def detect_tool_loop_anomaly(
    history: list[str],
    fingerprint: str,
    *,
    max_identical: int = MAX_IDENTICAL_REPEATS,
) -> str | None:
    """
    Return a human-readable reason if the next call would be anomalous, else None.
    """
    if not fingerprint:
        return None
    repeats = sum(1 for h in history if h == fingerprint)
    if repeats >= max_identical:
        return (
            f"repeated tool signature {fingerprint!r} "
            f"({repeats + 1} attempts; max {max_identical} identical before block)"
        )
    if len(history) >= 4:
        last_two = history[-2:]
        if len(last_two) == 2 and last_two[0] != last_two[1]:
            # A→B→A→B oscillation
            if (
                len(history) >= 4
                and history[-4] == history[-2]
                and history[-3] == history[-1]
                and fingerprint in (history[-2], history[-1])
            ):
                return f"oscillating tool pattern detected ending with {fingerprint!r}"
    return None
