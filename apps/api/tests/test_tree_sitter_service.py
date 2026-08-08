from pathlib import Path

from app.parser.tree_sitter_service import TreeSitterParserService


def test_python_parser_extracts_symbols_imports_comments_and_endpoints(tmp_path: Path) -> None:
    source = tmp_path / "routes.py"
    source.write_text(
        "# API routes\nfrom fastapi import FastAPI\napp = FastAPI()\n\nclass Service:\n    def run(self):\n        pass\n\n@app.get('/health')\ndef health():\n    return {'status': 'ok'}\n",
        encoding="utf-8",
    )

    parsed = TreeSitterParserService().parse_file(source, tmp_path)

    assert parsed is not None
    assert parsed.language == "Python"
    assert {symbol.name for symbol in parsed.symbols} >= {"Service", "run", "health"}
    assert parsed.imports[0].module == "fastapi"
    assert parsed.comment_count == 1
    assert parsed.rest_endpoints[0].path == "/health"


def test_typescript_parser_extracts_interface_and_function(tmp_path: Path) -> None:
    source = tmp_path / "client.ts"
    source.write_text("import axios from 'axios'\ninterface Client { run(): void }\nexport function fetchData() {}\n", encoding="utf-8")

    parsed = TreeSitterParserService().parse_file(source, tmp_path)

    assert parsed is not None
    assert parsed.language == "TypeScript"
    assert {symbol.name for symbol in parsed.symbols} >= {"Client", "fetchData"}
