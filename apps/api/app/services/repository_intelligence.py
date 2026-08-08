from concurrent.futures import (
    ProcessPoolExecutor,
    TimeoutError,
)
from datetime import UTC, datetime
from pathlib import Path

from app.models.repository import RepositoryRecord
from app.parser.tree_sitter_service import (
    ParsedFile,
    parse_file_worker,
)
from app.schemas.intelligence import (
    FileInfo,
    FolderNode,
    GraphEdge,
    RepositoryIntelligence,
)


IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
}


CONFIGURATION_FILENAMES = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "pom.xml",
    "application.yml",
    "application.yaml",
    ".env",
    "tsconfig.json",
    "vite.config.ts",
    "vite.config.js",
}


class RepositoryIntelligenceService:
    """
    Builds a persisted, structured repository map for later RAG use.

    Tree-sitter parsing is performed in separate worker processes so
    that a native crash in Tree-sitter cannot bring down the FastAPI
    server.
    """

    PARSE_TIMEOUT_SECONDS = 30

    def analyze(
        self,
        record: RepositoryRecord,
    ) -> RepositoryIntelligence:

        source_dir = record.storage_path / "source"

        files: list[FileInfo] = []
        language_statistics: dict[str, int] = {}
        configuration_files: list[str] = []
        frameworks: set[str] = set()

        # Collect files first so we can process them using a single
        # process pool instead of creating a new process for every file.
        source_files = list(
            self._iter_files(source_dir)
        )

        # A small pool is intentional. Tree-sitter uses native code
        # and each worker is isolated from the FastAPI process.
        max_workers = min(
            4,
            max(1, len(source_files)),
        )

        with ProcessPoolExecutor(
            max_workers=max_workers
        ) as executor:

            futures = []

            for path in source_files:

                relative_path = (
                    path.relative_to(
                        source_dir
                    ).as_posix()
                )

                is_configuration = (
                    path.name
                    in CONFIGURATION_FILENAMES
                )

                if is_configuration:
                    configuration_files.append(
                        relative_path
                    )

                    frameworks.update(
                        self._detect_frameworks(
                            path
                        )
                    )

                future = executor.submit(
                    parse_file_worker,
                    str(path),
                    str(source_dir),
                )

                futures.append(
                    (
                        path,
                        relative_path,
                        is_configuration,
                        future,
                    )
                )

            for (
                path,
                relative_path,
                is_configuration,
                future,
            ) in futures:

                parsed = self._get_parsed_result(
                    future
                )

                if parsed is None:

                    files.append(
                        FileInfo(
                            path=relative_path,
                            size_bytes=path.stat().st_size,
                            comment_count=0,
                            is_configuration=(
                                is_configuration
                            ),
                        )
                    )

                    continue

                language_statistics[
                    parsed.language
                ] = (
                    language_statistics.get(
                        parsed.language,
                        0,
                    )
                    + 1
                )

                if parsed.rest_endpoints:

                    frameworks.update(
                        endpoint.framework
                        for endpoint
                        in parsed.rest_endpoints
                    )

                files.append(
                    FileInfo(
                        path=relative_path,
                        language=parsed.language,
                        size_bytes=path.stat().st_size,
                        imports=parsed.imports,
                        symbols=parsed.symbols,
                        comment_count=(
                            parsed.comment_count
                        ),
                        rest_endpoints=(
                            parsed.rest_endpoints
                        ),
                        is_configuration=(
                            is_configuration
                        ),
                    )
                )

        relationships, dependencies = (
            self._build_graphs(files)
        )

        intelligence = RepositoryIntelligence(
            project_id=record.project_id,
            generated_at=datetime.now(UTC),
            folder_hierarchy=(
                self._folder_hierarchy(
                    source_dir
                )
            ),
            files=files,
            file_relationship_graph=relationships,
            dependency_graph=dependencies,
            language_statistics=(
                language_statistics
            ),
            frameworks=sorted(frameworks),
            configuration_files=sorted(
                configuration_files
            ),
            total_files=len(files),
        )

        self._write_intelligence(
            record.storage_path,
            intelligence,
        )

        return intelligence

    @classmethod
    def _get_parsed_result(
        cls,
        future,
    ) -> ParsedFile | None:
        """
        Safely retrieve a worker result.

        If Tree-sitter crashes inside a worker, times out,
        or raises another exception, return None instead
        of allowing repository analysis to fail.
        """

        try:
            return future.result(
                timeout=cls.PARSE_TIMEOUT_SECONDS
            )

        except TimeoutError:
            future.cancel()
            return None

        except Exception:
            return None

    def load(
        self,
        record: RepositoryRecord,
    ) -> RepositoryIntelligence | None:

        path = (
            record.storage_path
            / "intelligence.json"
        )

        if not path.is_file():
            return None

        return (
            RepositoryIntelligence
            .model_validate_json(
                path.read_text(
                    encoding="utf-8"
                )
            )
        )

    @staticmethod
    def _iter_files(root: Path):

        if not root.exists():
            return

        for path in root.rglob("*"):

            if any(
                part in IGNORED_DIRECTORIES
                for part
                in path.relative_to(
                    root
                ).parts
            ):
                continue

            if path.is_file():
                yield path

    @staticmethod
    def _folder_hierarchy(
        root: Path,
    ) -> FolderNode:

        def build(
            directory: Path,
        ) -> FolderNode:

            relative = (
                directory.relative_to(
                    root
                ).as_posix()
                if directory != root
                else "."
            )

            folders = [
                build(child)
                for child in sorted(
                    directory.iterdir()
                )
                if (
                    child.is_dir()
                    and child.name
                    not in IGNORED_DIRECTORIES
                )
            ]

            files = [
                child.relative_to(
                    root
                ).as_posix()
                for child in sorted(
                    directory.iterdir()
                )
                if child.is_file()
            ]

            return FolderNode(
                name=(
                    directory.name
                    if directory != root
                    else "root"
                ),
                path=relative,
                folders=folders,
                files=files,
            )

        return build(root)

    @staticmethod
    def _detect_frameworks(
        path: Path,
    ) -> set[str]:

        content = path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).lower()

        signatures = {
            "fastapi": "FastAPI",
            "flask": "Flask",
            "django": "Django",
            "spring-boot": "Spring Boot",
            "org.springframework": "Spring",
            "express": "Express",
            "@nestjs": "NestJS",
            "react": "React",
            "next": "Next.js",
        }

        return {
            framework
            for signature, framework
            in signatures.items()
            if signature in content
        }

    @staticmethod
    def _build_graphs(
        files: list[FileInfo],
    ) -> tuple[
        list[GraphEdge],
        list[GraphEdge],
    ]:

        paths = {
            file.path
            for file in files
        }

        relationships: list[GraphEdge] = []
        dependencies: list[GraphEdge] = []

        for file in files:

            for reference in file.imports:

                dependencies.append(
                    GraphEdge(
                        source=file.path,
                        target=reference.module,
                        relationship="imports",
                    )
                )

                target = (
                    RepositoryIntelligenceService
                    ._resolve_internal_import(
                        file.path,
                        reference.module,
                        paths,
                    )
                )

                if target:

                    relationships.append(
                        GraphEdge(
                            source=file.path,
                            target=target,
                            relationship="imports",
                        )
                    )

        return (
            relationships,
            dependencies,
        )

    @staticmethod
    def _resolve_internal_import(
        source: str,
        module: str,
        paths: set[str],
    ) -> str | None:

        normalized = (
            module
            .replace(".", "/")
            .lstrip("/")
        )

        for path in paths:

            stem = (
                str(
                    Path(path).with_suffix("")
                )
                .replace("\\", "/")
            )

            if (
                normalized == stem
                or path.endswith(
                    f"/{normalized}.py"
                )
                or path.endswith(
                    f"/{normalized}.ts"
                )
                or path.endswith(
                    f"/{normalized}.java"
                )
            ):
                return path

        return None

    @staticmethod
    def _write_intelligence(
        storage_path: Path,
        intelligence: RepositoryIntelligence,
    ) -> None:

        output = (
            storage_path
            / "intelligence.json"
        )

        temporary = (
            output.with_suffix(".tmp")
        )

        temporary.write_text(
            intelligence.model_dump_json(
                indent=2
            ),
            encoding="utf-8",
        )

        temporary.replace(output)