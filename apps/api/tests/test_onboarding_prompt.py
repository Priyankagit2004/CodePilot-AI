from app.agents.prompts import render_prompt


def test_onboarding_prompt_requires_all_new_developer_sections() -> None:
    prompt = render_prompt("onboarding", project_id="project-1", question="I'm new", file_path="", context="File: README.md")

    for heading in ("Repository overview", "Folder structure explanation", "Entry points", "Application flow", "Important classes", "Important services", "API overview", "Suggested reading order", "Technologies used", "Common developer workflow"):
        assert heading in prompt
