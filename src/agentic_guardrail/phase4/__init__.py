"""Phase 4 — tool-call and agency guardrails."""

from agentic_guardrail.phase4.guarded_tool import guarded_tool, score_tool_result
from agentic_guardrail.phase4.models import ToolGuardDecision, ToolScopePolicy
from agentic_guardrail.phase4.policy import REGULATORY_WORKFLOW_SCOPE, authorize_tool_call

__all__ = [
    "REGULATORY_WORKFLOW_SCOPE",
    "ToolGuardDecision",
    "ToolScopePolicy",
    "authorize_tool_call",
    "guarded_tool",
    "score_tool_result",
]
