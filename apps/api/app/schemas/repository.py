from datetime import datetime

from pydantic import BaseModel, Field


class RepositoryResponse(BaseModel):
    project_id: str
    name: str
    original_filename: str
    created_at: datetime
    archive_size_bytes: int = Field(ge=0)
    extracted_size_bytes: int = Field(ge=0)
    file_count: int = Field(ge=0)
    supported_languages: list[str]
    status: str = "ready"


class RepositoryListResponse(BaseModel):
    repositories: list[RepositoryResponse]
