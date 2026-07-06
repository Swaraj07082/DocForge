from agents.base_agent import BaseReviewAgent


class ArchitectureAgent(BaseReviewAgent):
    agent_name = "architecture"
    role = "an Architecture Agent."
    focus = """Find:
- Layer violations
- High coupling
- God classes
- SRP violations"""
    finding_types = (
        "tight_coupling",
        "large_class",
        "single_responsibility_violation",
        "high_complexity",
        "poor_naming",
        "dead_code",
        "long_function",
        "duplicate_code",
        "duplication",
        "readability_issue",
    )


if __name__ == "__main__":
    obj = ArchitectureAgent("openai/gpt-oss-20b")
    print(obj.get_code("app.py"))
