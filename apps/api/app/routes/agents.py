from typing import Annotated

from fastapi import APIRouter, Depends

from app.agents.orchestrator import MultiAgentOrchestrator
from app.routes.dependencies import get_multi_agent_orchestrator
from app.schemas.agents import AgentExecutionRequest, AgentExecutionResponse

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/execute", response_model=AgentExecutionResponse)
async def execute_agents(
    request: AgentExecutionRequest,
    orchestrator: Annotated[MultiAgentOrchestrator, Depends(get_multi_agent_orchestrator)],
) -> AgentExecutionResponse:
    return orchestrator.execute(request.project_id, request.request)
