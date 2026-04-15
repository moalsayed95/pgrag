# 06 — Exposing your MCP server to OpenAI (safely)

The **native MCP pattern** (`rag_mcp_native.py`) asks OpenAI's servers to
connect to *your* MCP server. That means the server URL has to be reachable
from the public internet — `localhost:8001` won't work.

For local dev the standard answer is an **ngrok tunnel**. It's quick, but
it also means: the moment you run `ngrok http 8001`, your database-backed
retrieval tool is on the open internet. This guide walks through doing that
without opening a hole someone else can walk through.

---

## TL;DR

1. Generate a strong random token.
2. Set `MCP_AUTH_TOKEN` for the MCP server **and** the backend.
3. Start ngrok against port 8001.
4. Put the ngrok URL in `MCP_PUBLIC_URL` for the backend.
5. Use the `mcp-native` toggle in the UI.
6. `Ctrl-C` ngrok the moment you're done. Rotate the token.

```bash
# 1. Token (run once per session)
export MCP_AUTH_TOKEN="$(openssl rand -hex 32)"

# 2. Start the stack with the token
MCP_AUTH_TOKEN=$MCP_AUTH_TOKEN docker compose up -d

# 3. Expose only the MCP port
ngrok http 8001

# 4. Grab the https URL ngrok prints, then:
export MCP_PUBLIC_URL="https://<your-ngrok-subdomain>.ngrok-free.app/mcp"

# 5. Restart the backend so it picks up MCP_PUBLIC_URL
docker compose up -d --force-recreate backend
```

---

## Why auth is non-negotiable here

Without `MCP_AUTH_TOKEN`, anyone who guesses (or scans) your ngrok URL can:

- Call `search_documents` and exfiltrate chunks of your entire corpus.
- Burn your OpenAI quota by calling tools indirectly (if you later add
  tools that make outbound requests).
- Use the tunnel as a stepping-stone into your local network.

With `MCP_AUTH_TOKEN` set, `mcp_server.py` rejects any request missing
the correct `Authorization: Bearer <token>` header. `rag_mcp_native.py`
forwards the same token to OpenAI via the `headers` field on the
`type: "mcp"` tool, and OpenAI forwards it unchanged to your server.

## What the token protects — and doesn't

- ✅ Blocks casual scanners and anyone who stumbled onto the URL.
- ✅ Keeps the tunnel useless to anyone not holding the token.
- ❌ Does **not** hide the token from OpenAI — it passes through their
  infrastructure. Use a token scoped to this demo, never a prod secret.
- ❌ Does **not** rate-limit. A stolen token lets the holder call
  your tool until you rotate.

## Generating a good token

```bash
openssl rand -hex 32        # 64 hex chars, ~256 bits of entropy
# or
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Do **not** reuse a token across demos, projects, or team members.
Never commit it; put it in `.env` and keep `.env` out of git.

## Running ngrok

```bash
# One-time: create a free ngrok account and configure your authtoken
ngrok config add-authtoken <your-ngrok-authtoken>

# Tunnel only the MCP port — do NOT tunnel port 8000 (the app) too
ngrok http 8001
```

**Only expose port 8001.** Your FastAPI app on 8000 has no auth, is not
needed by OpenAI, and has no business being on the internet.

ngrok prints a forwarding URL like `https://abcd-1234.ngrok-free.app`.
Your MCP endpoint is that URL plus `/mcp`:

```
MCP_PUBLIC_URL=https://abcd-1234.ngrok-free.app/mcp
```

## Security hardening checklist

| | Free ngrok | Paid ngrok |
|---|---|---|
| Bearer token on MCP server | **Required** | **Required** |
| Ephemeral URL (changes per run) | ✅ default | — |
| Reserved domain | — | ✅ |
| IP allow-list (OpenAI egress ranges) | — | ✅ recommended |
| OAuth/basic-auth at the ngrok edge | — | ✅ optional, belt-and-braces |
| Request logging / inspection | ✅ `http://localhost:4040` | ✅ dashboard |

For a tutorial video the free tier is fine — just treat every session as
disposable.

## The "do / don't" list

**Do**

- Set `MCP_AUTH_TOKEN` before the first `docker compose up` that exposes
  the MCP server publicly.
- Keep the ngrok window visible during demos — its inspector
  (`http://localhost:4040`) lets you *see* OpenAI's requests in real time,
  which is great B-roll.
- Close the tunnel (`Ctrl-C`) the second you stop filming.
- Rotate `MCP_AUTH_TOKEN` after publishing — if it's visible in any
  terminal frame of the video, treat it as leaked.

**Don't**

- Don't point ngrok at your whole machine. Tunnel the one port.
- Don't run the native-MCP flow against a production database. Use a
  throwaway corpus / local dev DB.
- Don't commit `.env`, ngrok config, or any terminal screenshot with the
  token in frame.
- Don't leave the tunnel up overnight "just in case." Every open minute
  is exposure.

## Verifying auth actually works

Quick smoke test — without the header, the server must reject:

```bash
# Should 401 / 403
curl -i $MCP_PUBLIC_URL

# Should 200 with a proper initialize handshake
curl -i $MCP_PUBLIC_URL -H "Authorization: Bearer $MCP_AUTH_TOKEN"
```

If the first one returns 200, your server is wide open — stop ngrok and
check that `MCP_AUTH_TOKEN` is actually set in the MCP service's env.

## When you outgrow ngrok

For anything beyond tutorials, replace ngrok with real infrastructure:

- Deploy the MCP server behind a managed ingress (Cloudflare, AWS ALB, etc.)
  with TLS and a proper hostname.
- Swap `StaticTokenVerifier` for `JWTVerifier` with short-lived tokens
  issued by an identity provider.
- Restrict ingress to OpenAI's published egress IP ranges if your provider
  supports it.
- Log every MCP call server-side. `StaticTokenVerifier` doesn't give you
  user identity; a real JWT does.

The tutorial pattern is a scaffold — production needs the real version.
