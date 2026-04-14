# 03 — Resources: Read-Only Data

## Tools vs Resources

| | Tools | Resources |
|---|---|---|
| **Action** | LLM calls a function to DO something | LLM reads data |
| **Analogy** | `POST /api/chat` | `GET /api/documents` |
| **Example** | `search_documents(query)` | `resource://documents/list` |

Think of resources as "files the LLM can look at."

## Two kinds of resources

1. **Static** — fixed URI, always returns the same kind of data
   ```python
   @mcp.resource("data://documents/list")
   def list_documents() -> str: ...
   ```

2. **Template** — URI with `{parameters}`, like a GET endpoint with path params
   ```python
   @mcp.resource("data://documents/{doc_id}")
   def get_document(doc_id: str) -> str: ...
   ```

## For your RAG app

| Resource URI | What it exposes |
|---|---|
| `data://documents/list` | All uploaded documents with chunk counts |
| `data://documents/{id}` | Content of a specific document |
| `data://config/settings` | Current embedding model, chunk size, etc. |

## Mixing tools + resources

A server can have both. Use **tools** for actions (search, upload, chat) and **resources** for reference data (config, document metadata).

## Run it

```bash
cd app/backend/learn_mcp

# Terminal 1
uv run fastmcp run 03_resources.py --transport http --port 8001

# Terminal 2 — list everything
uv run fastmcp list http://127.0.0.1:8001/mcp --auth none --resources
```

## Key takeaway

Resources are less commonly used than tools (most LLM clients focus on tools), but they're the right choice for exposing read-only reference data.
