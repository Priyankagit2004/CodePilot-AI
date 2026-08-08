from app.schemas.health import HealthResponse


class HealthService:
    """Health status service; future dependency checks belong here."""

    def get_status(self) -> HealthResponse:
        return HealthResponse(status="ok")
