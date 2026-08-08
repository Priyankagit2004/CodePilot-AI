from app.agents.orchestrator import PlannerAgent


def test_planner_selects_security_and_review_agents_for_security_review() -> None:
    selected = PlannerAgent().plan("Review this repository for security vulnerabilities and code quality bugs.")

    assert "repository_analysis" in selected
    assert "security" in selected
    assert "code_review" in selected


def test_planner_defaults_to_full_specialist_suite_for_ambiguous_requests() -> None:
    selected = PlannerAgent().plan("Help me understand this project.")

    assert set(selected) == {"repository_analysis", "architecture", "code_review", "security", "documentation", "testing"}
