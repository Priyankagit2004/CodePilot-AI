# Deployment guide

## Container deployment

Build and publish the two images from `apps/api/Dockerfile` and `apps/web/Dockerfile`. Run the API behind a TLS-terminating reverse proxy and expose only the web service publicly where practical.

## Required production settings

- Set `APP_ENV=production`, `DEBUG=false`, and an appropriate `CORS_ORIGINS` JSON array.
- Use a restricted `GEMINI_API_KEY` managed by the deployment secret store.
- Mount persistent storage for both repository archives and ChromaDB.
- Set resource limits appropriate for archive extraction and local embedding-model memory use.

## Operations

The API emits JSON logs and returns `X-Request-ID` on each response. Forward logs to your centralized logging platform and alert on repeated `5xx` errors, failed upload validation, and Gemini provider failures.

## Scaling

Local Chroma persistence is suitable for a single-instance deployment. For horizontally scaled production workloads, move repository metadata to managed storage and replace the embedded Chroma persistence with a shared Chroma server or managed vector store.
