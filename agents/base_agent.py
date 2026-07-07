import os

from dotenv import load_dotenv
from groq import Groq

from utilites.get_analysis import get_analysis
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

    def _build_prompt(self, analysis: list) -> str:
        finding_types = ", ".join(f'"{t}"' for t in self.finding_types)
        return f"""
You are {self.role}

Review this code:

{analysis}

{self.focus}

{FINDING_FIELDS_INSTRUCTION}
"finding_type" MUST be exactly one of: {finding_types}.
Set the top-level "agent" field to "{self.agent_name}".
"""

    def get_code(self, file_name: str) -> str:
        analysis = get_analysis(file_name)
        prompt = self._build_prompt(analysis)

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        chat_completion = client.chat.completions.create(
            model=self.model,
            max_tokens=4069,
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
