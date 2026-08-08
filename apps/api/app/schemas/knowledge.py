from pydantic import BaseModel, Field


class KnowledgeIndexResponse(BaseModel):
    project_id: str
    chunks_indexed: int = Field(ge=0)
    status: str = "ready"


class KnowledgeQuery(BaseModel):
    question: str = Field(min_length=2, max_length=2_000)
    limit: int = Field(default=5, ge=1, le=10)


class RetrievedContext(BaseModel):
    file_path: str
    chunk_id: str
    content: str
    relevance_score: float | None = None


class KnowledgeSearchResponse(BaseModel):
    project_id: str
    results: list[RetrievedContext]


class KnowledgeAnswerResponse(BaseModel):
    project_id: str
    question: str
    answer: str
    context: list[RetrievedContext]
