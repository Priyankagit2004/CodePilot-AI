# Installation guide

## Prerequisites

- Docker Desktop for the recommended path; or Python 3.12+ and Node.js 20+ for local development.
- A Gemini API key for AI answers and onboarding. Upload, parsing, and dashboard metrics work without it.

## Docker

1. Copy `apps/api/.env.example` to `apps/api/.env`.
2. Set `GEMINI_API_KEY` when Gemini features are required.
3. Run `docker compose up --build` from the repository root.
4. Visit `http://localhost:8080`; API docs are at `http://localhost:8000/docs`.

## Local development

Follow the commands in the root README. Keep the backend on port 8000 and Vite on port 5173, or set `VITE_API_BASE_URL` in `apps/web/.env`.

## Environment variables

See `apps/api/.env.example` and `apps/web/.env.example`. Do not add credentials to source control.
