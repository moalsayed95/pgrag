from fastmcp import FastMCP

mcp = FastMCP("ResourcesDemo")

DOCUMENTS = {
    "1": {"filename": "architecture.md", "chunks": 12, "created": "2025-01-15"},
    "2": {"filename": "api-guide.txt", "chunks": 8, "created": "2025-01-20"},
    "3": {"filename": "meeting-notes.md", "chunks": 3, "created": "2025-02-01"},
}


@mcp.resource("data://documents/list")
def list_documents() -> str:
    """List all documents in the knowledge base."""
    lines = []
    for doc_id, doc in DOCUMENTS.items():
        lines.append(f"[{doc_id}] {doc['filename']} ({doc['chunks']} chunks)")
    return "\n".join(lines)


@mcp.resource("data://documents/{doc_id}")
def get_document(doc_id: str) -> str:
    """Get details about a specific document by its ID."""
    doc = DOCUMENTS.get(doc_id)
    if not doc:
        return f"Document {doc_id} not found"
    return f"Filename: {doc['filename']}\nChunks: {doc['chunks']}\nCreated: {doc['created']}"


@mcp.resource("data://config/settings")
def get_settings() -> dict:
    """Current RAG pipeline configuration."""
    return {
        "embedding_model": "text-embedding-3-small",
        "chat_model": "gpt-4o-mini",
        "chunk_size": 500,
        "chunk_overlap": 100,
        "vector_dimensions": 1536,
    }


@mcp.tool
def search_docs(query: str) -> str:
    """Search documents (tool, not resource — because it performs an action)."""
    return f"Searching for: {query}"


if __name__ == "__main__":
    mcp.run()
