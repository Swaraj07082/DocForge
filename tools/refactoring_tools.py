# we will use ruff and radon/lizard + vulture her to get findings

import subprocess
import sys

from tools.static_findings import enrich_findings, parse_radon_cc_output, parse_ruff_output, parse_vulture_output


def _run_tool(command: list[str], module_fallback: list[str]) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except FileNotFoundError:
        result = subprocess.run(
            [sys.executable, "-m", *module_fallback], capture_output=True, text=True
        )

    output = result.stdout.strip()
    errors = result.stderr.strip()
    # Keep structured stdout (JSON) clean for parsers.
    if output:
        return output
    if errors:
        return errors
    return ""


def run_ruff(file_path: str) -> str:
    # Focused rule set (real bugs, security, complexity) instead of ALL, which
    # produces hundreds of stylistic findings that drown the LLM and blow past
    # token limits. E=errors, F=pyflakes, B=bugbear, S=bandit, C90=mccabe.
    return _run_tool(
        ["ruff","check",file_path,"--select","E,F,B,S,C90","--output-format=json"],
        ["ruff","check",file_path,"--select","E,F,B,S,C90","--output-format=json"],
    )


def run_radon(task: str, file_path: str) -> str:
    return _run_tool(
        ["radon", task, "-j", file_path],
        ["radon", task, "-j", file_path],
    )


def run_vulture(file_path: str) -> str:
    return _run_tool(["vulture", file_path], ["vulture", file_path])


def get_ruff_findings(file_path: str) -> list[dict]:
    raw = parse_ruff_output(run_ruff(file_path), file_path)
    return [finding.to_dict() for finding in enrich_findings(raw)]


def get_radon_findings(file_path: str) -> list[dict]:
    raw = parse_radon_cc_output(run_radon("cc", file_path), file_path)
    return [finding.to_dict() for finding in enrich_findings(raw)]


def get_vulture_findings(file_path: str) -> list[dict]:
    raw = parse_vulture_output(run_vulture(file_path), file_path)
    return [finding.to_dict() for finding in enrich_findings(raw)]


def get_refactoring_findings(file_path: str) -> list[dict]:
    findings: list[dict] = []
    findings.extend(get_ruff_findings(file_path))
    findings.extend(get_radon_findings(file_path))
    findings.extend(get_vulture_findings(file_path))
    return findings


if __name__ == "__main__":
    import json

    print(json.dumps(get_ruff_findings("error.py"), indent=2))
    # print(json.dumps(run_radon("cc" , "error.py") , indent = 2))
