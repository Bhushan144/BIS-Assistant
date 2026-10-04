import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

ingestion_dir = backend_dir / "ingestion"
if str(ingestion_dir) not in sys.path:
    sys.path.insert(0, str(ingestion_dir))

from pdf_extractor import extract_pages_from_pdf
from metadata_extractor import extract_document_metadata
from chunker import create_chunks_from_pages
from document_service import (
    load_documents_db,
    save_documents_db,
    get_document_by_id,
    UPLOADS_DIR,
    DATA_DIR
)

PROCESSED_DIR = DATA_DIR / "processed"

def ensure_processed_directory(document_id: str) -> Path:
    """Ensure data/processed/{document_id}/ directory exists."""
    doc_proc_dir = PROCESSED_DIR / document_id
    doc_proc_dir.mkdir(parents=True, exist_ok=True)
    return doc_proc_dir

def update_document_status_db(document_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update metadata fields for a document in documents.json registry."""
    docs = load_documents_db()
    updated_doc = None
    for doc in docs:
        if doc.get("document_id") == document_id:
            doc.update(updates)
            updated_doc = doc
            break
    if updated_doc:
        save_documents_db(docs)
    return updated_doc

def process_document_pipeline(document_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Execute full Phase 2 ingestion pipeline for an uploaded PDF document:
    1. Set status to 'processing'
    2. Read original PDF from data/uploads/
    3. Extract page-by-page text
    4. Detect document metadata & standard numbers
    5. Generate structure-aware chunks with metadata
    6. Save pages.json and chunks.json under data/processed/{document_id}/
    7. Update documents.json registry status to 'processed'
    """
    doc = get_document_by_id(document_id)
    if not doc:
        return {"error": f"Document with ID '{document_id}' not found."}, 404

    filename = doc.get("filename")
    safe_filename = f"{document_id}_{filename}"
    upload_file_path = UPLOADS_DIR / safe_filename

    if not upload_file_path.exists():
        # Fallback search if saved without prefix
        upload_file_path = UPLOADS_DIR / filename
        if not upload_file_path.exists():
            update_document_status_db(document_id, {"status": "error", "error": "Original PDF file missing from disk."})
            return {"error": f"Original PDF file for document '{document_id}' missing from uploads directory."}, 404

    # Step 1: Set status to 'processing'
    update_document_status_db(document_id, {"status": "processing"})

    try:
        # Step 2: Extract text page by page
        pages_data = extract_pages_from_pdf(str(upload_file_path))
        pages_with_text_count = len([p for p in pages_data if p.get("char_count", 0) > 0])

        # Step 3: Metadata extraction
        metadata = extract_document_metadata(pages_data, filename)
        std_number = metadata.get("standard_number")
        doc_title = metadata.get("document_title", filename)
        product_cat = metadata.get("product_category", "Unknown")

        # Step 4: Generate structure-aware chunks
        chunks_data = create_chunks_from_pages(
            pages_data=pages_data,
            document_id=document_id,
            document_name=filename,
            document_title=doc_title,
            standard_number=std_number,
            product_category=product_cat
        )

        # Step 5: Save processed pages and chunks JSON files
        proc_dir = ensure_processed_directory(document_id)
        
        pages_json_path = proc_dir / "pages.json"
        with open(pages_json_path, "w", encoding="utf-8") as f:
            json.dump(pages_data, f, indent=2, ensure_ascii=False)

        chunks_json_path = proc_dir / "chunks.json"
        with open(chunks_json_path, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)

        # Step 6: Update document registry DB with success status & counts
        status_updates = {
            "status": "processed",
            "page_count": len(pages_data),
            "pages_with_text": pages_with_text_count,
            "chunk_count": len(chunks_data),
            "standard_number": std_number,
            "document_title": doc_title,
            "product_category": product_cat,
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
        updated_doc = update_document_status_db(document_id, status_updates)

        return {
            "document_id": document_id,
            "filename": filename,
            "status": "processed",
            "page_count": len(pages_data),
            "pages_with_text": pages_with_text_count,
            "chunk_count": len(chunks_data),
            "standard_number": std_number,
            "product_category": product_cat
        }, 200

    except Exception as e:
        error_msg = f"Failed during document processing: {str(e)}"
        print(f"[Processing Error] {error_msg}")
        update_document_status_db(document_id, {
            "status": "error",
            "error": error_msg
        })
        return {"error": error_msg, "document_id": document_id, "status": "error"}, 500
