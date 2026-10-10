from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from typing import List
from schemas import DocumentMetadata, UploadResponse, ProcessDocumentResponse, IndexDocumentResponse
from document_service import (
    process_single_pdf,
    load_documents_db,
    get_document_by_id,
    UPLOADS_DIR
)
import os
import sys
import json
import shutil
from pathlib import Path
import qdrant_client

# Add services folder to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "services"))
from ingestion_service import process_document_pipeline
from indexing_service import index_document_pipeline

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Upload one or multiple PDF documents.
    - Validates PDF format
    - Saves original PDF unchanged
    - Calculates SHA256 checksum & page count
    - Prevents duplicates via SHA256 checksum match
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided for upload."
        )

    uploaded_docs = []
    warnings = []
    uploaded_count = 0
    skipped_count = 0

    for upload_file in files:
        content = await upload_file.read()
        filename = upload_file.filename or "file.pdf"

        doc_metadata, status_code, msg = process_single_pdf(filename, content)

        if status_code == "created":
            uploaded_count += 1
            uploaded_docs.append(DocumentMetadata(**doc_metadata))
        elif status_code == "duplicate":
            skipped_count += 1
            warnings.append(msg)
            if doc_metadata:
                uploaded_docs.append(DocumentMetadata(**doc_metadata))
        else: # invalid_file
            skipped_count += 1
            warnings.append(msg)

    if uploaded_count == 0 and skipped_count > 0 and len(uploaded_docs) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(warnings) if warnings else "Invalid files provided."
        )

    return UploadResponse(
        message=f"Upload completed. {uploaded_count} file(s) added, {skipped_count} skipped.",
        uploaded_count=uploaded_count,
        skipped_count=skipped_count,
        documents=uploaded_docs,
        warnings=warnings if warnings else None
    )

@router.post("/{document_id}/process", response_model=ProcessDocumentResponse)
def process_document(document_id: str):
    """
    Execute Phase 2 PDF ingestion, cleaning, section detection, metadata extraction,
    and structure-aware chunking for an uploaded document.
    """
    result, status_code = process_document_pipeline(document_id)
    if status_code != 200:
        raise HTTPException(
            status_code=status_code,
            detail=result.get("error", "Failed to process document.")
        )
    return ProcessDocumentResponse(**result)

@router.post("/{document_id}/index", response_model=IndexDocumentResponse)
def index_document(document_id: str):
    """
    Execute Phase 3 vector database indexing in Qdrant using SentenceTransformers.
    """
    result, status_code = index_document_pipeline(document_id)
    if status_code != 200:
        raise HTTPException(
            status_code=status_code,
            detail=result.get("error", "Failed to index document in vector store.")
        )
    return IndexDocumentResponse(**result)

@router.get("", response_model=List[DocumentMetadata])
def list_documents():
    """Retrieve all uploaded documents metadata from document registry."""
    raw_docs = load_documents_db()
    return [DocumentMetadata(**doc) for doc in raw_docs]

@router.get("/{document_id}", response_model=DocumentMetadata)
def get_document(document_id: str):
    """Retrieve detailed metadata for a specific document by document_id."""
    doc = get_document_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )
    return DocumentMetadata(**doc)

@router.get("/{document_id}/file")
def get_document_file(document_id: str):
    """
    Serve original uploaded PDF document file for browser preview / viewing.
    """
    doc = get_document_by_id(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )

    filename = doc.get("filename")
    safe_filename = f"{document_id}_{filename}"
    upload_path = UPLOADS_DIR / safe_filename

    if not upload_path.exists():
        upload_path = UPLOADS_DIR / filename
        if not upload_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PDF file for document '{document_id}' missing from disk."
            )

    return FileResponse(
        path=str(upload_path),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=\"{filename}\""}
    )

@router.delete("/wipe")
def wipe_all_documents():
    """Wipes all documents, uploaded files, and vector DB."""
    from document_service import DATA_DIR, UPLOADS_DIR, DOCUMENTS_JSON
    from vectorstore.qdrant_service import get_qdrant_client, get_collection_name

    # 1. Clear JSON DB
    if DOCUMENTS_JSON.exists():
        with open(DOCUMENTS_JSON, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)

    # 2. Delete all files in uploads
    if UPLOADS_DIR.exists():
        for file in UPLOADS_DIR.iterdir():
            if file.is_file():
                file.unlink()

    # 3. Wipe Qdrant
    try:
        q_client = get_qdrant_client()
        col_name = get_collection_name()
        q_client.delete_collection(collection_name=col_name)
        q_client.create_collection(
            collection_name=col_name,
            vectors_config=qdrant_client.models.VectorParams(size=384, distance=qdrant_client.models.Distance.COSINE)
        )
    except Exception as e:
        print(f"Error resetting Qdrant: {e}")

    return {"message": "All documents and vector stores have been wiped successfully."}

@router.delete("/{document_id}")
def delete_single_document(document_id: str):
    """Deletes a single document, its file, and its vectors from Qdrant."""
    from document_service import load_documents_db, save_documents_db, UPLOADS_DIR
    from vectorstore.qdrant_service import delete_document_chunks

    docs = load_documents_db()
    target_doc = next((d for d in docs if d.get("document_id") == document_id), None)
    if not target_doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 1. Remove from JSON DB
    docs = [d for d in docs if d.get("document_id") != document_id]
    save_documents_db(docs)

    # 2. Delete File
    filename = target_doc.get("filename")
    safe_filename = f"{document_id}_{filename}"
    upload_path = UPLOADS_DIR / safe_filename
    if upload_path.exists():
        upload_path.unlink()
    else:
        # Fallback for old files
        alt_path = UPLOADS_DIR / filename
        if alt_path.exists():
            alt_path.unlink()

    # 3. Delete from Vector DB
    try:
        delete_document_chunks(document_id)
    except Exception as e:
        print(f"Error deleting vectors for document {document_id}: {e}")

    return {"message": f"Document {document_id} deleted successfully."}

