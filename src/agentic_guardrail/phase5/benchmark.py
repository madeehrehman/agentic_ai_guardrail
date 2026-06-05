"""Compare hand-rolled vs Guardrails AI output guard latency."""

from __future__ import annotations

import argparse
import statistics
import time

from agentic_guardrail.phase3.guards import score_output as handrolled
from agentic_guardrail.phase5.guardrails_output import score_output_guardrails


SAMPLE = (
    "Based on approved internal sources: BCBS 239 requires banks to establish "
    "strong governance. Sources: [source:bcbs239-summary] BCBS 239 summary"
)
CHUNK_IDS = ["bcbs239-summary"]


def _time(fn, n: int) -> list[float]:
    times: list[float] = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000)
    return times


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 5 output guard benchmark")
    parser.add_argument("-n", type=int, default=50, help="iterations per backend")
    args = parser.parse_args()

    hand_times = _time(
        lambda: handrolled(SAMPLE, approved_chunk_ids=CHUNK_IDS), args.n
    )
    try:
        guard_times = _time(
            lambda: score_output_guardrails(SAMPLE, approved_chunk_ids=CHUNK_IDS),
            args.n,
        )
    except Exception as exc:
        print(f"Guardrails AI unavailable: {exc}")
        guard_times = []

    print(f"handrolled  p50={statistics.median(hand_times):.2f}ms  p95={sorted(hand_times)[int(0.95*len(hand_times))]:.2f}ms")
    if guard_times:
        print(
            f"guardrails  p50={statistics.median(guard_times):.2f}ms  "
            f"p95={sorted(guard_times)[int(0.95 * len(guard_times))]:.2f}ms"
        )


if __name__ == "__main__":
    main()
