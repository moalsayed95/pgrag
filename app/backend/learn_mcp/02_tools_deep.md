# 02 — Tools in Depth

## Why tools matter

Tools are the bread and butter of MCP. For your RAG app, the most valuable MCP tools would be:
- `search_documents(query)` → find relevant chunks via pgvector
- `list_documents()` → show what's been uploaded
- `ingest_document(filename, content)` → add a new document

## How tools work

1. You write a Python function with type hints
2. `@mcp.tool` generates a JSON schema from the signature
3. The **docstring** becomes the tool description — this is what the LLM reads to decide when to use it
4. FastMCP validates inputs, calls your function, serializes the output

## Patterns shown in this code

| Pattern | What it demonstrates |
|---------|---------------------|
| `search(query, max_results=5)` | Basic types, default values |
| `ingest_document(doc: DocumentInput)` | Pydantic model as input → complex structured JSON schema |
| `async analyze_text(text)` | Async tools (your RAG app is async end-to-end) |
| `list_available_models()` | Returning `list[dict]` — structured data is fine |
| `get_chunk_settings()` with `annotations` | `readOnlyHint=True` tells the LLM this tool has no side effects |

## Pydantic model inputs

When you need structured input (not just `str`/`int`), use a Pydantic `BaseModel`. The `Field(description=...)` becomes part of the schema the LLM sees:

```python
class DocumentInput(BaseModel):
    filename: str = Field(description="Name of the document file")
    content: str = Field(description="Raw text content")
    tags: list[str] = Field(default_factory=list, description="Optional tags")
```

## Run it

```bash
cd app/backend/learn_mcp

# Terminal 1
uv run fastmcp run 02_tools_deep.py --transport http --port 8001

# Terminal 2
uv run fastmcp list http://127.0.0.1:8001/mcp --auth none
uv run fastmcp call http://127.0.0.1:8001/mcp search query=pgvector --auth none
uv run fastmcp call http://127.0.0.1:8001/mcp get_chunk_settings --auth none
```

## Key takeaway

Your function signature IS the tool's API. Type hints → schema. Docstring → description. The better you annotate, the better the LLM uses your tool.
