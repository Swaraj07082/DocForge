from agents.base_agent import BaseReviewAgent


class TestAgent(BaseReviewAgent):
    agent_name = "testing"
    role = "a Testing Agent."
    focus = """Identify:
- Missing tests
- Edge cases not covered
- Untested branches
- Insufficient test coverage for critical paths"""
    finding_types = (
        "missing_test",
        "untested_branch",
        "missing_edge_case",
        "insufficient_test_coverage",
    )


if __name__ == "__main__":
    obj = TestAgent("openai/gpt-oss-20b")
    print(obj.get_code("app.py"))
