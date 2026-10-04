import json
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from schemas import SourceDetailsResponse
from document_service import DATA_DIR

PROCESSED_DIR = DATA_DIR / "processed"

router = APIRouter(prefix="/sources", tags=["Sources"])

def find_chunk_in_processed(chunk_id: str):
    """Scan data/processed/*/chunks.json to locate a specific chunk_id."""
    if not PROCESSED_DIR.exists():
        return None

    for doc_dir in PROCESSED_DIR.iterdir():
        if doc_dir.is_dir():
            chunks_path = doc_dir / "chunks.json"
            if chunks_path.exists():
                try:
                    with open(chunks_path, "r", encoding="utf-8") as f:
                        chunks = json.load(f)
                        for chunk in chunks:
                            if chunk.get("chunk_id") == chunk_id:
                                return chunk
                except Exception:
                    continue
    return None

@router.get("/{chunk_id}", response_model=SourceDetailsResponse)
def get_source_details(chunk_id: str):
    """
    Retrieve comprehensive source metadata and text snippet for a chunk by chunk_id.
    """
    chunk = find_chunk_in_processed(chunk_id)
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source citation with chunk ID '{chunk_id}' not found."
        )

    doc_id = chunk.get("document_id", "")
    page_num = chunk.get("page_number", 1)

    return SourceDetailsResponse(
        chunk_id=chunk_id,
        document_id=doc_id,
        document_name=chunk.get("document_name", "BIS Document"),
        document_title=chunk.get("document_title"),
        standard_number=chunk.get("standard_number"),
        page_number=page_num,
        section=chunk.get("section", "Unknown"),
        clause=chunk.get("clause"),
        product_category=chunk.get("product_category"),
        source=chunk.get("source", ""),
        text=chunk.get("content", ""),
        pdf_url=f"/api/documents/{doc_id}/file#page={page_num}"
    )
