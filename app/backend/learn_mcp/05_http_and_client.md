# 05 — HTTP Transport & the FastMCP Client

## What this lesson adds

Lessons 01–04 defaulted to stdio. This lesson:
1. Runs the server explicitly on **HTTP** (like your FastAPI backend)
2. Uses the **FastMCP `Client`** to call tools programmatically from Python

## HTTP transport

```python
mcp.run(transport="http", host="127.0.0.1", port=8001)
```

This starts a web server at `http://127.0.0.1:8001/mcp`. Any MCP client can connect via URL.

See [transports.md](transports.md) for the full stdio vs HTTP comparison.

## The FastMCP Client

Call any MCP server programmatically — useful for testing and building agentic workflows.

```python
async with Client("http://127.0.0.1:8001/mcp") as client:
    tools = await client.list_tools()              # discover tools
    result = await client.call_tool("greet", {"name": "Mohamed"})  # call one
```

Key points:
- The client is **async** → use `asyncio.run()`
- Must enter the context (`async with client:`) before making calls
- Multiple calls work within the same context

## Two files

| File | Purpose |
|------|---------|
| `05_http_and_client.py` | The MCP server (runs on HTTP port 8001) |
| `05_client_test.py` | Python client that connects and calls tools |

## Run it

```bash
cd app/backend/learn_mcp

# Terminal 1 — start the server
uv run python 05_http_and_client.py

# Terminal 2 — run the client
uv run python 05_client_test.py

# Or use the CLI instead of the Python client
uv run fastmcp list http://127.0.0.1:8001/mcp --auth none
uv run fastmcp call http://127.0.0.1:8001/mcp word_count text="Hello world" --auth none
```

## Key takeaway

HTTP transport makes your MCP server a regular web service. The `Client` class lets you call any MCP server from Python code — same pattern an AI agent would use.
