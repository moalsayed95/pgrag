from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from pg_rag.database import get_db
from pg_rag.schemas import ChatRequest, ChatResponse, SourceChunk
from pg_rag.rag import retrieve_chunks, generate_answer

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
