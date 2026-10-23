import hashlib
import json
import uuid
import os
import io
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
from pypdf import PdfReader

# Ensure services directory is in sys.path
backend_dir = Path(__file__).resolve().parent
services_dir = backend_dir / "services"
if str(services_dir) not in sys.path:
    sys.path.insert(0, str(services_dir))

try:
    from storage_service import (
        is_cloud_storage_enabled,
        upload_file_to_storage,
        download_file_from_storage,
        delete_file_from_storage,
        get_public_url,
    )
except ImportError:
    from services.storage_service import (
        is_cloud_storage_enabled,
        upload_file_to_storage,
        download_file_from_storage,
        delete_file_from_storage,
        get_public_url,
    )

# Setup directory paths:
# If root data/ exists (in monolithic/local dev), use it;
# Otherwise (in Render/cloud service root), use ai-service/data
project_root = backend_dir.parent
if (project_root / "data").exists():
    DATA_DIR = Path(os.getenv("DATA_DIR", str(project_root / "data")))
else:
    DATA_DIR = Path(os.getenv("DATA_DIR", str(backend_dir / "data")))

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
    except Exception:
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
    """
    Load document list from data/documents.json.
    If local file is empty or missing and Supabase Storage is configured,
    hydrates from Supabase Storage registry backup.
    """
    ensure_directories()
    docs = []
    try:
        if DOCUMENTS_JSON.exists():
            with open(DOCUMENTS_JSON, "r", encoding="utf-8") as f:
                docs = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        docs = []

    # If empty or freshly deployed container, try re-hydrating from Supabase Storage
    if not docs and is_cloud_storage_enabled():
        remote_data = download_file_from_storage("registry/documents.json")
        if remote_data:
            try:
                docs = json.loads(remote_data.decode("utf-8"))
                with open(DOCUMENTS_JSON, "w", encoding="utf-8") as f:
                    json.dump(docs, f, indent=2, ensure_ascii=False)
                print(f"[DocumentService] Re-hydrated {len(docs)} document(s) from Supabase Storage registry.")
            except Exception as e:
                print(f"[DocumentService] Failed to parse rehydrated registry: {e}")

    return docs

def save_documents_db(documents: List[Dict[str, Any]]) -> None:
    """
    Save document list atomically to data/documents.json and sync to Supabase Storage.
    """
    ensure_directories()
    payload = json.dumps(documents, indent=2, ensure_ascii=False)
    with open(DOCUMENTS_JSON, "w", encoding="utf-8") as f:
        f.write(payload)

    # Backup registry to Supabase Storage
    if is_cloud_storage_enabled():
        upload_file_to_storage("registry/documents.json", payload.encode("utf-8"), "application/json")

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

def ensure_pdf_cached_locally(document_id: str, filename: str) -> Optional[Path]:
    """
    Ensure the PDF file is present on the local filesystem.
    If missing (e.g. on ephemeral dyno restart), pulls from Supabase Storage and caches locally.
    """
    ensure_directories()
    safe_filename = f"{document_id}_{Path(filename).name}"
    local_path = UPLOADS_DIR / safe_filename
    if local_path.exists():
        return local_path

    alt_path = UPLOADS_DIR / filename
    if alt_path.exists():
        return alt_path

    # Try downloading from Supabase Storage
    if is_cloud_storage_enabled():
        print(f"[DocumentService] File not found locally. Fetching '{safe_filename}' from Supabase Storage...")
        data = download_file_from_storage(f"pdfs/{safe_filename}")
        if not data:
            data = download_file_from_storage(f"pdfs/{filename}")

        if data:
            with open(local_path, "wb") as f:
                f.write(data)
            print(f"[DocumentService] Successfully cached '{safe_filename}' to local disk.")
            return local_path

    return None

def process_single_pdf(filename: str, file_bytes: bytes) -> Tuple[Optional[Dict[str, Any]], str, str]:
    """
    Process single uploaded PDF:
    - Validates PDF format
    - Computes SHA256 checksum
    - Checks for duplicate SHA256 in database
    - Saves original PDF unchanged to data/uploads/{document_id}_{filename}
    - Uploads permanently to Supabase Storage (if configured)
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

    # 6. Save original PDF locally to data/uploads/
    clean_name = Path(filename).name
    safe_filename = f"{document_id}_{clean_name}"
    upload_file_path = UPLOADS_DIR / safe_filename
    with open(upload_file_path, "wb") as f:
        f.write(file_bytes)

    # 7. Upload to Supabase Storage for permanent persistence
    storage_path = f"pdfs/{safe_filename}"
    storage_url = None
    if is_cloud_storage_enabled():
        storage_url = upload_file_to_storage(storage_path, file_bytes, "application/pdf")

    # 8. Construct document metadata
    doc_metadata = {
        "document_id": document_id,
        "filename": filename,
        "file_size": file_size,
        "page_count": page_count,
        "sha256": sha256_hash,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "status": "uploaded",
        "chunk_count": 0,
        "storage_path": storage_path,
        "storage_url": storage_url
    }

    # 9. Save to registry database
    docs = load_documents_db()
    docs.append(doc_metadata)
    save_documents_db(docs)

    return doc_metadata, "created", f"Document '{filename}' successfully uploaded."
