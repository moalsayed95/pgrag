# 00 — What is MCP?

## The problem MCP solves

Modern AI apps wire things together manually: the LLM generates text, your backend parses that text, calls an API, formats the result, and passes it back. Every integration is custom glue code.

**MCP (Model Context Protocol)** is an open standard by Anthropic that gives LLMs a uniform way to discover and call external capabilities — databases, APIs, file systems, services — without any custom glue per integration.

Think of it like USB for AI: one standard plug, any device.

## Architecture: Host, Client, Server

```
┌─────────────────────────────────────────┐
│  Host (Claude Desktop, your AI app...)  │
│                                         │
│   ┌──────────┐      ┌──────────────┐   │
│   │  LLM     │ ←──→ │ MCP Client   │   │
│   └──────────┘      └──────┬───────┘   │
└──────────────────────────── │ ──────────┘
                              │  MCP Protocol
              ┌───────────────▼──────────────┐
              │         MCP Server           │
              │  (your Python code)          │
              │  tools / resources / prompts │
              └──────────────────────────────┘
```

| Role | What it is | Example |
|------|-----------|---------|
| **Host** | The AI application the user interacts with | Claude Desktop, your custom agent |
| **Client** | Sits inside the host, speaks the MCP protocol | `fastmcp.Client` |
| **Server** | Exposes capabilities the LLM can use | A `FastMCP` server you write |

One host can connect to **multiple** MCP servers simultaneously. One server can serve **multiple** clients.

## The 3 primitives

Everything an MCP server exposes falls into one of three categories:

| Primitive | Direction | Purpose | Analogy |
|-----------|-----------|---------|---------|
| **Tool** | LLM → Server | Call a function, get a result | `POST /api/action` |
| **Resource** | LLM ← Server | Read structured data | `GET /api/data` |
| **Prompt** | LLM ← Server | Reusable message templates | Prompt library |

**Tools** are what you'll use 90% of the time. A tool is just an annotated Python function — the LLM sees its name, description (docstring), and parameter schema, then decides when and how to call it.

## Transports: how the server is reached

| Transport | How | When to use |
|-----------|-----|-------------|
| **stdio** | stdin/stdout pipe | Local tools, CLI integrations, desktop apps |
| **HTTP (SSE)** | HTTP server at a URL | Web services, remote servers, production |

Stdio is the simplest to start with. HTTP is what you'd run in a deployed app.

## Why FastMCP?

The raw MCP spec is low-level JSON-RPC. **FastMCP** is a Python framework that wraps it:

- `@mcp.tool` turns a function into a tool (schema generated from type hints + docstring)
- `@mcp.resource` exposes read-only data
- Handles serialization, validation, and transport for you
- Same ergonomics as FastAPI

```python
from fastmcp import FastMCP

mcp = FastMCP("MyServer")

@mcp.tool
def search(query: str, max_results: int = 5) -> list[str]:
    """Search the knowledge base for relevant documents."""
    ...
```

That's it. The LLM now knows there's a `search` tool, what it does, and how to call it.

## What this series covers

This `learn_mcp/` folder walks through MCP step by step — **using the pg-rag app as the real-world context**. The application is a RAG (Retrieval-Augmented Generation) system built with:

- **PostgreSQL + pgvector** for storing and searching document embeddings
- **FastAPI** backend with `/api/chat` and `/api/documents/upload` endpoints
- **React/Vite** frontend

Right now the LLM inside that app is locked in the backend — it only answers when a user submits a chat message. **The goal of this series is to layer MCP on top of it**, so the LLM can proactively discover documents, run searches, and call the RAG pipeline as an agent.

### The roadmap

| File | What you learn |
|------|---------------|
| `01_hello_mcp.py` | Your first MCP server — two simple tools, run it and call it |
| `02_tools_deep.py` | Tools in depth — Pydantic inputs, async, annotations |
| `03_resources.py` | Resources — expose read-only data (document lists, config) |
| `04_context.py` | Lifespan + Context — connect to real databases and API clients |
| `05_http_and_client.py` | HTTP transport + the Python `Client` for programmatic calls |

Each file has a companion `.md` explaining the concepts and the connection back to the RAG app.

> Start with `01_hello_mcp.md` once you're comfortable here.
