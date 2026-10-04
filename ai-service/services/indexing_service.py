import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

vectorstore_dir = backend_dir / "vectorstore"
if str(vectorstore_dir) not in sys.path:
    sys.path.insert(0, str(vectorstore_dir))

from qdrant_service import add_chunks_to_vectorstore
from document_service import (
    load_documents_db,
    save_documents_db,
    get_document_by_id,
    DATA_DIR
)

PROCESSED_DIR = DATA_DIR / "processed"

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

def index_document_pipeline(document_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Execute Phase 3 vector database indexing pipeline for a processed document:
    1. Verify document registry entry & chunks.json existence
    2. Set status to 'indexing'
    3. Load processed chunks from data/processed/{document_id}/chunks.json
    4. Generate embeddings via SentenceTransformer and upsert into ChromaDB
    5. Set status to 'indexed' and record indexed_chunk_count
    """
    doc = get_document_by_id(document_id)
    if not doc:
        return {"error": f"Document with ID '{document_id}' not found."}, 404

    chunks_file_path = PROCESSED_DIR / document_id / "chunks.json"

    if not chunks_file_path.exists():
        update_document_status_db(document_id, {
            "status": "error",
            "error": "Processed chunks missing. Please run PDF processing (Phase 2) first."
        })
        return {
            "error": f"Processed chunks missing for document '{document_id}'. Please process document first."
        }, 400

    # Step 1: Set status to 'indexing'
    update_document_status_db(document_id, {"status": "indexing"})

    try:
        # Step 2: Load chunks from Phase 2
        with open(chunks_file_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        if not chunks:
            update_document_status_db(document_id, {
                "status": "error",
                "error": "No valid text chunks found in document."
            })
            return {"error": "Document contains no valid text chunks to index."}, 400

        # Step 3: Embed & upsert into ChromaDB vectorstore
        indexed_count = add_chunks_to_vectorstore(chunks)

        # Step 4: Update document status in registry DB to 'indexed'
        status_updates = {
            "status": "indexed",
            "chunk_count": len(chunks),
            "indexed_chunk_count": indexed_count,
            "indexed_at": datetime.now(timezone.utc).isoformat()
        }
        updated_doc = update_document_status_db(document_id, status_updates)

        return {
            "document_id": document_id,
            "filename": doc.get("filename"),
            "status": "indexed",
            "chunk_count": len(chunks),
            "indexed_chunk_count": indexed_count
        }, 200

    except Exception as e:
        error_msg = f"Failed during vector DB indexing: {str(e)}"
        print(f"[Indexing Error] {error_msg}")
        update_document_status_db(document_id, {
            "status": "error",
            "error": error_msg
        })
        return {"error": error_msg, "document_id": document_id, "status": "error"}, 500
