from agents.architecture_agent import ArchitectureAgent
from agents.security_agent import SecurityAgent
from agents.refactoring_agent import RefactoringAgent
from agents.test_agent import TestAgent
import json
from repo_analyser import analyse_symbol
from groq import Groq
import os
from dotenv import load_dotenv
from utilites.pydantic_types import AgentResponse , JudgeResponse
from utilites.get_analysis import get_analysis
from utilites.groq_utils import create_chat_completion

load_dotenv()

class JudgeAgent(ArchitectureAgent , SecurityAgent , RefactoringAgent , TestAgent):

    def __init__(self, model):
        super().__init__(model)
        self.result : dict = {}
        self.analysis : list = []
    
    def findings(self, file_name: str, workspace_dir: str = ".") -> dict:

        self.analysis = get_analysis(file_name, workspace_dir=workspace_dir)
        architect_findings = ArchitectureAgent.get_code(self, file_name=file_name, workspace_dir=workspace_dir)
        security_findings = SecurityAgent.get_code(self, file_name=file_name, workspace_dir=workspace_dir)
        refactoring_findings = RefactoringAgent.get_code(self, file_name=file_name, workspace_dir=workspace_dir)
        test_findings = TestAgent.get_code(self, file_name=file_name, workspace_dir=workspace_dir)

        self.result["architecture"] = architect_findings
        self.result["security"] = security_findings
        self.result["refactor"] = refactoring_findings
        self.result["test"] = test_findings

        return self.result

    def review(self, agent_findings: list, context: list) -> str:
        # Trim the code context so the judge request stays under the model's
        # per-minute token budget; the findings already carry affected_code.
        context_str = str(context)
        max_context_chars = 4000
        if len(context_str) > max_context_chars:
            context_str = context_str[:max_context_chars] + " ...[truncated]"

        prompt = f"""You are a Principal Software Engineer acting as the final reviewer.

You are given:

1. The source code and surrounding context. - {context_str}
2. Findings from multiple specialized review agents (each finding is tagged
   with the "agent" that produced it): {agent_findings}

Your responsibilities are:

- Validate every finding against the provided code.
- Remove duplicate findings.
- Reject findings that are unsupported by the code.
- Merge findings that describe the same underlying issue.
- Resolve disagreements between agents.
- Prioritize findings by severity and impact.
- Produce a final review report.

Do NOT invent new issues that were not raised unless they are immediately obvious from the supplied code.

For every accepted finding include ALL of these fields:
- finding_type (exactly one of the allowed finding_type values)
- severity (one of: low, medium, high, critical)
- confidence
- title
- reasoning
- recommendation
- affected_function
- affected_code

Also provide:

- overall_code_quality_score (0-100)
- summary
- highest_priority_issue

Return ONLY JSON matching the schema."""

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        chat_completion = create_chat_completion(
            client,
            model=self.model,
            max_tokens=3000,
            reasoning_effort="low",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "strict": True,
                    "name": "judge_review_response",
                    "schema": JudgeResponse.model_json_schema(),
                },
            },
        )

        return chat_completion.choices[0].message.content

    # def get_code(self , file_name):
        
    #     with open("symbol_index.json", "r") as f:
    #         symbol_index = json.load(f)

    #     # print(symbol_index)

    #     functions : list = []
    #     # getting all the functions from the symbol index that are in the file_name

    #     for symbol in symbol_index:
    #         if symbol_index[symbol][0] == f"{file_name}":
    #             functions.append(symbol)

    #     analysis = []
    #     for fn in functions:
    #         analysis.append(analyse_symbol(fn))

        

        prompt = f"""
        You are a refactoring agent.
        
        Review this code:
        
        {analysis}
        
        Find:
        - Long functions
        - Duplication
        - SRP violations
        - Readability issues
        
        Return findings as JSON matching the schema. For EVERY finding you MUST
        include a "finding_type" field, and its value MUST be exactly one of:
        "long_function", "duplicate_code", "dead_code", "high_complexity",
        "large_class", "poor_naming", "single_responsibility_violation",
        "tight_coupling", "duplication", "readability_issue".

        Every finding must also include all of these fields: finding_type,
        severity, confidence, title, reasoning, recommendation,
        affected_function, affected_code.

        Be concise. Return AT MOST 4 findings. For "affected_code", include ONLY
        the function signature line (e.g. "def predict():"), never the full
        function body. Keep "reasoning" and "recommendation" to one short sentence.
"""
         
        
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        chat_completion = client.chat.completions.create(
            model = self.model,
            max_tokens=5000,
            messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": prompt,
        }
    ],
     response_format={
        "type": "json_schema",
        "json_schema": {
            "strict" : True ,
            "name": "sql_query_generation",
            "schema": AgentResponse.model_json_schema()
        }
    }
        )

        raw_content = chat_completion.choices[0].message.content
        validated = JudgeResponse.model_validate_json(raw_content)
        return validated.model_dump_json()

     
    def judgeResponse(self , file_name):

        findings = self.findings(file_name)
        context = self.analysis

        architecture = findings["architecture"]
        security = findings["security"]
        refactor = findings["refactor"]
        test = findings["test"]

        prompt = f"""You are a Principal Software Engineer acting as the final reviewer.

You are given:

1. The source code and surrounding context. - {context}
2. Findings from multiple specialized review agents:
   - Refactoring - {refactor}
   - Security - {security}
   - Architecture - {architecture}
   - Testing - {test}

Your responsibilities are:

- Validate every finding against the provided code.
- Remove duplicate findings.
- Reject findings that are unsupported by the code.
- Merge findings that describe the same underlying issue.
- Resolve disagreements between agents.
- Prioritize findings by severity and impact.
- Produce a final review report.

Do NOT invent new issues that were not raised unless they are immediately obvious from the supplied code.

For every accepted finding include ALL of these fields:
- finding_type (exactly one of the allowed finding_type values)
- severity (one of: low, medium, high, critical)
- confidence
- title
- reasoning
- recommendation
- affected_function
- affected_code

Also provide:

- overall_code_quality_score (0-100)
- summary
- highest_priority_issue

Return ONLY JSON matching the schema."""
        
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        chat_completion = client.chat.completions.create(
            model = self.model,
            max_tokens=4069,
            messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": prompt,
        }
    ],
     response_format={
        "type": "json_schema",
        "json_schema": {
            "strict" : True ,
            "name": "sql_query_generation",
            "schema": JudgeResponse.model_json_schema()
        }
    }
        )

        return chat_completion.choices[0].message.content



if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    obj = JudgeAgent("openai/gpt-oss-20b") 
    print(obj.judgeResponse("app.py"))
