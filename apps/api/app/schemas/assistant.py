from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.knowledge import RetrievedContext

AssistantTask = Literal["repository-summary", "architecture-explanation", "explain-file", "explain-function", "code-review", "bug-detection", "refactoring-suggestions", "documentation-generation", "security-analysis", "testing-generation", "onboarding"]


class AssistantRequest(BaseModel):
    question: str = Field(default="", max_length=2_000)
    file_path: str = Field(default="", max_length=1_000)
    context_limit: int = Field(default=5, ge=1, le=10)


class AssistantResponse(BaseModel):
    project_id: str
    task: AssistantTask
    answer: str
    context: list[RetrievedContext]
