import uuid
from datetime import datetime
from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    created_at: datetime
    chunk_count: int = 0

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    question: str


class SourceChunk(BaseModel):
    content: str
    chunk_index: int
    document_filename: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
