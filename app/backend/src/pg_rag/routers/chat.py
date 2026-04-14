import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from pg_rag.database import get_db
from pg_rag.schemas import ChatRequest, SourceChunk
from pg_rag.rag import stream_rag_response

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/stream")
async def chat_stream(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Ask a question — streams the answer as Server-Sent Events."""

    async def event_generator():
        try:
            async for event_type, data in stream_rag_response(db, req.question):
                if event_type == "delta":
                    yield _sse("text_delta", {"delta": data})
                elif event_type == "sources":
                    sources = [
                        SourceChunk(
                            content=row.content,
                            chunk_index=row.chunk_index,
                            document_filename=row.filename,
                            score=round(row.score, 4),
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
