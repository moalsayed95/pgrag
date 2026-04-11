# Project Guidelines

## Scope

- Focus application work on the Docker Compose path unless a task explicitly asks for Kubernetes.
- Treat [../README.md](../README.md) as the primary runbook and [../plan.md](../plan.md) as the roadmap.

## Architecture

- This repo is a three-service app: PostgreSQL with pgvector, a FastAPI backend, and a React/Vite frontend.
- Docker Compose in [../docker-compose.yml](../docker-compose.yml) is the canonical full-stack runtime for app work.
- Backend code lives under [../app/backend/src/pg_rag](../app/backend/src/pg_rag). Frontend code lives under [../app/frontend/src](../app/frontend/src).
- The backend initializes the database on app startup in [../app/backend/src/pg_rag/main.py](../app/backend/src/pg_rag/main.py) via [../app/backend/src/pg_rag/database.py](../app/backend/src/pg_rag/database.py).
- RAG flow is: upload document -> decode text -> chunk -> embed with OpenAI -> store chunks in Postgres -> embed question -> pgvector similarity search -> generate answer with OpenAI chat.

## Build And Run

- Full stack: `docker compose up -d --build`
- Stop stack: `docker compose down`
- Backend local dev: `cd app/backend && uv sync && uv run fastapi dev src/pg_rag/main.py`
- Frontend local dev: `cd app/frontend && npm install && npm run dev`
- Frontend production build: `cd app/frontend && npm run build`
- Backend tests use pytest tooling, but there are currently no real test files.

## Conventions

- Keep backend code async end to end. Use `AsyncSession`, `await`, and existing dependency injection patterns from the routers.
- Keep API routes under the `/api` prefix to match the Vite dev proxy and the Nginx proxy used in Docker.
- Use existing models and schemas before introducing new response shapes or database tables.
- Preserve the current minimal frontend structure: [../app/frontend/src/App.tsx](../app/frontend/src/App.tsx) composes the app from focused components instead of centralizing all logic.

## OpenAI SDK

- Use the **Responses API** (`client.responses.create`) for all LLM text generation. Do **not** use the legacy Chat Completions API (`client.chat.completions.create`).
- The Responses API uses `instructions` (instead of a system message), `input` (instead of `messages`), and returns `response.output_text`.
- Embeddings still use `client.embeddings.create` — that endpoint is separate from the Responses API.
- Future MCP server integrations must be built on top of the Responses API (it natively supports MCP tools via the `tools` parameter).

## Known Pitfalls

- PDF upload is advertised in the UI and route docstring, but [../app/backend/src/pg_rag/routers/documents.py](../app/backend/src/pg_rag/routers/documents.py) currently just decodes uploaded bytes as UTF-8 text. Do not assume real PDF parsing exists.
- Chunk settings exist in [../app/backend/src/pg_rag/config.py](../app/backend/src/pg_rag/config.py), but the upload route currently uses `chunk_text` defaults instead of reading settings.
- CORS in [../app/backend/src/pg_rag/main.py](../app/backend/src/pg_rag/main.py) only allows `http://localhost:5173`. Any origin change should be intentional and tied to the deployment path.
- Retrieval in [../app/backend/src/pg_rag/rag.py](../app/backend/src/pg_rag/rag.py) uses raw SQL and pgvector cosine distance. Keep query semantics compatible if you change ranking or filtering.
- There is no streaming chat yet. The current API returns complete answers only.