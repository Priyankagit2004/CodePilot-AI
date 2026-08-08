from fastapi import APIRouter

from app.routes.health import router as health_router
from app.routes.repositories import router as repositories_router
from app.routes.agents import router as agents_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(repositories_router)
api_router.include_router(agents_router)

__all__ = ["api_router", "health_router", "repositories_router", "agents_router"]
