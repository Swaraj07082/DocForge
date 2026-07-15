import os

from dotenv import load_dotenv
from groq import Groq

from utilites.get_analysis import get_analysis
from utilites.groq_utils import create_chat_completion
from utilites.pydantic_types import AgentResponse

load_dotenv()

FINDING_FIELDS_INSTRUCTION = """
Return findings as JSON matching the schema. Every finding object MUST
include ALL of these fields and you must NOT omit any of them:
finding_type, severity, confidence, title, reasoning, recommendation,
affected_function, affected_code.

"severity" MUST be one of: "low", "medium", "high", "critical".

Be concise. Return AT MOST 4 findings. For "affected_code", include ONLY
the function signature line (e.g. "def predict():"), never the full
function body. Keep "reasoning" and "recommendation" to one short sentence.
"""


class BaseReviewAgent:
    agent_name: str
    role: str
    focus: str
    finding_types: tuple[str, ...]

    def __init__(self, model: str):
        self.model = model

    def _build_prompt(self, analysis: list, static_findings: list | None = None) -> str:
        finding_types = ", ".join(f'"{t}"' for t in self.finding_types)
        static_section = ""
        if static_findings:
            static_section = f"""
Static analysis tools (ruff, radon, vulture) already reported the findings
below. Treat them as grounding signals: validate them against the code,
expand on them, and do not blindly trust them.

{static_findings}
"""
        return f"""
You are {self.role}

Review this code:

{analysis}
{static_section}
{self.focus}

{FINDING_FIELDS_INSTRUCTION}
"finding_type" MUST be exactly one of: {finding_types}.
Set the top-level "agent" field to "{self.agent_name}".
"""

    def get_code(self, file_name: str, static_findings: list | None = None) -> str:
        analysis = get_analysis(file_name)
        prompt = self._build_prompt(analysis, static_findings)

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        chat_completion = create_chat_completion(
            client,
            model=self.model,
            max_tokens=2000,
            reasoning_effort="low",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "strict": True,
                    "name": "agent_review_response",
                    "schema": AgentResponse.model_json_schema(),
                },
            },
        )

        raw_content = chat_completion.choices[0].message.content
        validated = AgentResponse.model_validate_json(raw_content)
        return validated.model_dump_json()
