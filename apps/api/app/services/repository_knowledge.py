import json
import re
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

from app.core.config import Settings
from app.core.exceptions import APIException
from app.models.repository import RepositoryRecord
from app.schemas.knowledge import (
    KnowledgeAnswerResponse,
    KnowledgeIndexResponse,
    KnowledgeSearchResponse,
    RetrievedContext,
)
from app.services.repository_intelligence import (
    CONFIGURATION_FILENAMES,
    IGNORED_DIRECTORIES,
)


LANGUAGE_BY_EXTENSION = {
    ".py": ("Python", Language.PYTHON),
    ".java": ("Java", Language.JAVA),
    ".js": ("JavaScript", Language.JS),
    ".jsx": ("JavaScript", Language.JS),
    ".ts": ("TypeScript", Language.TS),
    ".tsx": ("TypeScript", Language.TS),
}


class RepositoryKnowledgeService:
    """Chunks, embeds, persists, and retrieves repository context locally."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    # ------------------------------------------------------------------
    # INDEXING
    # ------------------------------------------------------------------

    def index(self, record: RepositoryRecord) -> KnowledgeIndexResponse:
        documents = self._build_documents(
            record.storage_path / "source"
        )

        if not documents:
            raise APIException(
                422,
                "no_indexable_content",
                "Repository has no indexable source or configuration files.",
            )

        store = self._vector_store(
            record.project_id,
            recreate=True,
        )

        store.add_documents(
            documents,
            ids=[
                document.metadata["chunk_id"]
                for document in documents
            ],
        )

        marker = record.storage_path / "knowledge.json"

        marker.write_text(
            json.dumps(
                {
                    "project_id": record.project_id,
                    "chunks_indexed": len(documents),
                }
            ),
            encoding="utf-8",
        )

        return KnowledgeIndexResponse(
            project_id=record.project_id,
            chunks_indexed=len(documents),
        )

    # ------------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------------

    def search(
        self,
        record: RepositoryRecord,
        question: str,
        limit: int,
    ) -> KnowledgeSearchResponse:
        self._ensure_indexed(record)

        root = record.storage_path / "source"

        # --------------------------------------------------------------
        # 1. Semantic vector search
        # --------------------------------------------------------------

        vector_matches = (
            self._vector_store(
                record.project_id
            ).similarity_search_with_relevance_scores(
                question,
                k=max(limit * 2, 8),
            )
        )

        results: list[RetrievedContext] = []

        for document, score in vector_matches:
            results.append(
                RetrievedContext(
                    file_path=document.metadata["file_path"],
                    chunk_id=document.metadata["chunk_id"],
                    content=document.page_content,
                    relevance_score=round(score, 4),
                )
            )

        # --------------------------------------------------------------
        # 2. Direct repository search
        #
        # This is important for questions such as:
        #
        #   "Show me class APIRoute"
        #   "Explain APIRoute.__init__"
        #   "Find fastapi/routing.py"
        #
        # Vector search alone can miss exact symbols.
        # --------------------------------------------------------------

        direct_results = self._direct_repository_search(
            root=root,
            question=question,
            limit=limit,
        )

        # --------------------------------------------------------------
        # 3. Merge direct + semantic results
        #
        # Direct matches are placed first because they are exact
        # repository matches rather than semantic guesses.
        # --------------------------------------------------------------

        combined: list[RetrievedContext] = []
        seen: set[tuple[str, str]] = set()

        for result in direct_results + results:
            key = (
                result.file_path,
                result.content[:300],
            )

            if key in seen:
                continue

            seen.add(key)
            combined.append(result)

            if len(combined) >= limit:
                break

        return KnowledgeSearchResponse(
            project_id=record.project_id,
            results=combined,
        )

    # ------------------------------------------------------------------
    # ANSWER
    # ------------------------------------------------------------------

    def answer(
        self,
        record: RepositoryRecord,
        question: str,
        limit: int,
    ) -> KnowledgeAnswerResponse:
        search = self.search(
            record,
            question,
            limit,
        )

        return KnowledgeAnswerResponse(
            project_id=record.project_id,
            question=question,
            answer=self._format_answer(search.results),
            context=search.results,
        )

    # ------------------------------------------------------------------
    # DIRECT SEARCH
    # ------------------------------------------------------------------

    def _direct_repository_search(
        self,
        root: Path,
        question: str,
        limit: int,
    ) -> list[RetrievedContext]:
        """
        Performs lightweight exact matching against repository files.

        This complements vector search.

        Examples:

            "class APIRoute"
            "APIRoute.__init__"
            "fastapi/routing.py"
            "Explain routing.py"
        """

        if not root.exists():
            return []

        normalized_question = question.lower()

        requested_file = self._extract_file_path(
            question
        )

        requested_symbol = self._extract_symbol(
            question
        )

        candidates: list[tuple[int, Path]] = []

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            relative = path.relative_to(root)

            if any(
                part in IGNORED_DIRECTORIES
                for part in relative.parts
            ):
                continue

            language = LANGUAGE_BY_EXTENSION.get(
                path.suffix.lower()
            )

            if (
                language is None
                and path.name not in CONFIGURATION_FILENAMES
            ):
                continue

            relative_path = relative.as_posix()

            score = 0

            # ----------------------------------------------------------
            # Exact file path match
            # ----------------------------------------------------------

            if requested_file:
                requested_normalized = (
                    requested_file
                    .replace("\\", "/")
                    .lower()
                    .lstrip("./")
                )

                candidate_normalized = (
                    relative_path
                    .replace("\\", "/")
                    .lower()
                )

                if (
                    candidate_normalized
                    == requested_normalized
                ):
                    score += 100

                elif candidate_normalized.endswith(
                    requested_normalized
                ):
                    score += 80

            # ----------------------------------------------------------
            # Filename mentioned in question
            # ----------------------------------------------------------

            filename = path.name.lower()

            if filename in normalized_question:
                score += 60

            # Example:
            #
            # "fastapi/routing.py"
            #
            # should strongly prefer routing.py.

            if (
                path.stem.lower()
                in normalized_question
            ):
                score += 25

            # ----------------------------------------------------------
            # Symbol match
            # ----------------------------------------------------------

            if requested_symbol:
                try:
                    content = path.read_text(
                        encoding="utf-8",
                        errors="ignore",
                    )
                except OSError:
                    continue

                if re.search(
                    self._symbol_regex(
                        requested_symbol
                    ),
                    content,
                    flags=re.MULTILINE,
                ):
                    score += 100

            if score > 0:
                candidates.append(
                    (score, path)
                )

        candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        results: list[RetrievedContext] = []

        for score, path in candidates[:limit]:
            try:
                content = path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            except OSError:
                continue

            relative_path = path.relative_to(
                root
            ).as_posix()

            # ----------------------------------------------------------
            # If a symbol was requested, return the source surrounding
            # that symbol.
            # ----------------------------------------------------------

            if requested_symbol:
                extracted = self._extract_symbol_context(
                    content,
                    requested_symbol,
                )
            else:
                extracted = self._extract_file_context(
                    content,
                )

            if not extracted.strip():
                continue

            chunk_id = str(
                uuid5(
                    NAMESPACE_URL,
                    f"direct:{relative_path}:{requested_symbol or ''}:{extracted}",
                )
            )

            results.append(
                RetrievedContext(
                    file_path=relative_path,
                    chunk_id=chunk_id,
                    content=extracted,
                    relevance_score=1.0,
                )
            )

        return results

    # ------------------------------------------------------------------
    # FILE PATH EXTRACTION
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_file_path(
        question: str,
    ) -> str | None:
        """
        Extract likely source paths from natural language.

        Examples:

            fastapi/routing.py
            routing.py
            fastapi\\routing.py
        """

        normalized = question.replace(
            "\\",
            "/",
        )

        patterns = [
            r"[\w./-]+\.py",
            r"[\w./-]+\.java",
            r"[\w./-]+\.js",
            r"[\w./-]+\.jsx",
            r"[\w./-]+\.ts",
            r"[\w./-]+\.tsx",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                normalized,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(0)

        return None

    # ------------------------------------------------------------------
    # SYMBOL EXTRACTION
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_symbol(
        question: str,
    ) -> str | None:
        """
        Extract likely Python/Java/JS/TS symbols.

        Examples:

            APIRoute
            __init__
            APIRoute.__init__
            class APIRoute
        """

        # APIRoute.__init__
        qualified_match = re.search(
            r"\b([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+)\b",
            question,
        )

        if qualified_match:
            value = qualified_match.group(1)

            # Return the most specific component.
            return value.split(".")[-1]

        # class APIRoute
        class_match = re.search(
            r"\bclass\s+([A-Za-z_]\w*)",
            question,
            flags=re.IGNORECASE,
        )

        if class_match:
            return class_match.group(1)

        # function __init__
        function_match = re.search(
            r"\b(?:function|method|function\s+named|method\s+named)?\s*"
            r"(__[A-Za-z0-9_]+__|[A-Za-z_]\w*)\s*"
            r"(?:function|method)?\b",
            question,
            flags=re.IGNORECASE,
        )

        if function_match:
            candidate = function_match.group(1)

            # Avoid treating ordinary words as symbols.
            if (
                candidate.startswith("__")
                or candidate[:1].isupper()
                or candidate in {
                    "APIRoute",
                    "APIRouter",
                    "FastAPI",
                }
            ):
                return candidate

        # Explicit common CamelCase/class-looking symbol.
        camel_match = re.search(
            r"\b[A-Z][A-Za-z0-9_]+\b",
            question,
        )

        if camel_match:
            return camel_match.group(0)

        return None

    # ------------------------------------------------------------------
    # SYMBOL REGEX
    # ------------------------------------------------------------------

    @staticmethod
    def _symbol_regex(
        symbol: str,
    ) -> str:
        escaped = re.escape(symbol)

        return (
            rf"(?:"
            rf"class\s+{escaped}\b"
            rf"|def\s+{escaped}\s*\("
            rf"|async\s+def\s+{escaped}\s*\("
            rf"|function\s+{escaped}\s*\("
            rf"|{escaped}\s*=\s*function"
            rf"|{escaped}\s*:"
            rf")"
        )

    # ------------------------------------------------------------------
    # SYMBOL CONTEXT
    # ------------------------------------------------------------------

    @classmethod
    def _extract_symbol_context(
        cls,
        content: str,
        symbol: str,
    ) -> str:
        """
        Return exact source lines surrounding a requested symbol.

        No rewriting or summarization happens here.
        """

        lines = content.splitlines()

        regex = re.compile(
            cls._symbol_regex(symbol),
            flags=re.MULTILINE,
        )

        start_line = None

        current_offset = 0

        for index, line in enumerate(lines):
            match = regex.search(
                line
            )

            if match:
                start_line = index
                break

            current_offset += len(line) + 1

        if start_line is None:
            # Fallback: search for the raw symbol.
            for index, line in enumerate(lines):
                if re.search(
                    rf"\b{re.escape(symbol)}\b",
                    line,
                ):
                    start_line = index
                    break

        if start_line is None:
            return ""

        # Include some lines before the definition so decorators,
        # comments, and annotations are preserved.
        begin = max(
            0,
            start_line - 8,
        )

        # Include enough source after the definition to capture the
        # class/function body without dumping an entire huge file.
        end = min(
            len(lines),
            start_line + 140,
        )

        selected = lines[begin:end]

        header = (
            f"# Exact repository source: lines "
            f"{begin + 1}-{end}\n"
        )

        return (
            header
            + "\n".join(selected)
        )

    # ------------------------------------------------------------------
    # FILE CONTEXT
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_file_context(
        content: str,
    ) -> str:
        """
        Return a bounded exact source excerpt for a directly requested
        file.
        """

        lines = content.splitlines()

        if len(lines) <= 180:
            return content

        return "\n".join(
            lines[:180]
        )

    # ------------------------------------------------------------------
    # VECTOR STORE
    # ------------------------------------------------------------------

    def _vector_store(
        self,
        project_id: str,
        recreate: bool = False,
    ) -> Chroma:
        persist_directory = (
            self._settings.chroma_storage_dir.resolve()
        )

        persist_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        collection_name = (
            f"repository_{project_id}"
        )

        embeddings = HuggingFaceEmbeddings(
            model_name=self._settings.embedding_model_name
        )

        store = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(
                persist_directory
            ),
        )

        if recreate:
            try:
                store.delete_collection()
            except ValueError:
                pass

            store = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=str(
                    persist_directory
                ),
            )

        return store

    # ------------------------------------------------------------------
    # DOCUMENT BUILDING
    # ------------------------------------------------------------------

    def _build_documents(
        self,
        root: Path,
    ) -> list[Document]:
        documents: list[Document] = []

        if not root.exists():
            return documents

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            relative_parts = (
                path.relative_to(root).parts
            )

            if any(
                part in IGNORED_DIRECTORIES
                for part in relative_parts
            ):
                continue

            language = LANGUAGE_BY_EXTENSION.get(
                path.suffix.lower()
            )

            if (
                language is None
                and path.name not in CONFIGURATION_FILENAMES
            ):
                continue

            try:
                content = path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            except OSError:
                continue

            if (
                not content.strip()
                or "\x00" in content
            ):
                continue

            relative_path = (
                path.relative_to(root)
                .as_posix()
            )

            splitter = self._splitter(
                language[1]
                if language
                else None
            )

            split_documents = (
                splitter.create_documents(
                    [content],
                    metadatas=[
                        {
                            "file_path": relative_path,
                            "language": (
                                language[0]
                                if language
                                else "Configuration"
                            ),
                        }
                    ],
                )
            )

            for index, document in enumerate(
                split_documents
            ):
                document.metadata[
                    "chunk_id"
                ] = str(
                    uuid5(
                        NAMESPACE_URL,
                        (
                            f"{relative_path}:"
                            f"{index}:"
                            f"{document.page_content}"
                        ),
                    )
                )

                document.metadata[
                    "chunk_index"
                ] = index

            documents.extend(
                split_documents
            )

        return documents

    # ------------------------------------------------------------------
    # SPLITTER
    # ------------------------------------------------------------------

    @staticmethod
    def _splitter(
        language: Language | None,
    ) -> RecursiveCharacterTextSplitter:
        if language is not None:
            return RecursiveCharacterTextSplitter.from_language(
                language,
                chunk_size=1_500,
                chunk_overlap=180,
            )

        return RecursiveCharacterTextSplitter(
            chunk_size=1_500,
            chunk_overlap=180,
        )

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_indexed(
        record: RepositoryRecord,
    ) -> None:
        if not (
            record.storage_path
            / "knowledge.json"
        ).is_file():
            raise APIException(
                409,
                "knowledge_not_indexed",
                "Repository knowledge has not been indexed. Build the knowledge index first.",
            )

    # ------------------------------------------------------------------
    # FALLBACK ANSWER
    # ------------------------------------------------------------------

    @staticmethod
    def _format_answer(
        results: list[RetrievedContext],
    ) -> str:
        if not results:
            return (
                "No relevant repository context "
                "was found for this question."
            )

        excerpts = [
            f"[{item.file_path}]\n{item.content}"
            for item in results
        ]

        return (
            "Retrieved repository context relevant "
            "to your question:\n\n"
            + "\n\n---\n\n".join(excerpts)
        )