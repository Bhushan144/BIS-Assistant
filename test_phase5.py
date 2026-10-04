import sys
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from fastapi.testclient import TestClient
from main import app
from fpdf import FPDF

client = TestClient(app)

def create_food_mixer_pdf(filename: str) -> str:
    """Generate realistic test PDF for IS 4250 Electric Food Mixers."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Page 1: Cover & Scope
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "BUREAU OF INDIAN STANDARDS", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "INDIAN STANDARD IS 4250 : 2025", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "SPECIFICATION FOR ELECTRIC FOOD MIXERS AND GRINDERS", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 7, "1 Scope\nThis Indian Standard specifies electrical safety and performance requirements for domestic electric food mixers, juicers, and grinders.")

    # Page 2: Safety Requirements
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "4 Requirements", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 7, "4.1 Protection Against Electric Shock\nFood mixers shall be double insulated (Class II) or reliably earthed (Class I).\n\n4.2 Temperature Rise\nThe temperature rise of motor windings during normal operation shall not exceed 65 K.")

    filepath = Path(__file__).resolve().parent / filename
    pdf.output(str(filepath))
    return str(filepath)

def main():
    print("=============================================================")
    print("  RUNNING PHASE 5 CITATIONS & PDF SOURCE VIEWER TEST SUITE   ")
    print("=============================================================")

    pdf_path = create_food_mixer_pdf("IS_4250_Food_Mixer_Phase5.pdf")

    try:
        # Step 1: Ingest, Process, and Index PDF
        print("\n[Step 1] Upload, Process, & Index Test BIS Document")
        with open(pdf_path, "rb") as f:
            res_up = client.post("/api/documents/upload", files=[("files", ("IS_4250_Food_Mixer_Phase5.pdf", f, "application/pdf"))])
        assert res_up.status_code == 201
        doc_id = res_up.json()["documents"][0]["document_id"]
        
        client.post(f"/api/documents/{doc_id}/process")
        client.post(f"/api/documents/{doc_id}/index")
        print(f"  [OK] Ingested document ID: {doc_id}")

        # Step 2: Test PDF File Serving Endpoint GET /api/documents/{document_id}/file
        print(f"\n[Step 2] GET /api/documents/{doc_id}/file (PDF File Server)")
        res_file = client.get(f"/api/documents/{doc_id}/file")
        assert res_file.status_code == 200, f"File serving failed: {res_file.text}"
        assert res_file.headers["content-type"] == "application/pdf"
        assert len(res_file.content) > 100
        print(f"  [OK] Served PDF file successfully: {len(res_file.content)} bytes, Content-Type: application/pdf")

        # Step 3: Test RAG Query Citation Payload Format filtered by document_id
        print("\n[Step 3] POST /api/rag/query - Checking Source Citation Payload")
        mock_answer = "Food mixers must be double insulated (Class II) or earthed (Class I)."
        
        with patch("llm_service.get_groq_client") as mock_client:
            mock_cmpl = MagicMock()
            mock_cmpl.choices = [MagicMock(message=MagicMock(content=mock_answer))]
            mock_client.return_value.chat.completions.create.return_value = mock_cmpl

            res_rag = client.post("/api/rag/query", json={"query": "electrical safety food mixer", "top_k": 3, "document_id": doc_id})
            assert res_rag.status_code == 200
            body = res_rag.json()
            assert len(body["sources"]) > 0
            
            first_src = body["sources"][0]
            print("  [OK] RAG Source Citation Payload:")
            print(json.dumps(first_src, indent=2))

            # Verify required fields
            req_keys = ["document_id", "document_name", "standard_number", "page_number", "section", "clause", "chunk_id", "snippet", "pdf_url"]
            for k in req_keys:
                assert k in first_src, f"Missing citation key '{k}'"

            assert first_src["document_id"] == doc_id
            chunk_id = first_src["chunk_id"]

        # Step 4: Test Source Details Lookup Endpoint GET /api/sources/{chunk_id}
        print(f"\n[Step 4] GET /api/sources/{chunk_id} (Source Chunk Lookup)")
        res_source = client.get(f"/api/sources/{chunk_id}")
        assert res_source.status_code == 200, f"Source details failed: {res_source.text}"
        src_details = res_source.json()
        print("  [OK] Source Details Returned:")
        print(json.dumps(src_details, indent=2))

        assert src_details["chunk_id"] == chunk_id
        assert src_details["document_id"] == doc_id
        assert len(src_details["text"]) > 0
        assert src_details["pdf_url"].startswith(f"/api/documents/{doc_id}/file")

        print("\n=============================================================")
        print("  ALL PHASE 5 CITATION & SOURCE VIEWER TESTS PASSED 100%!    ")
        print("=============================================================")

    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

if __name__ == "__main__":
    main()
