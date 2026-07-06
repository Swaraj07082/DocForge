from agents.base_agent import BaseReviewAgent


class SecurityAgent(BaseReviewAgent):
    agent_name = "security"
    role = "a Security Agent."
    focus = """Look for:
- SQL injection
- XSS
- Hardcoded secrets
- Unsafe eval"""
    finding_types = (
        "SQL Injection",
        "Command Injection",
        "XSS",
        "CSRF",
        "Path Traversal",
        "Authentication flaws",
        "Authorization flaws",
        "Hardcoded credentials",
        "Insecure cryptography",
        "Unsafe deserialization",
        "SSRF",
        "XXE",
        "Sensitive information leakage",
        "Race conditions with security impact",
        "Unsafe file operations",
    )


if __name__ == "__main__":
    obj = SecurityAgent("openai/gpt-oss-20b")
    print(obj.get_code("app.py"))
