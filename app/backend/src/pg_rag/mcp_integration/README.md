# The three retrieval patterns, explained simply

This app lets you answer the **same question** using three different
retrieval pipelines. They all end in the same place — the LLM writes an
answer grounded in document chunks from Postgres — but the *way* they get
there is different. Understanding those differences is the whole point of
this tutorial.

Flip between them with the toggle in the top-right of the chat UI.

---

## The one question we're solving

> "Given a user question, figure out if we need to search documents, do the
> search if yes, then write an answer using what we found."

Every pattern below answers that exact prompt. Only the plumbing changes.

---

## Pattern 1 — Function calling (`pg_rag/rag.py`)

**The classic setup. No MCP involved.**

### How it works

1. Your app tells OpenAI: *"here's a tool called `search_documents`, here's
   what its arguments look like."* The tool definition is a **hardcoded
   Python dict** in your source code.
2. OpenAI decides whether to use it. If yes, it sends back: *"please call
   `search_documents({query: '...'})`."*
3. **Your app** runs the search — it queries Postgres directly via
   `retrieve_chunks()`.
4. Your app sends the result back to OpenAI, which streams the final answer.

### What to remember

- Tool definition: **in your code**.
- Tool execution: **in your code**.
- Everything lives in one process.
- Only talks to: OpenAI.

### When this is enough

You have one app, one tool, you wrote it, you run it. No need for MCP.

---

## Pattern 2 — MCP, app-as-client (`pg_rag/mcp_integration/rag_client.py` + `server.py`)

**Same flow as Pattern 1, but retrieval moves behind a protocol.**

### How it works

1. A **separate service** (`pg_rag/mcp/server.py`) runs an MCP server that
   exposes `search_documents`. This is now a standalone network service.
2. Your app starts an **MCP client** (`fastmcp.Client`), connects to the
   MCP server, and asks: *"what tools do you have?"* The tool definition
   is **fetched at runtime**, not hardcoded.
3. Your app tells OpenAI about those tools (same function-calling format
   as Pattern 1).
4. When OpenAI asks to call `search_documents`, your app **forwards the
   call to the MCP server** via `mcp_client.call_tool(...)` — the MCP
   server runs the actual Postgres query.
5. Your app sends the result back to OpenAI and streams the answer.

### What changed from Pattern 1

- Tool definition: **discovered from an MCP server at runtime**.
- Tool execution: **happens in the MCP server**, not your app.
- Two processes: your app + MCP server.
- Your app still talks to OpenAI *and* to the MCP server.

### Why you'd do this

- **Reusability**: any MCP client (Claude Desktop, Cursor, another team's
  agent) can use the same `search_documents` tool with zero extra code.
- **Separation**: retrieval logic is no longer glued to your app.
- **Discoverability**: add a new tool to the MCP server → your app picks
  it up on reconnect. No redeploy.

### The catch

Your app is still doing orchestration work (two API calls, schema
conversion, dispatching). It's more code than Pattern 1 for a single-app
demo. The win shows up when **multiple clients** share the same tools.

---

## Pattern 3 — MCP, native (`pg_rag/mcp_integration/rag_native.py` + `server.py`)

**The "OpenAI speaks MCP for you" shortcut.**

### How it works

1. Same MCP server as Pattern 2.
2. Your app tells OpenAI: *"here's an MCP server at this URL, use it."*
   That's literally it — one tool entry of `type: "mcp"` in the Responses API.
3. **OpenAI itself** connects to the MCP server, asks it what tools it has,
   decides when to call them, calls them, and streams the grounded answer
   back to you.
4. Your app's retrieval code shrinks to a single API call.

### What changed from Pattern 2

- Tool definition: **OpenAI discovers it** (your app never sees the schema).
- Tool execution: still happens in the MCP server, but **OpenAI triggers
  the call** directly — your app is no longer in the loop.
- One API round-trip instead of two.
- Your app only talks to: OpenAI. (OpenAI talks to the MCP server.)

### Why you'd do this

- **Least code**. The entire "when to search, how to search, how to ground
  the answer" flow becomes ~10 lines.
- It's what OpenAI recommends once MCP is involved.

### The catch (this matters)

**The MCP server must be reachable from the public internet.** OpenAI's
servers need to hit it. `localhost:8001` doesn't work. For local dev you
need ngrok (or deploy it).

That means the moment you enable this pattern, your retrieval tool is on
the open internet. You **must** protect it with a bearer token — see
`learn_mcp/06_exposing_with_ngrok.md` for the full setup.

Also: because OpenAI runs the whole tool call itself, extracting the
retrieved chunks for your "Cited Passages" UI is a bit indirect — we
parse them out of the `mcp_call` output items in the final response.
With Pattern 2 we have them in hand.

---

## Side-by-side cheat sheet

| | Pattern 1: fn-call | Pattern 2: mcp (app client) | Pattern 3: mcp (native) |
|---|---|---|---|
| Where's the tool defined? | In your app code | In the MCP server | In the MCP server |
| Who runs the tool? | Your app | The MCP server | The MCP server |
| Who's the MCP client? | (no MCP) | **Your app** | **OpenAI** |
| Who orchestrates? | Your app | Your app | OpenAI |
| API calls per question | 2 | 2 | 1 |
| Works with localhost only? | ✅ yes | ✅ yes | ❌ needs public URL |
| Needs auth on the server? | N/A | Optional (local) | **Required** |
| Reusable by other clients? | ❌ no | ✅ yes | ✅ yes |
| Your code is… | smallest for one app | more for same result | smallest overall |

---

## The one-paragraph summary

Function calling is when **your app** teaches the LLM about a tool and
**your app** runs it. MCP doesn't replace function calling — it's a
**standard way to ship the tool itself** so other clients can use it too.
In Pattern 2, your app is still the tool runner, it just loads the tool
from an MCP server. In Pattern 3, you hand the MCP server's URL straight
to OpenAI and it becomes the tool runner for you. Pattern 3 is the
cleanest code, but it's the one that puts your tool on the public
internet — so it's the one that needs auth.
