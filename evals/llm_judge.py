"""LLM-as-judge groundedness eval over local DocForge reports."""

from __future__ import annotations

import json
import os
from typing import Any, Literal

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, ConfigDict, Field

from utilites.b2_utils import get_all_reports
from utilites.groq_utils import create_chat_completion

load_dotenv()

EVAL_MODEL = "openai/gpt-oss-120b"

PROMPT_TEMPLATE = """You are an impartial evaluator of code-review findings.

EVIDENCE (code only):
{affected_code}

FINDING:
- title: {title}
- finding_type: {finding_type}
- reasoning: {reasoning}
- recommendation: {recommendation}

Decide if the finding is supported by the evidence.
- yes: clearly supported
- partial: vaguely related but overstated
- no: not supported / hallucinated

Return JSON matching the schema. Do not propose new findings.
"""


class FindingJudgeScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grounded: Literal["yes", "no", "partial"]
    score: float = Field(ge=0, le=1)  # 1=yes, 0.5=partial, 0=no
    rationale: str


def judge_one(finding: dict[str, Any], *, client: Groq | None = None) -> FindingJudgeScore:
    """Score a single finding for groundedness against its affected_code."""
    client = client or Groq(api_key=os.getenv("GROQ_API_KEY"))
    prompt = PROMPT_TEMPLATE.format(
        affected_code=finding.get("affected_code") or "(no code provided)",
        title=finding.get("title") or "",
        finding_type=finding.get("finding_type") or "",
        reasoning=finding.get("reasoning") or "",
        recommendation=finding.get("recommendation") or "",
    )

    chat_completion = create_chat_completion(
        client,
        model=EVAL_MODEL,
        max_tokens=500,
        temperature=0,
        messages=[
            {"role": "system", "content": "You are an LLM-as-judge evaluator."},
            {"role": "user", "content": prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "strict": True,
                "name": "llm_as_judge_review_response",
                "schema": FindingJudgeScore.model_json_schema(),
            },
        },
    )
    content = chat_completion.choices[0].message.content
    return FindingJudgeScore.model_validate_json(content)


def score_report(
    report: dict[str, Any],
    *,
    client: Groq | None = None,
) -> dict[str, Any]:
    """Score all accepted_findings in one report and return a scorecard."""
    client = client or Groq(api_key=os.getenv("GROQ_API_KEY"))
    findings = report.get("accepted_findings") or []
    per_finding: list[dict[str, Any]] = []

    for finding in findings:
        result = judge_one(finding, client=client)
        per_finding.append(
            {
                "title": finding.get("title"),
                "finding_type": finding.get("finding_type"),
                "affected_function": finding.get("affected_function"),
                **result.model_dump(),
            }
        )

    if not per_finding:
        return {
            "finding_count": 0,
            "groundedness": None,
            "counts": {"yes": 0, "no": 0, "partial": 0},
            "findings": [],
        }

    groundedness = sum(item["score"] for item in per_finding) / len(per_finding)
    counts = {"yes": 0, "no": 0, "partial": 0}
    for item in per_finding:
        counts[item["grounded"]] = counts.get(item["grounded"], 0) + 1

    return {
        "finding_count": len(per_finding),
        "groundedness": round(groundedness, 4),
        "counts": counts,
        "findings": per_finding,
    }


def main() -> None:
    reports = get_all_reports()
    if not reports:
        print("No reports found under reports/report_*.json")
        return

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    scorecards: list[dict[str, Any]] = []

    for entry in reports:
        card = score_report(entry["report"], client=client)
        card["path"] = entry["path"]
        card["file_name"] = entry["file_name"]
        scorecards.append(card)
        print(
            f"{entry['file_name']}: groundedness={card['groundedness']} "
            f"({card['finding_count']} findings, {card['counts']})"
        )

    scored = [c for c in scorecards if c["groundedness"] is not None]
    if scored:
        overall = sum(c["groundedness"] for c in scored) / len(scored)
        print(f"\nOverall groundedness across {len(scored)} report(s): {overall:.4f}")

    out_path = os.path.join("evals", "groundedness_scorecard.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(scorecards, f, indent=2)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
