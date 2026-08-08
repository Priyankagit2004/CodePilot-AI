from datetime import datetime

from pydantic import BaseModel, Field


class SourceLocation(BaseModel):
    file_path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)


class CodeSymbol(BaseModel):
    name: str
    kind: str
    location: SourceLocation
    parent: str | None = None


class ImportReference(BaseModel):
    module: str
    raw: str
    location: SourceLocation


class RestEndpoint(BaseModel):
    method: str
    path: str
    framework: str
    location: SourceLocation


class FileInfo(BaseModel):
    path: str
    language: str | None = None
    size_bytes: int = Field(ge=0)
    imports: list[ImportReference] = []
    symbols: list[CodeSymbol] = []
    comment_count: int = Field(default=0, ge=0)
    rest_endpoints: list[RestEndpoint] = []
    is_configuration: bool = False


class FolderNode(BaseModel):
    name: str
    path: str
    folders: list["FolderNode"] = []
    files: list[str] = []


class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str


class RepositoryIntelligence(BaseModel):
    project_id: str
    generated_at: datetime
    folder_hierarchy: FolderNode
    files: list[FileInfo]
    file_relationship_graph: list[GraphEdge]
    dependency_graph: list[GraphEdge]
    language_statistics: dict[str, int]
    frameworks: list[str]
    configuration_files: list[str]
    total_files: int
