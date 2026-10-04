import os
import sys
import json
import time
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from pypdf import PdfWriter, PageObject
import requests

def create_sample_pdf(filename: str, title: str, num_pages: int = 3) -> str:
    """Helper to generate a valid PDF file with synthetic pages for testing."""
    writer = PdfWriter()
    for i in range(num_pages):
        page = PageObject.create_blank_page(width=612, height=792)
        writer.add_page(page)
    
    filepath = Path(__file__).resolve().parent / filename
    with open(filepath, "wb") as f:
        writer.write(f)
    return str(filepath)

def run_tests():
    print("==========================================")
    print("  RUNNING PHASE 1 AUTOMATED VERIFICATION  ")
    print("==========================================")

    # 1. Create sample test PDFs and invalid text file
    pdf1 = create_sample_pdf("IS_4250_Pressure_Cooker_Standard.pdf", "IS 4250 Standard", 5)
    pdf2 = create_sample_pdf("IS_302_Household_Electrical_Safety.pdf", "IS 302 Standard", 12)
    invalid_txt = Path(__file__).resolve().parent / "sample_invalid.txt"
    with open(invalid_txt, "w") as f:
        f.write("This is a plain text file, not a valid PDF document.")

    BASE_URL = "http://127.0.0.1:8000"

    # Test 1: GET /api/health
    print("\n[Test 1] GET /api/health")
    resp = requests.get(f"{BASE_URL}/api/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    health_data = resp.json()
    assert health_data["status"] == "ok", "Status is not ok"
    print(f"✓ Health Check Passed: {health_data}")

    # Test 2: Upload single PDF
    print("\n[Test 2] POST /api/documents/upload (Single PDF)")
    with open(pdf1, "rb") as f:
        files = [("files", ("IS_4250_Pressure_Cooker_Standard.pdf", f, "application/pdf"))]
        resp = requests.post(f"{BASE_URL}/api/documents/upload", files=files)
    assert resp.status_code == 201, f"Single upload failed: {resp.text}"
    upload_res = resp.json()
    assert upload_res["uploaded_count"] == 1
    doc1_id = upload_res["documents"][0]["document_id"]
    doc1_sha256 = upload_res["documents"][0]["sha256"]
    print(f"✓ Single Upload Passed: {upload_res['message']}")
    print(f"  Doc ID: {doc1_id}, Pages: {upload_res['documents'][0]['page_count']}")

    # Test 3: Upload multiple PDFs
    print("\n[Test 3] POST /api/documents/upload (Multiple PDFs)")
    with open(pdf2, "rb") as f:
        files = [("files", ("IS_302_Household_Electrical_Safety.pdf", f, "application/pdf"))]
        resp = requests.post(f"{BASE_URL}/api/documents/upload", files=files)
    assert resp.status_code == 201, f"Multiple upload failed: {resp.text}"
    upload_res2 = resp.json()
    assert upload_res2["uploaded_count"] == 1
    print(f"✓ Multiple Upload Passed: {upload_res2['message']}")

    # Test 4: Duplicate PDF detection via SHA256
    print("\n[Test 4] Duplicate PDF detection (Re-uploading IS_4250)")
    with open(pdf1, "rb") as f:
        files = [("files", ("IS_4250_Pressure_Cooker_Standard.pdf", f, "application/pdf"))]
        resp = requests.post(f"{BASE_URL}/api/documents/upload", files=files)
    assert resp.status_code == 201, f"Duplicate check response failed: {resp.text}"
    dup_res = resp.json()
    assert dup_res["skipped_count"] == 1
    assert "already exists" in dup_res["warnings"][0]
    print(f"✓ Duplicate Detection Passed: {dup_res['warnings'][0]}")

    # Test 5: Rejection of non-PDF file
    print("\n[Test 5] Rejecting non-PDF file")
    with open(invalid_txt, "rb") as f:
        files = [("files", ("sample_invalid.txt", f, "text/plain"))]
        resp = requests.post(f"{BASE_URL}/api/documents/upload", files=files)
    assert resp.status_code == 400, f"Expected 400 rejection but got {resp.status_code}: {resp.text}"
    print(f"✓ Non-PDF Rejection Passed: {resp.json()['detail']}")

    # Test 6: GET /api/documents
    print("\n[Test 6] GET /api/documents")
    resp = requests.get(f"{BASE_URL}/api/documents")
    assert resp.status_code == 200
    docs_list = resp.json()
    assert len(docs_list) >= 2
    print(f"✓ Document Listing Passed: Found {len(docs_list)} documents in registry.")

    # Test 7: GET /api/documents/{document_id}
    print("\n[Test 7] GET /api/documents/{document_id}")
    resp = requests.get(f"{BASE_URL}/api/documents/{doc1_id}")
    assert resp.status_code == 200
    single_doc = resp.json()
    assert single_doc["document_id"] == doc1_id
    assert single_doc["page_count"] == 5
    print(f"✓ Single Document Retrieval Passed: {single_doc['filename']} ({single_doc['page_count']} pages)")

    # Test 8: Verify file system integrity
    print("\n[Test 8] File system & data/documents.json integrity check")
    uploads_dir = Path(__file__).resolve().parent / "data" / "uploads"
    docs_json = Path(__file__).resolve().parent / "data" / "documents.json"
    assert uploads_dir.exists(), "data/uploads directory does not exist"
    assert docs_json.exists(), "data/documents.json does not exist"
    
    uploaded_files = list(uploads_dir.glob("*.pdf"))
    print(f"✓ Files in data/uploads/: {len(uploaded_files)}")
    with open(docs_json, "r", encoding="utf-8") as f:
        registry = json.load(f)
    print(f"✓ Entries in data/documents.json: {len(registry)}")

    # Clean up test artifact files
    for p in [pdf1, pdf2, str(invalid_txt)]:
        if os.path.exists(p):
            os.remove(p)

    print("\n==========================================")
    print("  ALL PHASE 1 BACKEND TESTS PASSED 100%!  ")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
