from pydantic import BaseModel, Field

from app.schemas.knowledge import RetrievedContext


class OnboardingRequest(BaseModel):
    question: str = Field(default="I'm new to this repository.", min_length=2, max_length=2_000)
    context_limit: int = Field(default=8, ge=3, le=10)


class OnboardingResponse(BaseModel):
    project_id: str
    guide: str
    context: list[RetrievedContext]
