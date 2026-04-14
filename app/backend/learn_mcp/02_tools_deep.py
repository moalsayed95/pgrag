from pydantic import BaseModel, Field
from fastmcp import FastMCP

mcp = FastMCP("ToolsDemo")


@mcp.tool
def search(query: str, max_results: int = 5) -> str:
    """Search for documents matching a query."""
    return f"Found {max_results} results for '{query}'"


class DocumentInput(BaseModel):
    filename: str = Field(description="Name of the document file")
    content: str = Field(description="Raw text content of the document")
    tags: list[str] = Field(default_factory=list, description="Optional tags for categorization")


@mcp.tool
def ingest_document(doc: DocumentInput) -> dict:
    """Ingest a new document into the knowledge base."""
    return {
        "status": "ingested",
        "filename": doc.filename,
        "chunks": len(doc.content) // 500,  # fake chunking
        "tags": doc.tags,
    }


@mcp.tool
async def analyze_text(text: str) -> dict:
    """Analyze text and return basic statistics."""
    words = text.split()
    return {
        "word_count": len(words),
        "char_count": len(text),
        "unique_words": len(set(words)),
    }


@mcp.tool
def list_available_models() -> list[dict]:
    """List the AI models available for chat and embeddings."""
    return [
        {"name": "gpt-4o-mini", "purpose": "chat", "context_window": 128000},
        {"name": "text-embedding-3-small", "purpose": "embeddings", "dimensions": 1536},
    ]


@mcp.tool(
    annotations={"readOnlyHint": True, "openWorldHint": False},
)
def get_chunk_settings() -> dict:
    """Get the current chunking configuration."""
    return {"chunk_size": 500, "chunk_overlap": 100}


if __name__ == "__main__":
    mcp.run()
