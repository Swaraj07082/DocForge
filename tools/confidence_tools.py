from __future__ import annotations

from typing import Literal

ToolName = Literal["semgrep", "ruff", "radon", "vulture"]

_BASE_CONFIDENCE: dict[ToolName, float] = {
    "semgrep": 0.90,
    "ruff": 0.85,
    "radon": 0.95,
    "vulture": 0.65,
}


def _evidence_multiplier(match_count: int, weak_context: bool) -> float:
    if weak_context:
        return 0.85
    if match_count > 1:
        return 1.05
    return 1.00


def _symbol_mapping_multiplier(symbol_mapping: str) -> float:
    if symbol_mapping == "function":
        return 1.00
    if symbol_mapping == "file":
        return 0.90
    if symbol_mapping == "unknown":
        return 0.75
    raise ValueError("symbol_mapping must be one of: function, file, unknown")


def semgrep_metadata_confidence(value: str | None) -> float | None:
    if not value:
        return None
    mapping = {"HIGH": 0.95, "MEDIUM": 0.80, "LOW": 0.60}
    return mapping.get(value.upper())


def compute_confidence(
    *,
    tool: ToolName,
    match_count: int = 1,
    weak_context: bool = False,
    symbol_mapping: str = "function",
    base_override: float | None = None,
) -> float:
    """
    Compute normalized confidence for a static finding.

    Formula:
    confidence = base(tool or override) * evidence(match_count, weak_context) * symbol_mapping
    """
    if match_count < 1:
        raise ValueError("match_count must be >= 1")

    base = base_override if base_override is not None else _BASE_CONFIDENCE[tool]
    evidence = _evidence_multiplier(match_count=match_count, weak_context=weak_context)
    symbol = _symbol_mapping_multiplier(symbol_mapping=symbol_mapping)

    confidence = base * evidence * symbol
    return max(0.0, min(1.0, round(confidence, 3)))
