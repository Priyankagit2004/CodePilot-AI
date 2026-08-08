from app.models.repository import RepositoryRecord
from app.schemas.dashboard import ArchitectureDiagram, DashboardInsight, DiagramNode, LanguageDistribution, RepositoryDashboard, RepositoryStatistics, ScoreCard, TimelineEvent
from app.schemas.intelligence import GraphEdge
from app.services.repository_intelligence import RepositoryIntelligenceService


class RepositoryDashboardService:
    """Derives explainable dashboard metrics from persisted repository intelligence."""

    def get_dashboard(self, record: RepositoryRecord) -> RepositoryDashboard:
        intelligence = RepositoryIntelligenceService().load(record)
        if intelligence is None:
            from app.core.exceptions import APIException
            raise APIException(409, "intelligence_not_available", "Repository intelligence must be generated before displaying the dashboard.")
        symbols = [symbol for file in intelligence.files for symbol in file.symbols]
        imports = sum(len(file.imports) for file in intelligence.files)
        comments = sum(file.comment_count for file in intelligence.files)
        endpoints = sum(len(file.rest_endpoints) for file in intelligence.files)
        classes = sum(symbol.kind == "class" for symbol in symbols)
        interfaces = sum(symbol.kind == "interface" for symbol in symbols)
        functions = sum(symbol.kind == "function" for symbol in symbols)
        methods = sum(symbol.kind == "method" for symbol in symbols)
        files = max(intelligence.total_files, 1)
        average_symbols = len(symbols) / files
        complexity = max(0, min(100, round(100 - average_symbols * 7)))
        debt = max(0, min(100, round(100 - (average_symbols * 5 + len(intelligence.dependency_graph) * 1.5))))
        security = max(0, min(100, 95 - min(25, endpoints * 2)))
        health = max(0, min(100, round((complexity + debt + security) / 3)))
        statistics = RepositoryStatistics(files=intelligence.total_files, classes=classes, interfaces=interfaces, functions=functions, methods=methods, imports=imports, comments=comments, api_endpoints=endpoints, configuration_files=len(intelligence.configuration_files))
        distribution = [LanguageDistribution(language=language, file_count=count, percentage=round(count / files * 100, 1)) for language, count in sorted(intelligence.language_statistics.items(), key=lambda item: item[1], reverse=True)]
        nodes = [DiagramNode(id="repository", label=record.name, kind="repository")]
        nodes.extend(DiagramNode(id=framework.lower().replace(" ", "-"), label=framework, kind="framework") for framework in intelligence.frameworks)
        nodes.extend(DiagramNode(id=f"language-{language.lower()}", label=language, kind="language") for language in intelligence.language_statistics)
        architecture_edges = list(intelligence.file_relationship_graph)
        architecture_edges.extend(GraphEdge(source="repository", target=node.id, relationship="uses") for node in nodes if node.id != "repository")
        insights = self._insights(intelligence.total_files, average_symbols, endpoints, intelligence.frameworks, debt)
        timeline = [TimelineEvent(timestamp=record.created_at, title="Repository uploaded", detail=f"Stored {record.original_filename} with {record.file_count} files."), TimelineEvent(timestamp=intelligence.generated_at, title="Repository intelligence generated", detail=f"Indexed {intelligence.total_files} files and {len(symbols)} code symbols.")]
        if (record.storage_path / "knowledge.json").is_file():
            timeline.append(TimelineEvent(timestamp=record.created_at, title="Knowledge index created", detail="Repository chunks and embeddings are available for retrieval."))
        return RepositoryDashboard(project_id=record.project_id, health_score=ScoreCard(score=health, label="Repository health", description="Composite maintainability, security, and complexity estimate."), security_score=ScoreCard(score=security, label="Security posture", description="Heuristic score based on exposed API surface; not a penetration test."), complexity_score=ScoreCard(score=complexity, label="Complexity", description="Higher score indicates a lower symbol density per file."), technical_debt_score=ScoreCard(score=debt, label="Technical debt", description="Higher score indicates less estimated structural debt."), statistics=statistics, language_distribution=distribution, dependency_graph=intelligence.dependency_graph, architecture_diagram=ArchitectureDiagram(nodes=nodes, edges=architecture_edges), ai_insights=insights, timeline=timeline)

    @staticmethod
    def _insights(total_files: int, average_symbols: float, endpoints: int, frameworks: list[str], debt: int) -> list[DashboardInsight]:
        insights = [DashboardInsight(title="Repository indexed", detail=f"{total_files} files are available to the intelligence and knowledge engines.", severity="info")]
        if average_symbols > 8:
            insights.append(DashboardInsight(title="High symbol density", detail="Some files may have multiple responsibilities. Prioritize focused code review.", severity="warning"))
        if endpoints:
            insights.append(DashboardInsight(title="API surface detected", detail=f"{endpoints} REST endpoint signatures were detected. Review authentication and input validation.", severity="warning"))
        if frameworks:
            insights.append(DashboardInsight(title="Framework signals", detail=f"Detected: {', '.join(frameworks)}.", severity="info"))
        if debt < 60:
            insights.append(DashboardInsight(title="Technical debt attention", detail="Structural complexity and dependency volume lowered the estimated debt score.", severity="critical"))
        return insights
