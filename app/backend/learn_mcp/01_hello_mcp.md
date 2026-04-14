# 01 — Hello MCP: Your First Server

## What is MCP?

Your RAG app has FastAPI endpoints (`POST /api/chat`, `POST /api/documents/upload`). A human writes frontend code to call them. The LLM is trapped inside your backend.

**MCP flips this.** You expose "tools" that LLMs discover and call directly. The LLM sees what's available, decides when to use it, picks the arguments, and processes the result.

## The 3 primitives

| Primitive | What it is | Example |
|-----------|-----------|---------|
| **Tools** | Functions the LLM can call | `search_documents(query="pgvector")` → matching chunks |
| **Resources** | Read-only data the LLM can access | `resource://documents/list` → list of uploaded docs |
| **Prompts** | Reusable message templates | `"analyze this document: {content}"` |

Tools are the most important for your RAG app.

## What this code does

- Creates a `FastMCP` server named "HelloMCP"
- Registers two tools: `greet(name)` and `add(a, b)`
- The `@mcp.tool` decorator auto-generates the JSON schema from your function signature + docstring

## Run it

```bash
cd app/backend/learn_mcp

# Terminal 1 — start the server
uv run fastmcp run 01_hello_mcp.py --transport http --port 8001

# Terminal 2 — list tools (what the LLM sees)
uv run fastmcp list http://127.0.0.1:8001/mcp --auth none

# Terminal 2 — call tools (what the LLM does)
uv run fastmcp call http://127.0.0.1:8001/mcp greet name=Mohamed --auth none
uv run fastmcp call http://127.0.0.1:8001/mcp add a=17 b=25 --auth none

# Or use the visual Inspector (browser UI)
uv run fastmcp dev inspector 01_hello_mcp.py
```

## Key takeaway

A decorated Python function → a tool an LLM can call. That's it. FastMCP handles the protocol, schema generation, validation, and serialization.
