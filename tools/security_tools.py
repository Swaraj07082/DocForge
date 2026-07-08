import json
import subprocess
import sys

from tools.static_findings import enrich_findings, parse_semgrep_output


def _run_tool(command: list[str], module_fallback: list[str]) -> str:
    run_kwargs = {
        "capture_output": True,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
    }
    try:
        result = subprocess.run(command, **run_kwargs)
    except FileNotFoundError:
        result = subprocess.run([sys.executable, "-m", *module_fallback], **run_kwargs)

    output = result.stdout.strip()
    errors = result.stderr.strip()
    if output and errors:
        return f"{output}\n{errors}"
    if output:
        return output
    if errors:
        return errors
    return ""


def run_semgrep(file_name: str) -> str:
    return _run_tool(
        ["semgrep", "scan", "--config", "auto", "--json", file_name],
        ["semgrep", "scan", "--config", "auto", "--json", file_name],
    )


def get_semgrep_findings(file_name: str) -> list[dict]:
    raw = parse_semgrep_output(run_semgrep(file_name), file_name)
    return [finding.to_dict() for finding in enrich_findings(raw)]


if __name__ == "__main__":
    print(json.dumps(get_semgrep_findings("app.py"), indent=2))
