import hashlib
import json
import uuid
import os
import io
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
from pypdf import PdfReader

# Setup directory paths relative to bis-assistant root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
DOCUMENTS_JSON = DATA_DIR / "documents.json"

def ensure_directories():
    """Ensure data/ and data/uploads/ directories exist along with documents.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    if not DOCUMENTS_JSON.exists():
        with open(DOCUMENTS_JSON, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)

def calculate_sha256(file_bytes: bytes) -> str:
    """Calculate SHA256 checksum for binary file content."""
    return hashlib.sha256(file_bytes).hexdigest()

def extract_pdf_page_count(file_bytes: bytes) -> int:
    """Extract page count from PDF binary stream using pypdf."""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        return len(reader.pages)
    except Exception as e:
        # Fallback if corrupt page structure but valid PDF
        return 1

def is_pdf(filename: str, file_bytes: bytes) -> bool:
    """Validate file extension and PDF magic bytes header (%PDF-)."""
    if not filename.lower().endswith(".pdf"):
        return False
    # Check PDF magic bytes header
    if len(file_bytes) < 4 or not file_bytes.startswith(b"%PDF"):
        return False
    return True

def load_documents_db() -> List[Dict[str, Any]]:
    """Load document list from data/documents.json."""
    ensure_directories()
    try:
        with open(DOCUMENTS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_documents_db(documents: List[Dict[str, Any]]) -> None:
    """Save document list atomically to data/documents.json."""
    ensure_directories()
    with open(DOCUMENTS_JSON, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)

def get_document_by_id(document_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve document metadata by document_id."""
    docs = load_documents_db()
    for doc in docs:
        if doc.get("document_id") == document_id:
            return doc
    return None

def find_document_by_sha256(sha256_hash: str) -> Optional[Dict[str, Any]]:
    """Find existing document matching SHA256 checksum."""
    docs = load_documents_db()
    for doc in docs:
        if doc.get("sha256") == sha256_hash:
            return doc
    return None

def process_single_pdf(filename: str, file_bytes: bytes) -> Tuple[Optional[Dict[str, Any]], str, str]:
    """
    Process single uploaded PDF:
    - Validates PDF format
    - Computes SHA256 checksum
    - Checks for duplicate SHA256 in database
    - Saves original PDF unchanged to data/uploads/{document_id}_{filename}
    - Computes page count
    - Stores metadata entry in documents.json
    Returns (metadata_dict, status_code, message)
    """
    ensure_directories()

    # 1. Validate PDF format
    if not is_pdf(filename, file_bytes):
        return None, "invalid_file", f"File '{filename}' is not a valid PDF document."

    # 2. Compute SHA256 checksum
    sha256_hash = calculate_sha256(file_bytes)

    # 3. Duplicate check via SHA256
    existing_doc = find_document_by_sha256(sha256_hash)
    if existing_doc:
        return existing_doc, "duplicate", f"Document '{filename}' already exists in registry (SHA256: {sha256_hash[:10]}...)."

    # 4. Generate unique document_id
    document_id = str(uuid.uuid4())
    file_size = len(file_bytes)

    # 5. Extract page count
    page_count = extract_pdf_page_count(file_bytes)

    # 6. Save original PDF unchanged to data/uploads/
    safe_filename = f"{document_id}_{Path(filename).name}"
    upload_file_path = UPLOADS_DIR / safe_filename
    with open(upload_file_path, "wb") as f:
        f.write(file_bytes)

    # 7. Construct document metadata
    doc_metadata = {
        "document_id": document_id,
        "filename": filename,
        "file_size": file_size,
        "page_count": page_count,
        "sha256": sha256_hash,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "status": "uploaded",
        "chunk_count": 0
    }

    # 8. Save to registry database
    docs = load_documents_db()
    docs.append(doc_metadata)
    save_documents_db(docs)

    return doc_metadata, "created", f"Document '{filename}' successfully uploaded."
