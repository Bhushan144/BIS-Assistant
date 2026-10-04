import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Any

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

vectorstore_dir = backend_dir / "vectorstore"
if str(vectorstore_dir) not in sys.path:
    sys.path.insert(0, str(vectorstore_dir))

from vectorstore.qdrant_service import similarity_search

router = APIRouter(prefix="/search", tags=["Vector Search"])

class SearchRequest(BaseModel):
    query: str = Field(..., description="BIS query string to search in vector database")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of top matching chunks to retrieve")
    document_id: Optional[str] = Field(default=None, description="Optional document UUID filter")

class SearchResultChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    document_title: Optional[str] = None
    page_number: int
    section: str
    clause: Optional[str] = None
    standard_number: Optional[str] = None
    product_category: Optional[str] = None
    source: str
    text: str
    score: float

class SearchResponse(BaseModel):
    query: str
    top_k: int
    results_count: int
    results: List[SearchResultChunk]

@router.post("", response_model=SearchResponse)
def vector_search(req: SearchRequest):
    """
    Execute vector similarity search in ChromaDB using sentence-transformers embedding.
    Returns top-k matching BIS text chunks with page, section, and standard metadata.
    Does NOT call any LLM.
    """
    if not req.query or not req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty."
        )

    try:
        raw_results = similarity_search(
            query=req.query.strip(),
            top_k=req.top_k,
            document_id=req.document_id
        )

        formatted_results = [SearchResultChunk(**res) for res in raw_results]

        return SearchResponse(
            query=req.query,
            top_k=req.top_k,
            results_count=len(formatted_results),
            results=formatted_results
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector search failed: {str(e)}"
        )
