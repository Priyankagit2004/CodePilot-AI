from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class RepositoryRecord:
    project_id: str
    name: str
    original_filename: str
    created_at: datetime
    archive_size_bytes: int
    extracted_size_bytes: int
    file_count: int
    supported_languages: list[str]
    storage_path: Path
