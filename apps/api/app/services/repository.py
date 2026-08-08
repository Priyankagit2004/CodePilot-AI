import asyncio
import json
import logging
import shutil
import stat
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import APIException
from app.models.repository import RepositoryRecord
from app.schemas.repository import RepositoryResponse
from app.services.repository_intelligence import (
    RepositoryIntelligenceService,
)
from app.services.repository_knowledge import (
    RepositoryKnowledgeService,
)

logger = logging.getLogger(__name__)


LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".scala": "Scala",
    ".sql": "SQL",
    ".sh": "Shell",
    ".html": "HTML",
    ".css": "CSS",
}


class RepositoryService:
    """Local repository storage with safe, bounded ZIP extraction."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._storage_dir = (
            settings.repository_storage_dir.resolve()
        )
        self._max_upload_bytes = (
            settings.max_upload_size_mb * 1024 * 1024
        )
        self._max_extracted_bytes = (
            settings.max_extracted_size_mb * 1024 * 1024
        )
        self._max_archive_files = settings.max_archive_files

    async def upload(
        self,
        file: UploadFile,
    ) -> RepositoryResponse:
        self._validate_upload(file)

        project_id = uuid.uuid4().hex

        project_dir = self._storage_dir / project_id
        archive_path = project_dir / "source.zip"
        extracted_dir = project_dir / "source"

        project_dir.mkdir(
            parents=True,
            exist_ok=False,
        )

        try:
            archive_size = await self._write_upload(
                file,
                archive_path,
            )

            extracted_size, archive_file_count = (
                self._extract_safely(
                    archive_path,
                    extracted_dir,
                )
            )

            languages, source_file_count = (
                self._detect_languages(
                    extracted_dir
                )
            )

            if source_file_count == 0:
                raise APIException(
                    422,
                    "invalid_repository",
                    "The archive contains no supported source files.",
                )

            record = RepositoryRecord(
                project_id=project_id,
                name=Path(
                    file.filename or "repository.zip"
                ).stem,
                original_filename=(
                    file.filename or "repository.zip"
                ),
                created_at=datetime.now(UTC),
                archive_size_bytes=archive_size,
                extracted_size_bytes=extracted_size,
                file_count=archive_file_count,
                supported_languages=languages,
                storage_path=project_dir,
            )

            self._write_metadata(record)

            # Repository analysis is synchronous and can take a long
            # time for large repositories. Run it in a worker thread
            # so the FastAPI event loop remains responsive.
            await asyncio.to_thread(
                RepositoryIntelligenceService().analyze,
                record,
            )

            # Knowledge indexing is also potentially expensive.
            # Keep failures here from preventing the repository
            # itself from being uploaded successfully.
            try:
                await asyncio.to_thread(
                    RepositoryKnowledgeService(
                        self._settings
                    ).index,
                    record,
                )
            except Exception:
                logger.exception(
                    "repository_knowledge_indexing_failed",
                    extra={
                        "project_id": project_id,
                    },
                )

            return self._to_response(record)

        except Exception:
            shutil.rmtree(
                project_dir,
                ignore_errors=True,
            )
            raise

        finally:
            await file.close()

    def list_repositories(
        self,
    ) -> list[RepositoryResponse]:
        if not self._storage_dir.exists():
            return []

        records = [
            self._read_metadata(
                path / "metadata.json"
            )
            for path in self._storage_dir.iterdir()
            if path.is_dir()
        ]

        return sorted(
            (
                self._to_response(record)
                for record in records
                if record
            ),
            key=lambda item: item.created_at,
            reverse=True,
        )

    def get_repository(
        self,
        project_id: str,
    ) -> RepositoryResponse:
        return self._to_response(
            self.get_record(project_id)
        )

    def get_record(
        self,
        project_id: str,
    ) -> RepositoryRecord:
        record = self._read_metadata(
            self._storage_dir
            / project_id
            / "metadata.json"
        )

        if record is None:
            raise APIException(
                404,
                "repository_not_found",
                "Repository not found.",
            )

        return record

    def _validate_upload(
        self,
        file: UploadFile,
    ) -> None:
        if (
            not file.filename
            or Path(file.filename).suffix.lower()
            != ".zip"
        ):
            raise APIException(
                415,
                "unsupported_file_type",
                "Only ZIP archives are supported.",
            )

    async def _write_upload(
        self,
        file: UploadFile,
        destination: Path,
    ) -> int:
        written = 0

        with destination.open("wb") as output:
            while chunk := await file.read(
                1024 * 1024
            ):
                written += len(chunk)

                if written > self._max_upload_bytes:
                    raise APIException(
                        413,
                        "file_too_large",
                        "Archive exceeds the configured upload limit.",
                    )

                output.write(chunk)

        return written

    def _extract_safely(
        self,
        archive_path: Path,
        destination: Path,
    ) -> tuple[int, int]:
        try:
            with zipfile.ZipFile(
                archive_path
            ) as archive:
                members = archive.infolist()

                if not members:
                    raise APIException(
                        422,
                        "invalid_archive",
                        "The archive is empty.",
                    )

                if len(members) > self._max_archive_files:
                    raise APIException(
                        422,
                        "archive_too_large",
                        "Archive contains too many files.",
                    )

                extracted_size = sum(
                    member.file_size
                    for member in members
                    if not member.is_dir()
                )

                if (
                    extracted_size
                    > self._max_extracted_bytes
                ):
                    raise APIException(
                        422,
                        "archive_too_large",
                        "Archive expands beyond the configured limit.",
                    )

                destination.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                root = destination.resolve()

                for member in members:
                    if member.flag_bits & 0x1:
                        raise APIException(
                            422,
                            "unsupported_archive",
                            "Encrypted ZIP archives are not supported.",
                        )

                    target = (
                        destination
                        / member.filename
                    ).resolve()

                    try:
                        target.relative_to(root)

                    except ValueError as error:
                        raise APIException(
                            422,
                            "unsafe_archive",
                            "Archive contains an unsafe file path.",
                        ) from error

                    if stat.S_ISLNK(
                        member.external_attr >> 16
                    ):
                        raise APIException(
                            422,
                            "unsafe_archive",
                            "Archive contains symbolic links.",
                        )

                    if member.is_dir():
                        target.mkdir(
                            parents=True,
                            exist_ok=True,
                        )
                        continue

                    target.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    with archive.open(
                        member
                    ) as source, target.open(
                        "wb"
                    ) as output:
                        shutil.copyfileobj(
                            source,
                            output,
                        )

                return (
                    extracted_size,
                    sum(
                        not member.is_dir()
                        for member in members
                    ),
                )

        except zipfile.BadZipFile as error:
            raise APIException(
                422,
                "invalid_archive",
                "The uploaded file is not a valid ZIP archive.",
            ) from error

    def _detect_languages(
        self,
        source_dir: Path,
    ) -> tuple[list[str], int]:
        languages: set[str] = set()
        file_count = 0

        for path in source_dir.rglob("*"):
            if not path.is_file():
                continue

            language = LANGUAGE_BY_EXTENSION.get(
                path.suffix.lower()
            )

            if language:
                languages.add(language)
                file_count += 1

        return sorted(languages), file_count

    def _write_metadata(
        self,
        record: RepositoryRecord,
    ) -> None:
        payload = {
            "project_id": record.project_id,
            "name": record.name,
            "original_filename": (
                record.original_filename
            ),
            "created_at": record.created_at.isoformat(),
            "archive_size_bytes": (
                record.archive_size_bytes
            ),
            "extracted_size_bytes": (
                record.extracted_size_bytes
            ),
            "file_count": record.file_count,
            "supported_languages": (
                record.supported_languages
            ),
        }

        metadata_path = (
            record.storage_path
            / "metadata.json"
        )

        temporary_path = (
            metadata_path.with_suffix(".tmp")
        )

        temporary_path.write_text(
            json.dumps(
                payload,
                indent=2,
            ),
            encoding="utf-8",
        )

        temporary_path.replace(
            metadata_path
        )

    def _read_metadata(
        self,
        metadata_path: Path,
    ) -> RepositoryRecord | None:
        if not metadata_path.is_file():
            return None

        data = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        return RepositoryRecord(
            project_id=data["project_id"],
            name=data["name"],
            original_filename=data[
                "original_filename"
            ],
            created_at=datetime.fromisoformat(
                data["created_at"]
            ),
            archive_size_bytes=data[
                "archive_size_bytes"
            ],
            extracted_size_bytes=data[
                "extracted_size_bytes"
            ],
            file_count=data["file_count"],
            supported_languages=data[
                "supported_languages"
            ],
            storage_path=metadata_path.parent,
        )

    @staticmethod
    def _to_response(
        record: RepositoryRecord,
    ) -> RepositoryResponse:
        return RepositoryResponse(
            project_id=record.project_id,
            name=record.name,
            original_filename=(
                record.original_filename
            ),
            created_at=record.created_at,
            archive_size_bytes=(
                record.archive_size_bytes
            ),
            extracted_size_bytes=(
                record.extracted_size_bytes
            ),
            file_count=record.file_count,
            supported_languages=(
                record.supported_languages
            ),
        )