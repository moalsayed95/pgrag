import json
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from pg_rag.database import get_db
from pg_rag.schemas import ChatRequest, SourceChunk
from pg_rag.rag import stream_rag_response
from pg_rag.mcp_integration.rag_client import stream_rag_response_mcp
from pg_rag.mcp_integration.rag_native import stream_rag_response_mcp_native

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/stream")
async def chat_stream(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Ask a question — function-calling path. Streams SSE."""
    return _sse_stream(stream_rag_response(db, req.question))


@router.post("/stream-mcp")
async def chat_stream_mcp(req: ChatRequest):
    """Ask a question — MCP path (retrieval delegated to an MCP server). Streams SSE."""
    return _sse_stream(stream_rag_response_mcp(req.question))


@router.post("/stream-mcp-native")
async def chat_stream_mcp_native(req: ChatRequest):
    """Ask a question — native MCP path (OpenAI connects to the MCP server directly). Streams SSE."""
    return _sse_stream(stream_rag_response_mcp_native(req.question))


def _sse_stream(source: AsyncGenerator[tuple[str, Any], None]) -> StreamingResponse:
    """Wrap a (event_type, data) generator as an SSE response.

    Kept identical across both endpoints so the frontend can't tell them
    apart on the wire — only the URL differs.
    """

    async def event_generator():
        try:
            async for event_type, data in source:
                if event_type == "delta":
                    yield _sse("text_delta", {"delta": data})
                elif event_type == "sources":
                    sources = [
                        SourceChunk(
                            content=row.content,
                            chunk_index=row.chunk_index,
                            document_filename=row.filename,
                            score=round(float(row.score), 4),
                        ).model_dump()
                        for row in data
                    ]
                    yield _sse("sources", {"sources": sources})
            yield _sse("done", {})
        except Exception as exc:
            yield _sse("error", {"message": str(exc)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
