from groq import Groq
import json
from repo_analyser import analyse_symbol
from pydantic import BaseModel
from typing import List , Literal
import os
from dotenv import load_dotenv
from utilites.pydantic_types import AgentResponse

load_dotenv()


class TestAgent:

    def __init__(self , model):
        self.model = model

    def get_code(self , file_name):
        
        with open("symbol_index.json", "r") as f:
            symbol_index = json.load(f)

        # print(symbol_index)

        functions : list = []
        # getting all the functions from the symbol index that are in the file_name

        for symbol in symbol_index:
            if symbol_index[symbol][0] == f"{file_name}":
                functions.append(symbol)

        analysis = []
        for fn in functions:
            analysis.append(analyse_symbol(fn))

        

        prompt = f"""
        You are a Security Agent.
        
        Review this code:
        
        {analysis}
        
        Identify:
        - Missing tests
        - Edge cases
        - Untested branches
        
        Return findings as JSON matching the schema. Every finding object MUST
        include ALL of these fields and you must NOT omit any of them:
        finding_type, severity, confidence, title, reasoning, recommendation,
        affected_function, affected_code.

        "finding_type" MUST be exactly one of: "high_complexity", "dead_code",
        "long_function", "single_responsibility_violation", "readability_issue",
        "duplicate_code", "duplication".
        "severity" MUST be one of: "low", "medium", "high", "critical".

        Be concise. Return AT MOST 4 findings. For "affected_code", include ONLY
        the function signature line (e.g. "def predict():"), never the full
        function body. Keep "reasoning" and "recommendation" to one short sentence.
"""
        
        # print(prompt)

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
            "schema": AgentResponse.model_json_schema()
        }
    }
        )

        return chat_completion.choices[0].message.content
        



if __name__ == "__main__":
    obj = TestAgent("openai/gpt-oss-20b")
    response : list = obj.get_code("app.py")
    print(response)

