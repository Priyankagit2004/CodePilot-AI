from app.agents.prompts import PROMPT_TEMPLATES, render_prompt


def test_all_requested_prompt_templates_are_present() -> None:
    assert set(PROMPT_TEMPLATES) == {
        "repository-summary", "architecture-explanation", "explain-file", "explain-function",
        "code-review", "bug-detection", "refactoring-suggestions", "documentation-generation",
    }


def test_prompt_rendering_keeps_repository_context() -> None:
    prompt = render_prompt("explain-file", project_id="project-1", file_path="src/app.py", question="", context="File: src/app.py\ndef run(): pass")

    assert "src/app.py" in prompt
    assert "def run" in prompt
