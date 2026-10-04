import sys
import json
import os
import shutil
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from fastapi.testclient import TestClient
from main import app
from fpdf import FPDF

client = TestClient(app)

def create_real_bis_pdf(filename: str) -> str:
    """Generate a valid realistic BIS Standard PDF using FPDF for testing."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Page 1: Cover & Scope
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "BUREAU OF INDIAN STANDARDS", ln=True)
    pdf.cell(0, 10, "INDIAN STANDARD IS 4250 : 2025", ln=True)
    pdf.cell(0, 10, "SPECIFICATION FOR ELECTRIC FOOD MIXERS AND GRINDERS", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 7, "1 Scope\nThis Indian Standard specifies electrical safety and performance requirements for domestic electric food mixers, juicers, and grinders.")

    # Page 2: Safety Requirements
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "4 Requirements", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 7, "4.1 Protection Against Electric Shock\nFood mixers shall be double insulated (Class II) or reliably earthed (Class I).\n\n4.2 Temperature Rise\nThe temperature rise of motor windings during normal operation shall not exceed 65 K.")

    # Page 3: Testing Procedures
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "5 Tests", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 7, "5.1 High Voltage Withstand Test\nA high voltage of 1500 V AC at 50 Hz shall be applied between live parts and enclosure for 60 seconds without flashover or insulation breakdown.\n\n5.2 Moisture Resistance Test\nMixer body shall withstand splash testing for 10 minutes without water entering electrical compartments.")

    filepath = Path(__file__).resolve().parent / filename
    pdf.output(str(filepath))
    return str(filepath)

def main():
    print("=============================================================")
    print("  RUNNING PHASE 3 EMBEDDINGS & CHROMADB VERIFICATION SUITE   ")
    print("=============================================================")

    pdf_path = create_real_bis_pdf("IS_4250_Food_Mixer_Standard.pdf")

    try:
        # Test 1: Upload PDF
        print("\n[Test 1] POST /api/documents/upload")
        with open(pdf_path, "rb") as f:
            res = client.post("/api/documents/upload", files=[("files", ("IS_4250_Food_Mixer_Standard.pdf", f, "application/pdf"))])
        assert res.status_code == 201, f"Upload failed: {res.text}"
        doc_id = res.json()["documents"][0]["document_id"]
        print(f"  [OK] Uploaded document ID: {doc_id}")

        # Test 2: Process Document (Phase 2)
        print(f"\n[Test 2] POST /api/documents/{doc_id}/process")
        res_proc = client.post(f"/api/documents/{doc_id}/process")
        assert res_proc.status_code == 200, f"Processing failed: {res_proc.text}"
        proc_body = res_proc.json()
        assert proc_body["status"] == "processed"
        assert proc_body["chunk_count"] > 0
        print(f"  [OK] Phase 2 processing complete: {proc_body['chunk_count']} chunks created.")

        # Test 3: Index Document in ChromaDB (Phase 3)
        print(f"\n[Test 3] POST /api/documents/{doc_id}/index")
        res_idx = client.post(f"/api/documents/{doc_id}/index")
        assert res_idx.status_code == 200, f"Indexing failed: {res_idx.text}"
        idx_body = res_idx.json()
        assert idx_body["status"] == "indexed"
        assert idx_body["indexed_chunk_count"] == proc_body["chunk_count"]
        print(f"  [OK] Indexed into ChromaDB: {idx_body['indexed_chunk_count']} chunks stored as vectors.")

        # Test 4: Verify ChromaDB directory persistence
        print("\n[Test 4] ChromaDB persistence directory check")
        chroma_dir = Path(__file__).resolve().parent / "data" / "chroma"
        assert chroma_dir.exists(), "ChromaDB directory data/chroma/ does not exist"
        print(f"  [OK] ChromaDB persistent database directory exists at: {chroma_dir}")

        # Test 5: Perform Vector Search via POST /api/search
        query_str = "What high voltage insulation test is required for food mixers?"
        print(f"\n[Test 5] POST /api/search with query: '{query_str}'")
        res_search = client.post("/api/search", json={"query": query_str, "top_k": 3})
        assert res_search.status_code == 200, f"Search failed: {res_search.text}"
        search_body = res_search.json()
        results = search_body["results"]
        assert len(results) > 0, "No search results returned"
        print(f"  [OK] Vector search returned {len(results)} matching chunks.")

        # Test 6: Verify metadata fields present in search result
        print("\n[Test 6] Metadata completeness check on top result:")
        top_result = results[0]
        print(json.dumps(top_result, indent=2))
        
        required_meta = ["chunk_id", "document_id", "document_name", "page_number", "section", "standard_number", "product_category", "score", "text"]
        for k in required_meta:
            assert k in top_result, f"Missing metadata field '{k}'"
        print("  [OK] All required metadata fields present!")

        # Test 7: Re-indexing deduplication test
        print(f"\n[Test 7] Re-indexing document '{doc_id}' to verify no duplicates are created")
        res_reindex = client.post(f"/api/documents/{doc_id}/index")
        assert res_reindex.status_code == 200
        reindex_body = res_reindex.json()
        assert reindex_body["indexed_chunk_count"] == proc_body["chunk_count"]
        
        # Verify collection result length remains stable
        res_search_after = client.post("/api/search", json={"query": query_str, "top_k": 10})
        assert len(res_search_after.json()["results"]) == len(results)
        print("  [OK] Re-indexing test passed: Stable vector count preserved, no duplicates created.")

        print("\n=============================================================")
        print("  ALL PHASE 3 EMBEDDINGS & CHROMADB TESTS PASSED 100%!       ")
        print("=============================================================")

    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

if __name__ == "__main__":
    main()
