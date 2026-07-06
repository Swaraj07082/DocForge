from agents.base_agent import BaseReviewAgent


class RefactoringAgent(BaseReviewAgent):
    agent_name = "refactoring"
    role = "a Refactoring Agent."
    focus = """Find:
- Long functions
- Duplication
- SRP violations
- Readability issues"""
    finding_types = (
        "long_function",
        "duplicate_code",
        "dead_code",
        "high_complexity",
        "large_class",
        "poor_naming",
        "single_responsibility_violation",
        "tight_coupling",
        "duplication",
        "readability_issue",
    )


if __name__ == "__main__":
    obj = RefactoringAgent("openai/gpt-oss-20b")
    print(obj.get_code("app.py"))
