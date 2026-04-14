# 04 — Context & Lifespan: Connecting to Real Systems

## The problem

Your MCP tools need to talk to a database and call the OpenAI API. You need:
1. **Startup/shutdown logic** — connect to Postgres when the server starts, disconnect when it stops
2. **Shared state in tools** — every tool call needs access to that DB connection

## Lifespan

An async context manager that runs at server start/stop. Whatever you `yield` becomes shared state.

```python
@asynccontextmanager
async def app_lifespan(server: FastMCP):
    db = FakeDB(connected=True)       # setup
    try:
        yield {"db": db}              # shared state available to all tools
    finally:
        db.connected = False           # teardown
```

Pass it to the server: `mcp = FastMCP("Demo", lifespan=app_lifespan)`

## Context

Add `ctx: Context` to any tool function. FastMCP injects it automatically — **the LLM never sees this parameter** (it's hidden from the schema).

```python
@mcp.tool
async def list_documents(ctx: Context) -> str:
    db = ctx.request_context.lifespan_context["db"]  # access shared state
    await ctx.info("Found 5 documents")               # log to the LLM client
    return ...
```

## What Context gives you

| Method | Purpose |
|--------|---------|
| `ctx.request_context.lifespan_context` | Access shared state from lifespan |
| `await ctx.info(msg)` | Send log messages visible to the LLM client |
| `await ctx.warning(msg)` | Send warning-level log |
| `await ctx.report_progress(current, total)` | Progress reporting for long ops |

## For your RAG app

This is exactly how you'll wire up:
- **SQLAlchemy async session** → in lifespan, yield the session factory
- **OpenAI client** → in lifespan, create the client once, share it
- **Tools** → inject via `ctx`, query the DB, call embeddings

## Run it

```bash
cd app/backend/learn_mcp

# Terminal 1
uv run fastmcp run 04_context.py --transport http --port 8001

# Terminal 2
uv run fastmcp call http://127.0.0.1:8001/mcp list_documents --auth none
uv run fastmcp call http://127.0.0.1:8001/mcp add_document filename=notes.txt content="Hello MCP" --auth none
uv run fastmcp call http://127.0.0.1:8001/mcp list_documents --auth none
```

## Key takeaway

Lifespan = setup/teardown. Context = dependency injection. Together they let your tools access databases, API clients, and shared state cleanly.
