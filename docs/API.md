# API reference

FastAPI publishes interactive Swagger UI at `/docs`, ReDoc at `/redoc`, and the OpenAPI schema at `/openapi.json`.

## Core

- `GET /health` and `GET /api/v1/health` — service health.
- `POST /api/v1/repositories/upload` — upload a repository ZIP.
- `GET /api/v1/repositories` — list stored repositories.
- `GET /api/v1/repositories/{project_id}` — repository metadata.

## Intelligence and knowledge

- `GET /api/v1/repositories/{project_id}/intelligence`
- `POST /api/v1/repositories/{project_id}/intelligence/rebuild`
- `POST /api/v1/repositories/{project_id}/knowledge/index`
- `POST /api/v1/repositories/{project_id}/knowledge/search`
- `POST /api/v1/repositories/{project_id}/knowledge/answer`

## AI and agents

- `POST /api/v1/repositories/{project_id}/assistant/{task}` — Gemini assistant task.
- `POST /api/v1/repositories/{project_id}/onboarding` — newcomer repository guide.
- `POST /api/v1/agents/execute` — LangGraph multi-agent orchestration.

## Dashboard

- `GET /api/v1/repositories/{project_id}/dashboard` — scores, charts, graphs, insights, and timeline data.

All error responses use the form `{"error": {"code": "…", "message": "…"}}`.
