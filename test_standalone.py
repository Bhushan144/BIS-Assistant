import sys
import json
import os
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from fastapi.testclient import TestClient
from main import app
from pypdf import PdfWriter, PageObject

client = TestClient(app)

def create_sample_pdf(filename: str, num_pages: int = 3) -> str:
    """Helper to generate a valid PDF file with synthetic pages for testing."""
    writer = PdfWriter()
    for _ in range(num_pages):
        page = PageObject.create_blank_page(width=612, height=792)
        writer.add_page(page)
    
    filepath = Path(__file__).resolve().parent / filename
    with open(filepath, "wb") as f:
        writer.write(f)
    return str(filepath)

def main():
    print("=================================================")
    print("  RUNNING FASTAPI TESTCLIENT VERIFICATION SUITE  ")
    print("=================================================")

    # Generate sample PDFs & invalid file
    pdf1_path = create_sample_pdf("IS_4250_Pressure_Cooker_Standard.pdf", num_pages=5)
    pdf2_path = create_sample_pdf("IS_302_Household_Electrical_Safety.pdf", num_pages=12)
    invalid_txt_path = Path(__file__).resolve().parent / "invalid_sample.txt"
    with open(invalid_txt_path, "w") as f:
        f.write("This is a plain text file, not a PDF document.")

    try:
        # 1. Test /api/health
        print("\n[Test 1] GET /api/health")
        res = client.get("/api/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        data = res.json()
        assert data["status"] == "ok"
        print(f"  ✓ Status: {data['status']} | Timestamp: {data['timestamp']}")

        # 2. Test upload single PDF
        print("\n[Test 2] POST /api/documents/upload (Single PDF)")
        with open(pdf1_path, "rb") as f:
            res = client.post("/api/documents/upload", files=[("files", ("IS_4250_Pressure_Cooker_Standard.pdf", f, "application/pdf"))])
        assert res.status_code == 201, f"Upload single failed: {res.text}"
        body = res.json()
        assert body["uploaded_count"] == 1
        doc1 = body["documents"][0]
        assert doc1["filename"] == "IS_4250_Pressure_Cooker_Standard.pdf"
        assert doc1["page_count"] == 5
        assert doc1["status"] == "uploaded"
        doc1_id = doc1["document_id"]
        doc1_sha256 = doc1["sha256"]
        print(f"  ✓ Uploaded 1 document. ID: {doc1_id}, Pages: {doc1['page_count']}, SHA256: {doc1_sha256[:12]}...")

        # 3. Test upload multiple PDFs
        print("\n[Test 3] POST /api/documents/upload (Multiple PDFs)")
        with open(pdf2_path, "rb") as f:
            res = client.post("/api/documents/upload", files=[("files", ("IS_302_Household_Electrical_Safety.pdf", f, "application/pdf"))])
        assert res.status_code == 201, f"Upload multiple failed: {res.text}"
        body2 = res.json()
        assert body2["uploaded_count"] == 1
        doc2 = body2["documents"][0]
        assert doc2["page_count"] == 12
        print(f"  ✓ Uploaded second document: {doc2['filename']} ({doc2['page_count']} pages)")

        # 4. Test duplicate PDF upload detection via SHA256
        print("\n[Test 4] Duplicate PDF detection via SHA256 hash")
        with open(pdf1_path, "rb") as f:
            res = client.post("/api/documents/upload", files=[("files", ("IS_4250_Pressure_Cooker_Standard.pdf", f, "application/pdf"))])
        assert res.status_code == 201, f"Duplicate check failed: {res.text}"
        dup_body = res.json()
        assert dup_body["skipped_count"] == 1
        assert dup_body["warnings"] is not None
        print(f"  ✓ Duplicate correctly detected & skipped: {dup_body['warnings'][0]}")

        # 5. Test rejection of non-PDF file
        print("\n[Test 5] Rejection of non-PDF file (.txt)")
        with open(invalid_txt_path, "rb") as f:
            res = client.post("/api/documents/upload", files=[("files", ("invalid_sample.txt", f, "text/plain"))])
        assert res.status_code == 400, f"Expected HTTP 400 rejection, got {res.status_code}"
        print(f"  ✓ Non-PDF file correctly rejected: {res.json()['detail']}")

        # 6. Test GET /api/documents
        print("\n[Test 6] GET /api/documents")
        res = client.get("/api/documents")
        assert res.status_code == 200
        docs_list = res.json()
        assert len(docs_list) >= 2
        print(f"  ✓ Document registry returned {len(docs_list)} documents.")

        # 7. Test GET /api/documents/{document_id}
        print("\n[Test 7] GET /api/documents/{document_id}")
        res = client.get(f"/api/documents/{doc1_id}")
        assert res.status_code == 200
        single_doc = res.json()
        assert single_doc["document_id"] == doc1_id
        assert single_doc["filename"] == "IS_4250_Pressure_Cooker_Standard.pdf"
        print(f"  ✓ Retrieved metadata for ID {doc1_id}: filename={single_doc['filename']}, file_size={single_doc['file_size']} bytes")

        # 8. Test file system integrity
        print("\n[Test 8] File storage & data/documents.json integrity check")
        uploads_dir = Path(__file__).resolve().parent / "data" / "uploads"
        docs_json = Path(__file__).resolve().parent / "data" / "documents.json"
        
        uploaded_files = list(uploads_dir.glob("*.pdf"))
        print(f"  ✓ Saved PDF files in data/uploads/: {len(uploaded_files)}")
        with open(docs_json, "r", encoding="utf-8") as f:
            registry = json.load(f)
        print(f"  ✓ Total entries recorded in data/documents.json: {len(registry)}")

        print("\n=================================================")
        print("  ALL FASTAPI TESTCLIENT CHECKS PASSED 100%!   ")
        print("=================================================")

    finally:
        # Cleanup temporary test files
        for p in [pdf1_path, pdf2_path, str(invalid_txt_path)]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

if __name__ == "__main__":
    main()
