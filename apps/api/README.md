# CodePilot AI API

FastAPI service for CodePilot AI. It provides safe repository ingestion, Tree-sitter intelligence, ChromaDB knowledge retrieval, Gemini-assisted workflows, LangGraph orchestration, dashboards, structured logging, and health checks.

## Requirements

- Python 3.12 or later

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # macOS/Linux: cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/health` for the unversioned health check. The same check is also available at `http://127.0.0.1:8000/api/v1/health`.

## Repository upload API

- `POST /api/v1/repositories/upload` accepts a multipart ZIP archive.
- `GET /api/v1/repositories` returns uploaded repository metadata.
- `GET /api/v1/repositories/{project_id}` returns a single repository.

Archives are bounded by configured compressed and extracted size limits, checked for path traversal and symbolic links before extraction, and stored locally under `REPOSITORY_STORAGE_DIR`.

## Repository intelligence

Each successful repository upload generates Tree-sitter-backed structured intelligence for Java, Python, JavaScript, and TypeScript. It indexes folders, source symbols, imports, comments, REST endpoint signatures, configuration files, framework signals, and dependency relationships. No embeddings or AI providers are involved.

- `GET /api/v1/repositories/{project_id}/intelligence` retrieves the stored repository map.
- `POST /api/v1/repositories/{project_id}/intelligence/rebuild` regenerates it.

Run parser tests with `pytest tests` after installing dependencies.

## Repository knowledge

Repository knowledge uses LangChain code-aware splitters, local Hugging Face sentence-transformer embeddings, and a persistent ChromaDB store. It does not call Gemini or any hosted generative model. Index each repository, then retrieve semantic context or receive a source-cited extractive answer:

- `POST /api/v1/repositories/{project_id}/knowledge/index`
- `POST /api/v1/repositories/{project_id}/knowledge/search`
- `POST /api/v1/repositories/{project_id}/knowledge/answer`

## Gemini assistant

Set `GEMINI_API_KEY` in `.env` to enable Gemini. Every assistant request first retrieves repository context from ChromaDB, then submits only that context plus the selected prompt template to Gemini. Prompt templates live separately in `app/agents/prompts.py`.

`POST /api/v1/repositories/{project_id}/assistant/{task}` supports: `repository-summary`, `architecture-explanation`, `explain-file`, `explain-function`, `code-review`, `bug-detection`, `refactoring-suggestions`, and `documentation-generation`.

`POST /api/v1/repositories/{project_id}/onboarding` generates a RAG-grounded Gemini onboarding guide for developers new to a repository.

## Multi-agent execution

`POST /api/v1/agents/execute` runs the LangGraph workflow. Its Planner Agent selects specialists based on the request, then the selected repository-analysis, architecture, code-review, security, documentation, and testing agents share one typed state and return independent typed outputs. Agent nodes have retry policies and structured logs; new agents can be registered in `app/agents/orchestrator.py`.

## Enterprise repository dashboard

`GET /api/v1/repositories/{project_id}/dashboard` returns explainable repository health, security, complexity, and technical-debt scores together with statistics, language distribution, dependency and architecture graph data, insights, and timeline events.

## Environment

Configuration is loaded from `.env` and environment variables. `CORS_ORIGINS` is a JSON array of permitted frontend origins.
