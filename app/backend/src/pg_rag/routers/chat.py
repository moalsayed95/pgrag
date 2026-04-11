import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from pg_rag.database import get_db
from pg_rag.schemas import ChatRequest, ChatResponse, SourceChunk
from pg_rag.rag import retrieve_chunks, generate_answer, generate_answer_stream

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Ask a question — retrieves relevant chunks and generates an answer."""
    chunks = await retrieve_chunks(db, req.question)

    if not chunks:
        return ChatResponse(answer="No documents found. Please upload some documents first.", sources=[])

    answer = await generate_answer(req.question, chunks)

    sources = [
        SourceChunk(
            content=row.content,
            chunk_index=row.chunk_index,
            document_filename=row.filename,
            score=round(row.score, 4),
        )
        for row in chunks
    ]

    return ChatResponse(answer=answer, sources=sources)


@router.post("/stream")
async def chat_stream(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Ask a question — streams the answer as Server-Sent Events."""
    chunks = await retrieve_chunks(db, req.question)

    sources = [
        SourceChunk(
            content=row.content,
            chunk_index=row.chunk_index,
            document_filename=row.filename,
            score=round(row.score, 4),
        )
        for row in chunks
    ]

    async def event_generator():
        if not chunks:
            yield _sse("text_delta", {"delta": "No documents found. Please upload some documents first."})
            yield _sse("sources", {"sources": []})
            yield _sse("done", {})
            return

        try:
            async for delta in generate_answer_stream(req.question, chunks):
                yield _sse("text_delta", {"delta": delta})
            yield _sse("sources", {"sources": [s.model_dump() for s in sources]})
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
