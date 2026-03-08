import uuid
from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from pg_rag.database import get_db
from pg_rag.models import Document, DocumentChunk
from pg_rag.schemas import DocumentOut
from pg_rag.embeddings import chunk_text, get_embeddings

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut)
async def upload_document(file: UploadFile, db: AsyncSession = Depends(get_db)):
    """Upload a text/PDF file, chunk it, embed it, and store everything."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content = (await file.read()).decode("utf-8", errors="ignore")

    # Create document record
    doc = Document(id=uuid.uuid4(), filename=file.filename, content=content)
    db.add(doc)

    # Chunk and embed
    chunks = chunk_text(content)
    embeddings = await get_embeddings(chunks)

    for i, (chunk_text_str, embedding) in enumerate(zip(chunks, embeddings)):
        chunk = DocumentChunk(
            id=uuid.uuid4(),
            document_id=doc.id,
            content=chunk_text_str,
            chunk_index=i,
            embedding=embedding,
        )
        db.add(chunk)

    await db.commit()
    await db.refresh(doc)

    return DocumentOut(
        id=doc.id,
        filename=doc.filename,
        created_at=doc.created_at,
        chunk_count=len(chunks),
    )


@router.get("/", response_model=list[DocumentOut])
async def list_documents(db: AsyncSession = Depends(get_db)):
    """List all uploaded documents."""
    stmt = (
        select(
            Document.id,
            Document.filename,
            Document.created_at,
            func.count(DocumentChunk.id).label("chunk_count"),
        )
        .outerjoin(DocumentChunk)
        .group_by(Document.id)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        DocumentOut(id=r.id, filename=r.filename, created_at=r.created_at, chunk_count=r.chunk_count)
        for r in rows
    ]
