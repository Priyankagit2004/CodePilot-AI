from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.routes.dependencies import get_gemini_assistant_service, get_repository_dashboard_service, get_repository_knowledge_service, get_repository_service
from app.schemas.dashboard import RepositoryDashboard
from app.schemas.assistant import AssistantRequest, AssistantResponse, AssistantTask
from app.schemas.knowledge import KnowledgeAnswerResponse, KnowledgeIndexResponse, KnowledgeQuery, KnowledgeSearchResponse
from app.schemas.onboarding import OnboardingRequest, OnboardingResponse
from app.schemas.repository import RepositoryListResponse, RepositoryResponse
from app.schemas.intelligence import RepositoryIntelligence
from app.services.repository import RepositoryService
from app.services.repository_intelligence import RepositoryIntelligenceService
from app.services.repository_knowledge import RepositoryKnowledgeService
from app.services.gemini_assistant import GeminiAssistantService
from app.services.repository_dashboard import RepositoryDashboardService

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("/upload", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def upload_repository(
    file: Annotated[UploadFile, File(description="Repository ZIP archive")],
    service: Annotated[RepositoryService, Depends(get_repository_service)],
) -> RepositoryResponse:
    return await service.upload(file)


@router.get("", response_model=RepositoryListResponse)
async def list_repositories(
    service: Annotated[RepositoryService, Depends(get_repository_service)],
) -> RepositoryListResponse:
    return RepositoryListResponse(repositories=service.list_repositories())


@router.get("/{project_id}", response_model=RepositoryResponse)
async def get_repository(
    project_id: str,
    service: Annotated[RepositoryService, Depends(get_repository_service)],
) -> RepositoryResponse:
    return service.get_repository(project_id)


@router.get("/{project_id}/intelligence", response_model=RepositoryIntelligence)
async def get_repository_intelligence(
    project_id: str,
    service: Annotated[RepositoryService, Depends(get_repository_service)],
) -> RepositoryIntelligence:
    from app.core.exceptions import APIException

    intelligence = RepositoryIntelligenceService().load(service.get_record(project_id))
    if intelligence is None:
        raise APIException(404, "intelligence_not_found", "Repository intelligence has not been generated.")
    return intelligence


@router.post("/{project_id}/intelligence/rebuild", response_model=RepositoryIntelligence)
async def rebuild_repository_intelligence(
    project_id: str,
    service: Annotated[RepositoryService, Depends(get_repository_service)],
) -> RepositoryIntelligence:
    return RepositoryIntelligenceService().analyze(service.get_record(project_id))


@router.post("/{project_id}/knowledge/index", response_model=KnowledgeIndexResponse)
async def index_repository_knowledge(
    project_id: str,
    repository_service: Annotated[RepositoryService, Depends(get_repository_service)],
    knowledge_service: Annotated[RepositoryKnowledgeService, Depends(get_repository_knowledge_service)],
) -> KnowledgeIndexResponse:
    return knowledge_service.index(repository_service.get_record(project_id))


@router.post("/{project_id}/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_repository_knowledge(
    project_id: str,
    query: KnowledgeQuery,
    repository_service: Annotated[RepositoryService, Depends(get_repository_service)],
    knowledge_service: Annotated[RepositoryKnowledgeService, Depends(get_repository_knowledge_service)],
) -> KnowledgeSearchResponse:
    return knowledge_service.search(repository_service.get_record(project_id), query.question, query.limit)


@router.post("/{project_id}/knowledge/answer", response_model=KnowledgeAnswerResponse)
async def answer_repository_question(
    project_id: str,
    query: KnowledgeQuery,
    repository_service: Annotated[RepositoryService, Depends(get_repository_service)],
    knowledge_service: Annotated[RepositoryKnowledgeService, Depends(get_repository_knowledge_service)],
) -> KnowledgeAnswerResponse:
    return knowledge_service.answer(repository_service.get_record(project_id), query.question, query.limit)


@router.post("/{project_id}/assistant/{task}", response_model=AssistantResponse)
async def answer_with_gemini(
    project_id: str,
    task: AssistantTask,
    request: AssistantRequest,
    repository_service: Annotated[RepositoryService, Depends(get_repository_service)],
    assistant_service: Annotated[GeminiAssistantService, Depends(get_gemini_assistant_service)],
) -> AssistantResponse:
    return assistant_service.answer(repository_service.get_record(project_id), task, request)


@router.post("/{project_id}/onboarding", response_model=OnboardingResponse)
async def generate_onboarding_guide(
    project_id: str,
    request: OnboardingRequest,
    repository_service: Annotated[RepositoryService, Depends(get_repository_service)],
    assistant_service: Annotated[GeminiAssistantService, Depends(get_gemini_assistant_service)],
) -> OnboardingResponse:
    response = assistant_service.answer(
        repository_service.get_record(project_id),
        "onboarding",
        AssistantRequest(question=request.question, context_limit=request.context_limit),
    )
    return OnboardingResponse(project_id=project_id, guide=response.answer, context=response.context)


@router.get("/{project_id}/dashboard", response_model=RepositoryDashboard)
async def get_repository_dashboard(
    project_id: str,
    repository_service: Annotated[RepositoryService, Depends(get_repository_service)],
    dashboard_service: Annotated[RepositoryDashboardService, Depends(get_repository_dashboard_service)],
) -> RepositoryDashboard:
    return dashboard_service.get_dashboard(repository_service.get_record(project_id))
