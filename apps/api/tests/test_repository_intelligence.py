from datetime import UTC, datetime
from pathlib import Path

from app.models.repository import RepositoryRecord
from app.services.repository_intelligence import RepositoryIntelligenceService


def test_intelligence_builds_hierarchy_statistics_and_metadata(tmp_path: Path) -> None:
    project = tmp_path / "project"
    source = project / "source" / "src"
    source.mkdir(parents=True)
    (source / "main.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    (project / "source" / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    record = RepositoryRecord("project-1", "sample", "sample.zip", datetime.now(UTC), 1, 1, 2, ["Python"], project)

    intelligence = RepositoryIntelligenceService().analyze(record)

    assert intelligence.total_files == 2
    assert intelligence.language_statistics == {"Python": 1}
    assert intelligence.configuration_files == ["requirements.txt"]
    assert "FastAPI" in intelligence.frameworks
    assert (project / "intelligence.json").is_file()
