from langchain_core.prompts import ChatPromptTemplate

BASE_SYSTEM = """You are CodePilot AI, an expert software-engineering assistant. Answer only from the supplied repository context. Be concise, technically precise, and cite file paths in backticks. If the context is insufficient, say so clearly. Do not invent files, symbols, or behavior."""

PROMPT_TEMPLATES: dict[str, ChatPromptTemplate] = {
    "repository-summary": ChatPromptTemplate.from_messages([("system", BASE_SYSTEM), ("human", "Summarize repository `{project_id}`: its purpose, primary languages, key modules, and important dependencies.\n\nContext:\n{context}")]),
    "architecture-explanation": ChatPromptTemplate.from_messages([("system", BASE_SYSTEM), ("human", "Explain the architecture of repository `{project_id}`, including component responsibilities and data or dependency flow.\n\nContext:\n{context}")]),
    "explain-file": ChatPromptTemplate.from_messages([("system", BASE_SYSTEM), ("human", "Explain file `{file_path}` in repository `{project_id}`: its responsibility, main symbols, and dependencies.\n\nContext:\n{context}")]),
    "explain-function": ChatPromptTemplate.from_messages([("system", BASE_SYSTEM), ("human", "Explain function or method `{question}` in repository `{project_id}`. Cover inputs, outputs, side effects, and callers only when the context supports it.\n\nContext:\n{context}")]),
    "code-review": ChatPromptTemplate.from_messages([("system", BASE_SYSTEM), ("human", "Review the supplied repository context for correctness, maintainability, readability, and testability. Prioritize findings by impact and propose concrete changes.\n\nFocus: {question}\n\nContext:\n{context}")]),
    "bug-detection": ChatPromptTemplate.from_messages([("system", BASE_SYSTEM), ("human", "Identify likely bugs or edge cases in the supplied context. Explain evidence, impact, and a safe fix. Do not claim certainty without evidence.\n\nFocus: {question}\n\nContext:\n{context}")]),
    "refactoring-suggestions": ChatPromptTemplate.from_messages([("system", BASE_SYSTEM), ("human", "Suggest focused refactorings for the supplied context. Explain tradeoffs, migration steps, and expected benefits.\n\nFocus: {question}\n\nContext:\n{context}")]),
    "documentation-generation": ChatPromptTemplate.from_messages([("system", BASE_SYSTEM), ("human", "Draft concise developer documentation for the supplied repository context. Include purpose, usage, interfaces, and caveats that are supported by context.\n\nFocus: {question}\n\nContext:\n{context}")]),
    "security-analysis": ChatPromptTemplate.from_messages([("system", BASE_SYSTEM), ("human", "Perform a security-focused review of the supplied context. Identify vulnerabilities, insecure practices, evidence, impact, and remediations.\n\nFocus: {question}\n\nContext:\n{context}")]),
    "testing-generation": ChatPromptTemplate.from_messages([("system", BASE_SYSTEM), ("human", "Propose unit tests and edge cases for the supplied context. Provide focused test cases or test code only where the context supports it.\n\nFocus: {question}\n\nContext:\n{context}")]),
    "onboarding": ChatPromptTemplate.from_messages([("system", BASE_SYSTEM), ("human", "Create a practical onboarding guide for a developer who is new to repository `{project_id}`. Use these exact Markdown sections: Repository overview; Folder structure explanation; Entry points; Application flow; Important classes; Important services; API overview; Suggested reading order; Technologies used; Common developer workflow. If context does not support a section, say what is unknown rather than guessing.\n\nNew developer's focus: {question}\n\nContext:\n{context}")]),
}


def render_prompt(template_name: str, **values: str) -> str:
    """Render a named prompt while keeping templates independent of services."""

    messages = PROMPT_TEMPLATES[template_name].format_messages(**values)
    return "\n\n".join(str(message.content) for message in messages)
