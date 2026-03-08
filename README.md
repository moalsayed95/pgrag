# 🐘 PG-RAG — Retrieval Augmented Generation with PostgreSQL

A full-stack RAG (Retrieval Augmented Generation) application that uses **PostgreSQL + pgvector** as the vector store — no separate vector database needed.

Upload documents, chunk & embed them with OpenAI, then ask questions answered by an LLM grounded in your own data.

## Architecture

```
┌─────────────┐       ┌──────────────────┐       ┌──────────────────────┐
│  React/Vite  │──────▶│  FastAPI Backend  │──────▶│  PostgreSQL + pgvector│
│  Frontend    │◀──────│  (Python / uv)   │◀──────│  (Docker)            │
└─────────────┘       └──────────────────┘       └──────────────────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │  OpenAI API   │
                      │  (Embeddings  │
                      │   + Chat)     │
                      └──────────────┘
```

## Tech Stack

| Layer      | Tech                                |
| ---------- | ----------------------------------- |
| Frontend   | React 18 + Vite + TypeScript        |
| Backend    | Python 3.12 + FastAPI               |
| Database   | PostgreSQL 16 + pgvector            |
| Embeddings | OpenAI `text-embedding-3-small`     |
| LLM        | OpenAI `gpt-4o-mini`                |
| Packaging  | uv (Python), npm (Frontend)         |
| Infra      | Docker Compose (PostgreSQL)         |

## Project Structure

```
pg-rag/
├── README.md
├── plan.md                    # Live demo roadmap
├── docker-compose.yml         # PostgreSQL + pgvector
├── .env.example               # Environment variable template
├── app/
│   ├── backend/
│   │   ├── pyproject.toml
│   │   ├── src/pg_rag/
│   │   │   ├── main.py           # FastAPI app + CORS + lifespan
│   │   │   ├── config.py         # Pydantic settings from .env
│   │   │   ├── database.py       # Async SQLAlchemy + table init
│   │   │   ├── models.py         # Documents + chunks with vector column
│   │   │   ├── schemas.py        # Request/response Pydantic models
│   │   │   ├── embeddings.py     # OpenAI embedding + text chunking
│   │   │   ├── rag.py            # Retrieve chunks + generate answers
│   │   │   └── routers/
│   │   │       ├── documents.py  # POST /upload, GET /list
│   │   │       └── chat.py       # POST /chat
│   │   └── tests/
│   └── frontend/
│       └── src/
│           ├── App.tsx
│           └── components/
│               ├── ChatPanel.tsx
│               └── DocumentUpload.tsx
```

## How It Works

1. **Upload** — A document (TXT/MD) is uploaded via the API
2. **Chunk** — The text is split into overlapping chunks (500 chars, 100 overlap)
3. **Embed** — Each chunk is sent to OpenAI's embedding API → 1536-dim vector
4. **Store** — Chunks + vectors are stored in PostgreSQL using pgvector's `VECTOR(1536)` column
5. **Query** — A user question is embedded, then pgvector finds the most similar chunks using cosine distance (`<=>`)
6. **Generate** — Retrieved chunks are injected as context into a prompt, and OpenAI generates a grounded answer

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- [Node.js](https://nodejs.org/) (v18+)
- An [OpenAI API key](https://platform.openai.com/api-keys)

### 1. Start PostgreSQL

```bash
docker compose up -d
```

This runs PostgreSQL 16 with the pgvector extension pre-installed (using the `pgvector/pgvector:pg16` image).

### 2. Start the Backend

```bash
cd app/backend
cp ../../.env.example .env
# Edit .env and add your OPENAI_API_KEY
uv sync
uv run fastapi dev src/pg_rag/main.py
```

The API will be available at `http://localhost:8000` with Swagger docs at `http://localhost:8000/docs`.

On first startup, the app automatically:
- Enables the `vector` extension in PostgreSQL
- Creates the `documents` and `document_chunks` tables

### 3. Start the Frontend

```bash
cd app/frontend
npm install
npm run dev
```

Open `http://localhost:5173` — upload documents on the left, ask questions on the right.

## API Endpoints

| Method | Endpoint               | Description                          |
| ------ | ---------------------- | ------------------------------------ |
| GET    | `/api/health`          | Health check                         |
| POST   | `/api/documents/upload`| Upload & embed a document            |
| GET    | `/api/documents/`      | List all uploaded documents           |
| POST   | `/api/chat/`           | Ask a question (RAG query)           |

### Example: Ask a Question

```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What is pgvector?"}'
```

Response:
```json
{
  "answer": "pgvector is an open-source extension for PostgreSQL that adds support for vector similarity search...",
  "sources": [
    {
      "content": "pgvector is an open-source extension...",
      "chunk_index": 0,
      "document_filename": "test-doc.txt",
      "score": 0.7322
    }
  ]
}
```

## Why PostgreSQL for RAG?

- **No extra infrastructure** — If you already run Postgres, you don't need a separate vector DB
- **SQL + vectors** — Combine similarity search with traditional filters in a single query
- **ACID compliance** — Transactions, reliability, and a mature ecosystem
- **Indexing** — pgvector supports HNSW and IVFFlat indexes for fast approximate nearest neighbor search at scale

## License

MIT
