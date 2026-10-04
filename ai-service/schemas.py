from pydantic import BaseModel, Field
from typing import List, Optional

class DocumentMetadata(BaseModel):
    document_id: str = Field(..., description="Unique UUID for the document")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    page_count: int = Field(..., description="Total pages in PDF document")
    sha256: str = Field(..., description="SHA256 checksum of the PDF file")
    uploaded_at: str = Field(..., description="ISO 8601 upload timestamp")
    status: str = Field(default="uploaded", description="Processing status (uploaded | processing | processed | indexing | indexed | error)")
    chunk_count: int = Field(default=0, description="Total structure-aware chunks generated")
    indexed_chunk_count: int = Field(default=0, description="Total chunks indexed in ChromaDB vector database")
    pages_with_text: Optional[int] = Field(default=None, description="Pages containing extractable text")
    standard_number: Optional[str] = Field(default=None, description="Detected Indian Standard number (e.g. IS 4250)")
    document_title: Optional[str] = Field(default=None, description="Extracted document title")
    product_category: Optional[str] = Field(default=None, description="Inferred product category")
    processed_at: Optional[str] = Field(default=None, description="ISO timestamp when processing completed")
    indexed_at: Optional[str] = Field(default=None, description="ISO timestamp when vector indexing completed")
    error: Optional[str] = Field(default=None, description="Error message if processing or indexing failed")

class ProcessDocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    page_count: int
    pages_with_text: int
    chunk_count: int
    standard_number: Optional[str] = None
    product_category: Optional[str] = None

class IndexDocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    chunk_count: int
    indexed_chunk_count: int

class UploadResponse(BaseModel):
    message: str
    uploaded_count: int
    skipped_count: int
    documents: List[DocumentMetadata]
    warnings: Optional[List[str]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str

# --- Phase 4 & Phase 5 Citation & Source Models ---

class RagSourceMetadata(BaseModel):
    document_id: str
    document_name: str
    standard_number: Optional[str] = None
    page_number: int
    section: str
    clause: Optional[str] = None
    chunk_id: str
    snippet: str = Field(..., description="Retrieved text excerpt / snippet")
    pdf_url: str = Field(..., description="API endpoint URL to view original PDF file at page")

class SourceDetailsResponse(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    document_title: Optional[str] = None
    standard_number: Optional[str] = None
    page_number: int
    section: str
    clause: Optional[str] = None
    product_category: Optional[str] = None
    source: str
    text: str
    pdf_url: str

class RagQueryRequest(BaseModel):
    query: str = Field(..., description="User question about BIS standards")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Top-k chunks to retrieve")
    document_id: Optional[str] = Field(default=None, description="Optional document UUID filter")
    chat_history: Optional[List[dict]] = Field(default=None, description="Previous conversation messages (role, content)")

class RagQueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[RagSourceMetadata]
    retrieved_chunks: int
