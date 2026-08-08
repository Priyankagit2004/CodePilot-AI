from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.health import HealthService
from app.services.repository import RepositoryService
from app.services.repository_knowledge import RepositoryKnowledgeService
from app.services.gemini_assistant import GeminiAssistantService
from app.agents.orchestrator import MultiAgentOrchestrator
from app.services.repository_dashboard import RepositoryDashboardService


def get_health_service(_: Settings = Depends(get_settings)) -> HealthService:
    """Provide services through FastAPI's dependency injection system."""

    return HealthService()


def get_repository_service(settings: Settings = Depends(get_settings)) -> RepositoryService:
    return RepositoryService(settings)


def get_repository_knowledge_service(settings: Settings = Depends(get_settings)) -> RepositoryKnowledgeService:
    return RepositoryKnowledgeService(settings)


def get_gemini_assistant_service(
    settings: Settings = Depends(get_settings),
    knowledge_service: RepositoryKnowledgeService = Depends(get_repository_knowledge_service),
) -> GeminiAssistantService:
    return GeminiAssistantService(settings, knowledge_service)


def get_multi_agent_orchestrator(settings: Settings = Depends(get_settings)) -> MultiAgentOrchestrator:
    return MultiAgentOrchestrator(settings)


def get_repository_dashboard_service() -> RepositoryDashboardService:
    return RepositoryDashboardService()
