from __future__ import annotations

import json
import os
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tools.confidence_tools import ToolName, compute_confidence, semgrep_metadata_confidence

SYMBOL_INDEX_PATH = "symbol_index.json"
RADON_COMPLEXITY_THRESHOLD = 10
VULTURE_LINE_RE = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+):\s+(?P<message>.+?)\s+\((?P<confidence>\d+)% confidence\)\s*$"
)


@dataclass
class RawFinding:
    tool: ToolName
    rule_id: str
    file: str
    line: int | None
    message: str
    finding_type: str = "readability_issue"
    severity: str = "low"
    native_confidence: float | None = None


@dataclass
class StaticFinding:
    tool: ToolName
    rule_id: str
    file: str
    line: int | None
    message: str
    affected_function: str | None
    affected_code: str
    finding_type: str
    severity: str
    confidence: float
    match_count: int
    weak_context: bool
    symbol_mapping: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize_file_path(path: str) -> str:
    return os.path.basename(path.replace("\\", "/"))


def _symbol_start_line(symbol_id: str) -> int | None:
    try:
        location = symbol_id.rsplit("::", 1)[-1]
        return int(location.split(":")[0])
    except (ValueError, IndexError):
        return None


def _function_signature(code: str) -> str:
    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith("def ") or stripped.startswith("class "):
            return stripped
    first_line = code.splitlines()[0].strip() if code else ""
    return first_line or "unknown"


def load_file_symbol_ranges(symbol_index_path: str = SYMBOL_INDEX_PATH) -> dict[str, list[dict[str, Any]]]:
    path = Path(symbol_index_path)
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as handle:
        symbol_index = json.load(handle)

    grouped: dict[str, list[dict[str, Any]]] = {}
    for symbol_id, payload in symbol_index.items():
        file_name = payload[0]
        start_line = _symbol_start_line(symbol_id)
        if start_line is None:
            continue

        symbol_name = payload[3] if len(payload) > 3 else symbol_id
        code = payload[2] if len(payload) > 2 else ""
        grouped.setdefault(file_name, []).append(
            {
                "start_line": start_line,
                "name": symbol_name,
                "signature": _function_signature(code),
            }
        )

    for symbols in grouped.values():
        symbols.sort(key=lambda item: item["start_line"])
        for index, symbol in enumerate(symbols):
            next_start = symbols[index + 1]["start_line"] if index + 1 < len(symbols) else 10**9
            symbol["end_line"] = next_start - 1

    return grouped


def resolve_symbol(
    file_name: str,
    line: int | None,
    symbol_ranges: dict[str, list[dict[str, Any]]],
) -> tuple[str | None, str, str]:
    if line is None:
        return None, "", "unknown"

    normalized_file = _normalize_file_path(file_name)
    ranges = symbol_ranges.get(normalized_file, [])
    for symbol in ranges:
        if symbol["start_line"] <= line <= symbol["end_line"]:
            return symbol["name"], symbol["signature"], "function"

    if normalized_file:
        return None, "", "file"
    return None, "", "unknown"


def _is_weak_context(*, line: int | None, file_name: str, message: str) -> bool:
    if not message.strip():
        return True
    if line is None:
        return True
    if not _normalize_file_path(file_name):
        return True
    return False


def _group_key(finding: RawFinding, affected_function: str | None) -> tuple[str, str, str, str]:
    scope = affected_function or (f"line:{finding.line}" if finding.line is not None else "unknown")
    return (finding.tool, finding.rule_id, _normalize_file_path(finding.file), scope)


def _attach_dynamic_confidence(
    findings: list[RawFinding],
    symbol_ranges: dict[str, list[dict[str, Any]]],
) -> list[StaticFinding]:
    resolved: list[tuple[RawFinding, str | None, str, str]] = []
    for finding in findings:
        function_name, signature, symbol_mapping = resolve_symbol(
            finding.file,
            finding.line,
            symbol_ranges,
        )
        resolved.append((finding, function_name, signature, symbol_mapping))

    group_counts = Counter(
        _group_key(finding, function_name)
        for finding, function_name, _, _ in resolved
    )

    enriched: list[StaticFinding] = []
    for finding, function_name, signature, symbol_mapping in resolved:
        match_count = group_counts[_group_key(finding, function_name)]
        weak_context = _is_weak_context(
            line=finding.line,
            file_name=finding.file,
            message=finding.message,
        )
        confidence = compute_confidence(
            tool=finding.tool,
            match_count=match_count,
            weak_context=weak_context,
            symbol_mapping=symbol_mapping,
            base_override=finding.native_confidence,
        )
        enriched.append(
            StaticFinding(
                tool=finding.tool,
                rule_id=finding.rule_id,
                file=_normalize_file_path(finding.file),
                line=finding.line,
                message=finding.message,
                affected_function=function_name,
                affected_code=signature,
                finding_type=finding.finding_type,
                severity=finding.severity,
                confidence=confidence,
                match_count=match_count,
                weak_context=weak_context,
                symbol_mapping=symbol_mapping,
            )
        )
    return enriched


