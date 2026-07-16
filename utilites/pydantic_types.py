from pydantic import BaseModel , ConfigDict
from typing import Literal , List , Optional

class Finding(BaseModel):    

    model_config = ConfigDict(extra="forbid")

    finding_type: Literal[
    "long_function", "duplicate_code", "dead_code", "high_complexity",
    "large_class", "poor_naming", "single_responsibility_violation",
    "tight_coupling", "SQL Injection", "Command Injection", "XSS", "CSRF",
    "Path Traversal", "Authentication flaws", "Authorization flaws",
    "Hardcoded credentials", "Insecure cryptography", "Unsafe deserialization",
    "SSRF", "XXE", "Sensitive information leakage", "Race conditions with security impact",
    "Unsafe file operations", "duplication", "readability_issue",
    "missing_test", "untested_branch", "missing_edge_case", "insufficient_test_coverage",
]
    severity: Literal["low", "medium", "high", "critical"]
    confidence: float
    title: str
    reasoning: str
    recommendation: str
    affected_function: Optional[str]
    affected_code: Optional[str]

class AgentResponse(BaseModel):
    
    model_config = ConfigDict(extra="forbid")

    agent: Literal[ "security", "refactoring", "architecture", "testing" ] 
    findings: List[Finding]


class JudgeResponse(BaseModel):
    
    model_config = ConfigDict(extra="forbid")

    overall_code_quality_score: int
    summary: str
    highest_priority_issue: str
    accepted_findings: list[Finding]
    rejected_findings: list[str]