import json
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI

from pg_rag.config import get_settings
from pg_rag.embeddings import get_embedding

settings = get_settings()
client = AsyncOpenAI(api_key=settings.openai_api_key)

# Instructions for the first-pass call (no context yet — LLM picks whether to search)
GENERAL_INSTRUCTIONS = (
    "You are a helpful assistant. "
    "If the user's question requires information from uploaded documents, "
    "use the search_documents tool. "
    "For casual conversation or general knowledge questions, answer directly without searching."
)

# Instructions for the grounded second-pass call (context supplied via tool result)
GROUNDED_INSTRUCTIONS = (
    "You are a helpful assistant. Answer the user's question using the document "
    "context returned by the search_documents tool. "
    "If the context does not contain enough information, say so clearly. "
    "Be concise and accurate."
)

SEARCH_TOOL: dict = {
    "type": "function",
    "name": "search_documents",
    "description": (
        "Search the uploaded documents for information relevant to a query. "
        "Use this tool when the user asks about document content, specific facts, "
        "or anything that requires looking up stored knowledge."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant document chunks.",
            }
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}


def build_context(chunks) -> str:
    return "\n\n---\n\n".join(
        f"[Source: {row.filename}, chunk {row.chunk_index}]\n{row.content}"
        for row in chunks
    )


async def retrieve_chunks(db: AsyncSession, query: str, top_k: int = 5):
    """Embed the query and find the most similar document chunks."""
    query_embedding = await get_embedding(query)

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


async def stream_rag_response(
    db: AsyncSession, question: str
) -> AsyncGenerator[tuple[str, Any], None]:
    """
    Single entry point for the RAG streaming pipeline.

    Step 1 — Ask the LLM with the search_documents tool available.
             If it responds directly (casual chat), yield that answer and stop.
    Step 2 — If it calls the tool, run retrieval, then stream the grounded answer.

    Yields:
        ("delta",   str)        — one text chunk of the answer
        ("sources", list[Row])  — the DB rows used (empty for direct answers)
    """
    # Step 1: let the LLM decide whether retrieval is needed
    first_response = await client.responses.create(
        model=settings.openai_chat_model,
        instructions=GENERAL_INSTRUCTIONS,
        input=question,
        tools=[SEARCH_TOOL],
        temperature=0.2,
    )

    tool_call = next(
        (item for item in first_response.output if item.type == "function_call"), None
    )

    if tool_call is None:
        # Conversational reply — no retrieval needed
        yield ("delta", first_response.output_text or "")
        yield ("sources", [])
        return

    # Step 2: retrieve relevant chunks
    args = json.loads(tool_call.arguments)
    chunks = await retrieve_chunks(db, args["query"])
    context = build_context(chunks) if chunks else "No relevant documents found."

    # Step 3: stream the grounded answer.
    # Use previous_response_id so the API resolves the full context (including
    # the function_call and any reasoning items) from the first response
    # server-side. We only need to provide the new tool output here.
    stream = await client.responses.create(
        model=settings.openai_chat_model,
        instructions=GROUNDED_INSTRUCTIONS,
        input=[{
            "type": "function_call_output",
            "call_id": tool_call.call_id,
            "output": context,
        }],
        previous_response_id=first_response.id,
        temperature=0.2,
        stream=True,
    )
    async for event in stream:
        if event.type == "response.output_text.delta":
            yield ("delta", event.delta)

    yield ("sources", chunks)
