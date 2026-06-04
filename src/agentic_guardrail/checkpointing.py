"""Graph checkpointers — SQLite for durable HITL, memory for tests."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

DEFAULT_CHECKPOINT_DB = Path(".data/checkpoints.db")


def get_checkpointer(
    *,
    backend: str | None = None,
    db_path: Path | str | None = None,
) -> MemorySaver | SqliteSaver:
    """
    Return a LangGraph checkpointer.

    backend:
      - ``auto`` (default): SQLite unless ``GUARDRAIL_CHECKPOINT=memory``
      - ``sqlite`` / ``memory``
    """
    resolved = backend or os.environ.get("GUARDRAIL_CHECKPOINT", "auto")
    if resolved == "auto":
        resolved = "sqlite"

    if resolved == "memory":
        return MemorySaver()

    if resolved != "sqlite":
        raise ValueError(f"unknown checkpoint backend: {resolved}")

    path = Path(db_path or os.environ.get("GUARDRAIL_CHECKPOINT_DB", DEFAULT_CHECKPOINT_DB))
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    saver = SqliteSaver(conn)
    saver.setup()
    return saver


def run_config(
    thread_id: str,
    *,
    recursion_limit: int = 25,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Invoke/stream config: thread + LangGraph recursion cap (learning plan)."""
    cfg: dict[str, Any] = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": recursion_limit,
    }
    if extra:
        cfg.update(extra)
    return cfg
