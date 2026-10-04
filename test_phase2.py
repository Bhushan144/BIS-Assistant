import sys
import json
import os
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from fastapi.testclient import TestClient
from main import app
import fitz  # PyMuPDF

client = TestClient(app)

def create_rich_bis_pdf(filename: str, include_empty_page: bool = False) -> str:
    """Helper to generate a realistic synthetic BIS standard PDF with PyMuPDF."""
    doc = fitz.open()

    # Page 1: Cover & Foreword
    p1 = doc.new_page(width=612, height=792)
    p1.insert_text((50, 50), "BUREAU OF INDIAN STANDARDS\nINDIAN STANDARD\nIS 4250 : 2025\n\nELECTRIC FOOD MIXERS - SPECIFICATION")
    p1.insert_text((50, 150), "Foreword\nThis Indian Standard (Second Revision) was adopted by the Bureau of Indian Standards.")

    # Page 2: 1 Scope & 2 References
    p2 = doc.new_page(width=612, height=792)
    p2.insert_text((50, 50), "1 Scope\nThis standard specifies the safety and performance requirements for electric food mixers, food processors, and grinders intended for household use.\nOperating voltage shall not exceed 250 V AC.")
    p2.insert_text((50, 200), "2 References\nIS 302-1 : 2024 Safety of household electrical appliances - General requirements.")

    # Page 3: 4 Requirements
    p3 = doc.new_page(width=612, height=792)
    p3.insert_text((50, 50), "4 Requirements\n4.1 General\nMixers shall be constructed so as to ensure safety in normal use.\n4.2 Protection Against Electric Shock\nEnclosures shall provide adequate protection against accidental contact with live parts.")

    # Page 4: 5 Tests
    p4 = doc.new_page(width=612, height=792)
    p4.insert_text((50, 50), "5 Tests\n5.1 Insulation Resistance Test\nInsulation resistance measured with 500 V DC shall be not less than 2 M-ohms.\n5.2 High Voltage Test\nAn AC voltage of 1500 V shall be applied for 1 minute without breakdown.")

    # Page 5: Optional Empty Page
    if include_empty_page:
        p5 = doc.new_page(width=612, height=792)
        # Blank page (no text)

    filepath = Path(__file__).resolve().parent / filename
    doc.save(str(filepath))
    doc.close()
    return str(filepath)

def main():
    print("=========================================================")
    print("  RUNNING PHASE 2 INGESTION & CHUNKING VERIFICATION SUITE")
    print("=========================================================")

    pdf_path = create_rich_bis_pdf("IS_4250_Test_Doc.pdf", include_empty_page=True)

    try:
        # Step 1: Upload PDF
        print("\n[Step 1] Upload PDF to document registry")
        with open(pdf_path, "rb") as f:
            res = client.post("/api/documents/upload", files=[("files", ("IS_4250_Test_Doc.pdf", f, "application/pdf"))])
        assert res.status_code == 201, f"Upload failed: {res.text}"
        doc_info = res.json()["documents"][0]
        doc_id = doc_info["document_id"]
        print(f"  ✓ Uploaded document ID: {doc_id}")

        # Step 2: Trigger POST /api/documents/{document_id}/process
        print(f"\n[Step 2] POST /api/documents/{doc_id}/process")
        res_proc = client.post(f"/api/documents/{doc_id}/process")
        assert res_proc.status_code == 200, f"Processing failed: {res_proc.text}"
        proc_data = res_proc.json()
        assert proc_data["status"] == "processed"
        assert proc_data["page_count"] == 5
        assert proc_data["pages_with_text"] == 4  # Page 5 was empty
        assert proc_data["chunk_count"] > 0
        assert proc_data["standard_number"] == "IS 4250:2025"
        print(f"  ✓ Processed successfully:")
        print(f"    - Status: {proc_data['status']}")
        print(f"    - Total Pages: {proc_data['page_count']}")
        print(f"    - Pages with Text: {proc_data['pages_with_text']}")
        print(f"    - Chunks Created: {proc_data['chunk_count']}")
        print(f"    - Standard Number: {proc_data['standard_number']}")

        # Step 3: Verify GET /api/documents updated registry metadata
        print("\n[Step 3] GET /api/documents metadata inspection")
        res_list = client.get("/api/documents")
        assert res_list.status_code == 200
        doc_in_list = [d for d in res_list.json() if d["document_id"] == doc_id][0]
        assert doc_in_list["status"] == "processed"
        assert doc_in_list["chunk_count"] == proc_data["chunk_count"]
        assert doc_in_list["standard_number"] == "IS 4250:2025"
        print("  ✓ Document registry status updated to 'processed' with chunk count!")

        # Step 4: Verify storage files data/processed/{doc_id}/pages.json & chunks.json
        print("\n[Step 4] Verify processed files on disk")
        proc_dir = Path(__file__).resolve().parent / "data" / "processed" / doc_id
        pages_file = proc_dir / "pages.json"
        chunks_file = proc_dir / "chunks.json"

        assert pages_file.exists(), "pages.json file missing"
        assert chunks_file.exists(), "chunks.json file missing"

        with open(pages_file, "r", encoding="utf-8") as f:
            pages_list = json.load(f)
        with open(chunks_file, "r", encoding="utf-8") as f:
            chunks_list = json.load(f)

        assert len(pages_list) == 5
        print(f"  ✓ Verified data/processed/{doc_id}/pages.json ({len(pages_list)} page objects)")
        print(f"  ✓ Verified data/processed/{doc_id}/chunks.json ({len(chunks_list)} chunk objects)")

        # Step 5: Inspect a generated chunk structure and metadata
        print("\n[Step 5] Detailed Inspection of Generated Chunk:")
        sample_chunk = chunks_list[0]
        print(json.dumps(sample_chunk, indent=2))

        # Check metadata fields requirement
        required_keys = ["chunk_id", "document_id", "document_name", "page_number", "section", "standard_number", "content"]
        for key in required_keys:
            assert key in sample_chunk, f"Missing key '{key}' in generated chunk"

        print("\n=========================================================")
        print("  ALL PHASE 2 VERIFICATION TESTS PASSED 100%!           ")
        print("=========================================================")

    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

if __name__ == "__main__":
    main()
