import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import httpx

# Supabase Storage Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "bis-documents")

_bucket_checked = False

def is_cloud_storage_enabled() -> bool:
    """Check if Supabase Storage is configured via environment variables."""
    return bool(SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL.strip() and SUPABASE_KEY.strip())

def _get_headers(content_type: Optional[str] = None) -> Dict[str, str]:
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apiKey": SUPABASE_KEY,
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers

def _get_api_url(path: str) -> str:
    base = SUPABASE_URL.rstrip("/")
    return f"{base}/storage/v1/{path.lstrip('/')}"

def ensure_bucket_exists(bucket_name: str = SUPABASE_BUCKET) -> bool:
    """Ensure the target bucket exists in Supabase Storage. Creates it as public if not."""
    global _bucket_checked
    if not is_cloud_storage_enabled():
        return False
    if _bucket_checked:
        return True

    try:
        url = _get_api_url("bucket")
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{url}/{bucket_name}", headers=_get_headers())
            if resp.status_code == 200:
                _bucket_checked = True
                return True

            # Bucket does not exist, create it
            payload = {"id": bucket_name, "name": bucket_name, "public": True}
            create_resp = client.post(url, headers=_get_headers("application/json"), json=payload)
            if create_resp.status_code in (200, 201):
                _bucket_checked = True
                print(f"[StorageService] Created Supabase Storage bucket '{bucket_name}'.")
                return True
            else:
                print(f"[StorageService] Warning: Could not create bucket '{bucket_name}': {create_resp.text}")
                return False
    except Exception as e:
        print(f"[StorageService] Warning: ensure_bucket_exists check failed: {e}")
        return False

def upload_file_to_storage(
    storage_path: str,
    file_bytes: bytes,
    content_type: str = "application/pdf",
    bucket_name: str = SUPABASE_BUCKET
) -> Optional[str]:
    """Upload a file or object to Supabase Storage with upsert enabled."""
    if not is_cloud_storage_enabled():
        return None

    try:
        ensure_bucket_exists(bucket_name)
        url = _get_api_url(f"object/{bucket_name}/{storage_path}")
        headers = _get_headers(content_type)
        headers["x-upsert"] = "true"

        with httpx.Client(timeout=45.0) as client:
            resp = client.post(url, headers=headers, content=file_bytes)
            if resp.status_code in (200, 201):
                public_url = get_public_url(storage_path, bucket_name)
                print(f"[StorageService] Successfully uploaded '{storage_path}' to Supabase Storage.")
                return public_url
            else:
                print(f"[StorageService] Upload failed for '{storage_path}' ({resp.status_code}): {resp.text}")
                return None
    except Exception as e:
        print(f"[StorageService] Error uploading '{storage_path}': {e}")
        return None

def download_file_from_storage(
    storage_path: str,
    bucket_name: str = SUPABASE_BUCKET
) -> Optional[bytes]:
    """Download raw file bytes from Supabase Storage."""
    if not is_cloud_storage_enabled():
        return None

    try:
        # Try authenticated endpoint first
        url = _get_api_url(f"object/authenticated/{bucket_name}/{storage_path}")
        with httpx.Client(timeout=45.0) as client:
            resp = client.get(url, headers=_get_headers())
            if resp.status_code == 200:
                return resp.content

            # Fallback to public endpoint
            pub_url = _get_api_url(f"object/public/{bucket_name}/{storage_path}")
            pub_resp = client.get(pub_url)
            if pub_resp.status_code == 200:
                return pub_resp.content

            return None
    except Exception as e:
        print(f"[StorageService] Error downloading '{storage_path}': {e}")
        return None

def delete_file_from_storage(
    storage_path: str,
    bucket_name: str = SUPABASE_BUCKET
) -> bool:
    """Delete a file object from Supabase Storage."""
    if not is_cloud_storage_enabled():
        return False

    try:
        url = _get_api_url(f"object/{bucket_name}/{storage_path}")
        with httpx.Client(timeout=15.0) as client:
            resp = client.delete(url, headers=_get_headers())
            return resp.status_code in (200, 204)
    except Exception as e:
        print(f"[StorageService] Error deleting '{storage_path}': {e}")
        return False

def get_public_url(storage_path: str, bucket_name: str = SUPABASE_BUCKET) -> str:
    """Construct public URL for an object in Supabase Storage."""
    if not is_cloud_storage_enabled():
        return ""
    base = SUPABASE_URL.rstrip("/")
    return f"{base}/storage/v1/object/public/{bucket_name}/{storage_path}"
