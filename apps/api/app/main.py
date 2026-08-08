from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.routes import api_router, health_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    logger.info("application_started", extra={"environment": settings.app_env})
    yield
    logger.info("application_stopped")


def create_application() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def log_request(request, call_next):
        request_id = request.headers.get("X-Request-ID", uuid4().hex)
        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("request_failed", extra={"request_id": request_id, "path": request.url.path})
            raise
        response.headers["X-Request-ID"] = request_id
        logger.info("request_completed", extra={"request_id": request_id, "path": request.url.path, "status_code": response.status_code, "duration_ms": round((perf_counter() - started) * 1_000, 2)})
        return response
    application.include_router(health_router)
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    register_exception_handlers(application)
    return application


app = create_application()
