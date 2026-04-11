from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI

from pg_rag.config import get_settings
from pg_rag.embeddings import get_embedding

settings = get_settings()
client = AsyncOpenAI(api_key=settings.openai_api_key)

INSTRUCTIONS = """You are a helpful assistant that answers questions based on the provided context.
Use ONLY the context below to answer. If the context doesn't contain enough information, say so.
Be concise and accurate.

Context:
{context}"""


def _build_context(chunks) -> str:
    return "\n\n---\n\n".join(
        f"[Source: {row.filename}, chunk {row.chunk_index}]\n{row.content}"
        for row in chunks
    )


async def retrieve_chunks(db: AsyncSession, question: str, top_k: int = 5):
    """Embed the question and find the most similar document chunks."""
    query_embedding = await get_embedding(question)

    sql = text("""
        SELECT
            dc.content,
            dc.chunk_index,
            d.filename,
            1 - (dc.embedding <=> cast(:embedding AS vector)) AS score
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        ORDER BY dc.embedding <=> cast(:embedding AS vector)
        LIMIT :top_k
    """)

    result = await db.execute(sql, {"embedding": str(query_embedding), "top_k": top_k})
    return result.fetchall()


async def generate_answer(question: str, chunks) -> str:
    """Build a prompt from retrieved chunks and generate an answer."""
    context = _build_context(chunks)

    response = await client.responses.create(
        model=settings.openai_chat_model,
        instructions=INSTRUCTIONS.format(context=context),
        input=question,
        temperature=0.2,
    )

    return response.output_text


async def generate_answer_stream(question: str, chunks) -> AsyncGenerator[str, None]:
    """Stream text deltas from the Responses API."""
    context = _build_context(chunks)

    stream = await client.responses.create(
        model=settings.openai_chat_model,
        instructions=INSTRUCTIONS.format(context=context),
        input=question,
        temperature=0.2,
        stream=True,
    )

    async for event in stream:
        if event.type == "response.output_text.delta":
            yield event.delta