def _ruff_meta(rule_id: str) -> tuple[str, str]:
    if rule_id.startswith("S"):
        return "Command Injection", "high"
    if rule_id in {"C901"}:
        return "high_complexity", "medium"
    if rule_id.startswith("E"):
        return "readability_issue", "low"
    return "readability_issue", "low"


def _semgrep_meta(rule_id: str, extra_severity: str | None) -> tuple[str, str]:
    lowered = rule_id.lower()
    if "sql" in lowered:
        finding_type = "SQL Injection"
    elif "xss" in lowered:
        finding_type = "XSS"
    elif "secret" in lowered or "credential" in lowered:
        finding_type = "Hardcoded credentials"
    elif "eval" in lowered:
        finding_type = "Command Injection"
    else:
        finding_type = "Command Injection"

    severity_map = {
        "ERROR": "high",
        "WARNING": "medium",
        "INFO": "low",
    }
    return finding_type, severity_map.get((extra_severity or "").upper(), "medium")


def parse_ruff_output(raw_output: str, file_path: str) -> list[RawFinding]:
    if not raw_output.strip():
        return []

    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError:
        return []

    findings: list[RawFinding] = []
    for item in payload:
        location = item.get("location", {})
        rule_id = str(item.get("code", "unknown"))
        finding_type, severity = _ruff_meta(rule_id)
        findings.append(
            RawFinding(
                tool="ruff",
                rule_id=rule_id,
                file=item.get("filename", file_path),
                line=location.get("row"),
                message=str(item.get("message", "")),
                finding_type=finding_type,
                severity=severity,
            )
        )
    return findings


def parse_vulture_output(raw_output: str, file_path: str) -> list[RawFinding]:
    findings: list[RawFinding] = []
    for line in raw_output.splitlines():
        match = VULTURE_LINE_RE.match(line.strip())
        if not match:
            continue

        native = int(match.group("confidence")) / 100.0
        findings.append(
            RawFinding(
                tool="vulture",
                rule_id="dead_code",
                file=match.group("file") or file_path,
                line=int(match.group("line")),
                message=match.group("message").strip(),
                finding_type="dead_code",
                severity="medium",
                native_confidence=native,
            )
        )
    return findings


def parse_radon_cc_output(raw_output: str, file_path: str) -> list[RawFinding]:
    if not raw_output.strip():
        return []

    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError:
        return []

    findings: list[RawFinding] = []
    normalized_target = _normalize_file_path(file_path)
    for file_name, blocks in payload.items():
        if _normalize_file_path(file_name) != normalized_target:
            continue
        for block in blocks:
            complexity = block.get("complexity", 0)
            if complexity < RADON_COMPLEXITY_THRESHOLD:
                continue
            findings.append(
                RawFinding(
                    tool="radon",
                    rule_id="high_complexity",
                    file=file_name,
                    line=block.get("lineno"),
                    message=(
                        f"Cyclomatic complexity {complexity} "
                        f"(rank {block.get('rank', '?')}) for {block.get('name', 'unknown')}"
                    ),
                    finding_type="high_complexity",
                    severity="medium",
                )
            )
    return findings


def parse_semgrep_output(raw_output: str, file_path: str) -> list[RawFinding]:
    if not raw_output.strip():
        return []

    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError:
        return []

    findings: list[RawFinding] = []
    for item in payload.get("results", []):
        extra = item.get("extra", {})
        metadata = extra.get("metadata", {})
        native = semgrep_metadata_confidence(metadata.get("confidence"))
        start = item.get("start", {})
        finding_type, severity = _semgrep_meta(
            str(item.get("check_id", "unknown")),
            extra.get("severity"),
        )
        findings.append(
            RawFinding(
                tool="semgrep",
                rule_id=str(item.get("check_id", "unknown")),
                file=item.get("path", file_path),
                line=start.get("line"),
                message=str(extra.get("message", "")),
                finding_type=finding_type,
                severity=severity,
                native_confidence=native,
            )
        )
    return findings


def enrich_findings(
    raw_findings: list[RawFinding],
    symbol_index_path: str = SYMBOL_INDEX_PATH,
) -> list[StaticFinding]:
    symbol_ranges = load_file_symbol_ranges(symbol_index_path)
    return _attach_dynamic_confidence(raw_findings, symbol_ranges)
