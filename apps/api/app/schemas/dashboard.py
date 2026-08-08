from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.intelligence import GraphEdge


class ScoreCard(BaseModel):
    score: int = Field(ge=0, le=100)
    label: str
    description: str


class RepositoryStatistics(BaseModel):
    files: int
    classes: int
    interfaces: int
    functions: int
    methods: int
    imports: int
    comments: int
    api_endpoints: int
    configuration_files: int


class LanguageDistribution(BaseModel):
    language: str
    file_count: int
    percentage: float


class DiagramNode(BaseModel):
    id: str
    label: str
    kind: str


class ArchitectureDiagram(BaseModel):
    nodes: list[DiagramNode]
    edges: list[GraphEdge]


class DashboardInsight(BaseModel):
    title: str
    detail: str
    severity: str


class TimelineEvent(BaseModel):
    timestamp: datetime
    title: str
    detail: str


class RepositoryDashboard(BaseModel):
    project_id: str
    health_score: ScoreCard
    security_score: ScoreCard
    complexity_score: ScoreCard
    technical_debt_score: ScoreCard
    statistics: RepositoryStatistics
    language_distribution: list[LanguageDistribution]
    dependency_graph: list[GraphEdge]
    architecture_diagram: ArchitectureDiagram
    ai_insights: list[DashboardInsight]
    timeline: list[TimelineEvent]
