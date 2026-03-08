from openai import AsyncOpenAI
from pg_rag.config import get_settings

settings = get_settings()
client = AsyncOpenAI(api_key=settings.openai_api_key)


async def get_embedding(text: str) -> list[float]:
    """Generate embedding for a single text string."""
    response = await client.embeddings.create(
        input=text,
        model=settings.openai_embedding_model,
    )
    return response.data[0].embedding


async def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts in a single API call."""
    response = await client.embeddings.create(
        input=texts,
        model=settings.openai_embedding_model,
    )
    return [item.embedding for item in response.data]


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks by character count."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks
