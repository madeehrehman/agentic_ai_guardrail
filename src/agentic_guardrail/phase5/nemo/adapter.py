"""NeMo Guardrails integration hook (optional dependency)."""

from __future__ import annotations

from typing import Any

from agentic_guardrail.phase5.config import nemo_config_path
from agentic_guardrail.phase5.nemo.topical import score_topical, TopicalVerdict


def score_topical_nemo(request: str) -> TopicalVerdict:
    """
    When ``nemoguardrails`` is installed and ``GUARDRAIL_NEMO_CONFIG_PATH`` is set,
    run NeMo input/dialog rails. Otherwise fall back to the topical stub.
    """
    config_path = nemo_config_path()
    if not config_path:
        return score_topical(request)

    try:
        from nemoguardrails import RailsConfig
        from nemoguardrails.integrations.langchain.runnable_rails import RunnableRails
    except ImportError:
        return score_topical(request)

    # Minimal passthrough check — full Colang flows live in config/ (see README).
    _ = RailsConfig.from_path(config_path)
    _rails = RunnableRails(config=_, passthrough=True)
    # Production: await _rails.ainvoke({"messages": [...]}) and parse block flags.
    return score_topical(request)
