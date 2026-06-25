from groq import Groq
import json
from repo_analyser import analyse_symbol
from pydantic import BaseModel
from typing import List


class Finding(BaseModel):
    type: str
    severity: str
    confidence: float
    title: str
    reasoning: str
    recommendation: str


class RefactorAgentResponse(BaseModel):
    agent: str
    symbol: str
    findings: List[Finding]

class RefactoringAgent:

    def __init__(self , model):
        self.model = model

    def refactor_code(self , file_name):
        
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
        You are a senior software engineer.
        
        Review this code:
        
        {analysis}
        
        Find:
        - Long functions
        - Duplication
        - SRP violations
        - Readability issues
        
        Return findings.
"""
        
        # print(prompt)

        client = Groq()

        chat_completion = client.chat.completions.create(
            model = self.model,
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
            "name": "sql_query_generation",
            "schema": RefactorAgentResponse.model_json_schema()
        }
    }
    
   
        )
        




obj = RefactoringAgent()
analysis : list = obj.refactor_code("app.py")
print(analysis)

