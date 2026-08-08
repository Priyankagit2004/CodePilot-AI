import re
from dataclasses import dataclass
from pathlib import Path

import tree_sitter_java as ts_java
import tree_sitter_javascript as ts_javascript
import tree_sitter_python as ts_python
import tree_sitter_typescript as ts_typescript
from tree_sitter import Language, Parser

from app.schemas.intelligence import (
    CodeSymbol,
    ImportReference,
    RestEndpoint,
    SourceLocation,
)


@dataclass(frozen=True)
class ParsedFile:
    language: str
    symbols: list[CodeSymbol]
    imports: list[ImportReference]
    comment_count: int
    rest_endpoints: list[RestEndpoint]


LANGUAGES = {
    ".py": ("Python", Language(ts_python.language())),
    ".java": ("Java", Language(ts_java.language())),
    ".js": ("JavaScript", Language(ts_javascript.language())),
    ".jsx": ("JavaScript", Language(ts_javascript.language())),
    ".ts": (
        "TypeScript",
        Language(ts_typescript.language_typescript()),
    ),
    ".tsx": (
        "TypeScript",
        Language(ts_typescript.language_tsx()),
    ),
}


SYMBOL_TYPES = {
    "Python": {
        "class_definition": "class",
        "function_definition": "function",
    },
    "Java": {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "method_declaration": "method",
    },
    "JavaScript": {
        "class_declaration": "class",
        "function_declaration": "function",
        "method_definition": "method",
    },
    "TypeScript": {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "function_declaration": "function",
        "method_definition": "method",
    },
}


IMPORT_TYPES = {
    "Python": {
        "import_statement",
        "import_from_statement",
    },
    "Java": {
        "import_declaration",
    },
    "JavaScript": {
        "import_statement",
    },
    "TypeScript": {
        "import_statement",
    },
}


