"""Pre-fan-out gate: block unsafe analysis requests before the 4 agents run."""

from __future__ import annotations

from functools import lru_cache

from nemoguardrails import LLMRails
from nemoguardrails.rails.llm.options import RailStatus, RailType

from guardrails.rails_config import load_rails_config


@lru_cache(maxsize=1)
def _rails() -> LLMRails:
    return LLMRails(load_rails_config())


def check_analysis_request(clone_url: str, file_path: str) -> dict:
    """Return guardrail_allowed / guardrail_reason for graph.py."""
    message = (
        "Code analysis request for a multi-agent review pipeline.\n"
        f"Repository: {clone_url}\n"
        f"File path: {file_path}\n"
        "Please analyze this source file for architecture, security, "
        "refactoring, and test quality."
    )
    result = _rails().check(
        [{"role": "user", "content": message}],
        rail_types=[RailType.INPUT],
    )

    if result.status == RailStatus.BLOCKED:
        reason = result.content or (
            f"Blocked by rail: {result.rail}" if result.rail else "Blocked by input guardrail."
        )
        return {"guardrail_allowed": False, "guardrail_reason": reason}

    return {"guardrail_allowed": True, "guardrail_reason": ""}
