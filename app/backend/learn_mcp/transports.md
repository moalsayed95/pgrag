# MCP Transports: stdio vs HTTP

## The problem both solve

Your MCP server needs to exchange JSON messages with an MCP client (an LLM agent, VS Code, Claude Desktop, etc.). The **transport** is *how* those messages travel.

## stdio

```
[LLM Client] --stdin/stdout--> [Your MCP Server]
```

- The client **launches your server as a subprocess**
- Messages flow over **stdin** (client → server) and **stdout** (server → client)
- Your server is **not** a web server — no port, no URL
- The client manages the process lifecycle (starts it, kills it)

**Used by:** Claude Desktop, VS Code Copilot, Cursor, Claude Code — anything that runs locally and can spawn a process.

**When you run:** `uv run python 01_hello_mcp.py`
→ Server starts, waits on stdin. Useless in a terminal by itself because *you* aren't an MCP client piping JSON.

## HTTP (Streamable HTTP)

```
[LLM Client] --HTTP POST--> http://localhost:8001/mcp --> [Your MCP Server]
```

- Your server **runs as a web service** on a port
- Messages flow over standard **HTTP requests/responses**
- Server runs independently — any client can connect via URL
- You can test it from the CLI, browser inspector, or code

**Used by:** Remote/hosted servers, production deployments, multi-client setups.

**When you run:** `uv run fastmcp run 01_hello_mcp.py --transport http --port 8001`
→ Web server starts at `http://127.0.0.1:8001/mcp`. You can hit it from another terminal.

## When to use which

| | stdio | HTTP |
|---|---|---|
| **Local dev with an MCP client** (VS Code, Claude) | ✅ Default, just works | Overkill |
| **Testing from terminal** | ❌ Can't interact manually | ✅ Use `fastmcp list` / `fastmcp call` |
| **Production / remote access** | ❌ Requires local process | ✅ Runs as a service |
| **Multiple clients at once** | ❌ One client per process | ✅ Any number of clients |

## TL;DR

- **stdio** = client launches your server as a child process, talks via pipes. Zero config, but only works locally.
- **HTTP** = your server is a web service. Works everywhere, testable from CLI.

For learning, use HTTP so you can poke at it from the terminal. When you wire it into VS Code or Claude Desktop later, stdio is the default and simplest.
