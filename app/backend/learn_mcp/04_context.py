from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastmcp import FastMCP, Context


@dataclass
class FakeDB:
    connected: bool = False
    documents: dict = None

    def __post_init__(self):
        self.documents = {
            "1": {"filename": "test.txt", "content": "Hello world"},
            "2": {"filename": "guide.md", "content": "MCP is a protocol for LLMs"},
        }


@asynccontextmanager
async def app_lifespan(server: FastMCP):
    db = FakeDB(connected=True)
    print("DB connected!")
    try:
        yield {"db": db}
    finally:
        db.connected = False
        print("DB disconnected!")


mcp = FastMCP("ContextDemo", lifespan=app_lifespan)


@mcp.tool
async def list_documents(ctx: Context) -> str:
    """List all documents in the database."""
    db: FakeDB = ctx.request_context.lifespan_context["db"]
    if not db.connected:
        return "Error: database not connected"

    lines = []
    for doc_id, doc in db.documents.items():
        lines.append(f"[{doc_id}] {doc['filename']}")

    await ctx.info(f"Found {len(db.documents)} documents")
    return "\n".join(lines)


@mcp.tool
async def get_document(doc_id: str, ctx: Context) -> str:
    """Get a document by ID from the database."""
    db: FakeDB = ctx.request_context.lifespan_context["db"]
    doc = db.documents.get(doc_id)
    if not doc:
        return f"Document {doc_id} not found"
    return f"Filename: {doc['filename']}\nContent: {doc['content']}"


@mcp.tool
async def add_document(filename: str, content: str, ctx: Context) -> str:
    """Add a new document to the database."""
    db: FakeDB = ctx.request_context.lifespan_context["db"]
    new_id = str(max(int(k) for k in db.documents) + 1)
    db.documents[new_id] = {"filename": filename, "content": content}
    await ctx.info(f"Added document {new_id}: {filename}")
    return f"Document '{filename}' added with ID {new_id}"


if __name__ == "__main__":
    mcp.run()