class TreeSitterParserService:
    """
    Reusable Tree-sitter parser for CodePilot's supported
    source languages.
    """

    def parse_file(
        self,
        path: Path,
        repository_root: Path,
    ) -> ParsedFile | None:

        language_info = LANGUAGES.get(path.suffix.lower())

        if language_info is None:
            return None

        language_name, language = language_info

        source = path.read_bytes()

        parser = Parser(language)
        tree = parser.parse(source)

        relative_path = path.relative_to(
            repository_root
        ).as_posix()

        symbols: list[CodeSymbol] = []
        imports: list[ImportReference] = []
        comments = 0

        # IMPORTANT:
        # Use an iterative stack instead of recursive traversal.
        # This prevents Python recursion problems on very large
        # or deeply nested syntax trees.
        for node in self._walk(tree.root_node):

            if (
                node.type == "comment"
                or node.type.endswith("_comment")
            ):
                comments += 1

            kind = SYMBOL_TYPES[language_name].get(node.type)

            if kind:
                name = self._name_for_node(
                    node,
                    source,
                )

                if name:
                    symbols.append(
                        CodeSymbol(
                            name=name,
                            kind=kind,
                            location=self._location(
                                relative_path,
                                node,
                            ),
                        )
                    )

            if node.type in IMPORT_TYPES[language_name]:

                raw = self._text(
                    node,
                    source,
                ).strip()

                imports.append(
                    ImportReference(
                        module=self._module_from_import(raw),
                        raw=raw,
                        location=self._location(
                            relative_path,
                            node,
                        ),
                    )
                )

        self._set_symbol_parents(symbols)

        endpoints = self._extract_endpoints(
            source.decode(
                "utf-8",
                errors="replace",
            ),
            language_name,
            relative_path,
        )

        return ParsedFile(
            language=language_name,
            symbols=symbols,
            imports=imports,
            comment_count=comments,
            rest_endpoints=endpoints,
        )

    @staticmethod
    def _walk(node):
        """
        Iterative Tree-sitter tree traversal.

        We deliberately avoid recursive yield-from traversal
        because very large source trees can become extremely deep.
        """

        stack = [node]

        while stack:

            current = stack.pop()

            yield current

            children = current.children

            if children:
                stack.extend(reversed(children))

    @staticmethod
    def _text(
        node,
        source: bytes,
    ) -> str:

        return source[
            node.start_byte:node.end_byte
        ].decode(
            "utf-8",
            errors="replace",
        )

    def _name_for_node(
        self,
        node,
        source: bytes,
    ) -> str | None:

        name = node.child_by_field_name("name")

        if name is not None:
            return self._text(
                name,
                source,
            )

        for child in node.named_children:

            if child.type in {
                "identifier",
                "type_identifier",
                "property_identifier",
            }:

                return self._text(
                    child,
                    source,
                )

        return None

    @staticmethod
    def _location(
        file_path: str,
        node,
    ) -> SourceLocation:

        return SourceLocation(
            file_path=file_path,
            start_line=node.start_point.row + 1,
            end_line=node.end_point.row + 1,
        )

    @staticmethod
    def _module_from_import(
        raw: str,
    ) -> str:

        match = re.search(
            r"(?:from\s+|import\s+)([\w./@-]+)",
            raw,
        )

        return (
            match.group(1)
            if match
            else raw
        )

    @staticmethod
    def _set_symbol_parents(
        symbols: list[CodeSymbol],
    ) -> None:

        classes = [
            symbol
            for symbol in symbols
            if symbol.kind in {
                "class",
                "interface",
            }
        ]

        for symbol in symbols:

            if symbol.kind not in {
                "function",
                "method",
            }:
                continue

            for candidate in classes:

                if (
                    candidate.location.file_path
                    == symbol.location.file_path
                    and candidate.location.start_line
                    <= symbol.location.start_line
                    <= candidate.location.end_line
                ):

                    symbol.parent = candidate.name

                    break

    @staticmethod
    def _extract_endpoints(
        source: str,
        language: str,
        file_path: str,
    ) -> list[RestEndpoint]:

        endpoints: list[RestEndpoint] = []

        patterns = []

        if language == "Python":

            patterns.append(
                (
                    r"@(?:\w+\.)?"
                    r"(get|post|put|patch|delete|route)"
                    r"\(\s*['\"]([^'\"]+)",
                    "FastAPI/Flask",
                )
            )

        elif language == "Java":

            patterns.append(
                (
                    r"@(Get|Post|Put|Patch|Delete|Request)Mapping"
                    r"\s*\(\s*(?:value\s*=\s*)?"
                    r"['\"]?([^'\")]+)",
                    "Spring",
                )
            )

        else:

            patterns.append(
                (
                    r"\b(?:app|router)\."
                    r"(get|post|put|patch|delete)"
                    r"\(\s*['\"]([^'\"]+)",
                    "Express",
                )
            )

        for pattern, framework in patterns:

            for match in re.finditer(
                pattern,
                source,
                flags=re.IGNORECASE,
            ):

                line = (
                    source.count(
                        "\n",
                        0,
                        match.start(),
                    )
                    + 1
                )

                method = (
                    match.group(1)
                    .upper()
                    .replace(
                        "MAPPING",
                        "",
                    )
                )

                endpoints.append(
                    RestEndpoint(
                        method=method,
                        path=match.group(2),
                        framework=framework,
                        location=SourceLocation(
                            file_path=file_path,
                            start_line=line,
                            end_line=line,
                        ),
                    )
                )

        return endpoints


def parse_file_worker(
    path_string: str,
    repository_root_string: str,
) -> ParsedFile | None:
    """
    Parse one file inside a separate OS process.

    Tree-sitter uses native code. If a problematic source
    file causes a native crash, the worker process can die
    without killing the FastAPI server process.
    """

    parser = TreeSitterParserService()

    return parser.parse_file(
        Path(path_string),
        Path(repository_root_string),
    )