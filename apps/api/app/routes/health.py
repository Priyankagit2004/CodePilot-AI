from typing import Annotated

from fastapi import APIRouter, Depends

from app.routes.dependencies import get_health_service
from app.schemas.health import HealthResponse
from app.services.health import HealthService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Check API health")
async def health_check(
    service: Annotated[HealthService, Depends(get_health_service)],
) -> HealthResponse:
    return service.get_status()
