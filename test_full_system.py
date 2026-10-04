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

def safe_print(text: str):
    """Safely print unicode strings on Windows cp1252 terminal."""
    try:
        print(text)
    except Exception:
        print(text.encode("ascii", errors="replace").decode("ascii"))

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

    # Page 3: Testing Procedures
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "5 Tests", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 7, "5.1 High Voltage Withstand Test\nA high voltage of 1500 V AC at 50 Hz shall be applied between live parts and enclosure for 60 seconds without flashover or insulation breakdown.\n\n5.2 Moisture Resistance Test\nMixer body shall withstand splash testing for 10 minutes without water entering electrical compartments.")

    filepath = Path(__file__).resolve().parent / filename
    pdf.output(str(filepath))
    return str(filepath)

def main():
    safe_print("=============================================================")
    safe_print("  RUNNING FULL-STACK BIS ASSISTANT MASTER SYSTEM TEST SUITE  ")
    safe_print("=============================================================")

    pdf_path = create_food_mixer_pdf("IS_4250_Master_Test_Doc.pdf")

    try:
        # Step 1: Ingest, Process, and Index PDF
        safe_print("\n[Test 1] Phase 1 Upload -> Phase 2 Process -> Phase 3 ChromaDB Index")
        with open(pdf_path, "rb") as f:
            res_up = client.post("/api/documents/upload", files=[("files", ("IS_4250_Master_Test_Doc.pdf", f, "application/pdf"))])
        assert res_up.status_code == 201
        doc_id = res_up.json()["documents"][0]["document_id"]
        
        client.post(f"/api/documents/{doc_id}/process")
        client.post(f"/api/documents/{doc_id}/index")
        safe_print(f"  [OK] Ingested document ID: {doc_id}")

        # Step 2: Phase 6 Hybrid Search (Vector + BM25 Fusion)
        safe_print("\n[Test 2] Phase 6 Hybrid Vector + BM25 Search")
        res_search = client.post("/api/search", json={"query": "insulation resistance high voltage test", "top_k": 3})
        assert res_search.status_code == 200
        assert res_search.json()["results_count"] > 0
        safe_print(f"  [OK] Hybrid search returned {res_search.json()['results_count']} results.")

        # Step 3: Phase 7 LangGraph Agent RAG Query Workflow (English)
        safe_print("\n[Test 3] Phase 7 LangGraph RAG Agent Query (English)")
        mock_answer_en = "Food mixers must be double insulated (Class II) or reliably earthed (Class I). The temperature rise shall not exceed 65 K."

        with patch("llm_service.get_groq_client") as mock_client:
            mock_cmpl = MagicMock()
            mock_cmpl.choices = [MagicMock(message=MagicMock(content=mock_answer_en))]
            mock_client.return_value.chat.completions.create.return_value = mock_cmpl

            res_rag_en = client.post("/api/rag/query", json={"query": "What are the electrical safety requirements for food mixers?", "top_k": 3, "language": "English", "document_id": doc_id})
            assert res_rag_en.status_code == 200
            body_en = res_rag_en.json()
            safe_print("  [OK] RAG Answer (English):")
            safe_print(f"    Answer: {body_en['answer']}")
            assert len(body_en["sources"]) > 0
            assert "pdf_url" in body_en["sources"][0]
            assert "snippet" in body_en["sources"][0]

        # Step 4: Phase 8 Multilingual Engine (Hindi & Marathi)
        safe_print("\n[Test 4] Phase 8 Multilingual Engine (Hindi Output)")
        mock_answer_hi = "फूड मिक्सर दोहरे इंसुलेटेड (Class II) या अर्थ्ड (Class I) होने चाहिए। मोटर वाइंडिंग का तापमान 65 K से अधिक नहीं होना चाहिए।"

        with patch("llm_service.get_groq_client") as mock_client:
            mock_cmpl = MagicMock()
            mock_cmpl.choices = [MagicMock(message=MagicMock(content=mock_answer_hi))]
            mock_client.return_value.chat.completions.create.return_value = mock_cmpl

            res_rag_hi = client.post("/api/rag/query", json={"query": "फूड मिक्सर के सुरक्षा नियम क्या हैं?", "top_k": 3, "language": "Hindi", "document_id": doc_id})
            assert res_rag_hi.status_code == 200
            body_hi = res_rag_hi.json()
            safe_print("  [OK] RAG Answer (Hindi generated):")
            safe_print(f"    Answer: {body_hi['answer']}")

        # Step 5: Phase 9 BIS Product Compliance Inspector Report
        safe_print("\n[Test 5] Phase 9 BIS Compliance Inspector Report")
        res_comp = client.post("/api/compliance/check", json={"product_name": "Food Mixer"})
        assert res_comp.status_code == 200
        comp_body = res_comp.json()
        safe_print("  [OK] BIS Compliance Inspection Report:")
        safe_print(f"    Product: {comp_body['product_name']}")
        safe_print(f"    Standard Number: {comp_body['standard_number']}")
        safe_print(f"    Certification Scheme: {comp_body['certification_scheme']}")
        safe_print(f"    Mandatory Tests: {comp_body['mandatory_tests']}")
        assert comp_body["standard_number"] == "IS 4250"

        # Step 6: Phase 5 PDF File Server & Citation Details Lookup
        safe_print(f"\n[Test 6] Phase 5 GET /api/documents/{doc_id}/file & GET /api/sources/...")
        res_file = client.get(f"/api/documents/{doc_id}/file")
        assert res_file.status_code == 200
        assert res_file.headers["content-type"] == "application/pdf"

        chunk_id = body_en["sources"][0]["chunk_id"]
        res_src = client.get(f"/api/sources/{chunk_id}")
        assert res_src.status_code == 200
        assert res_src.json()["chunk_id"] == chunk_id
        safe_print("  [OK] PDF File Server & Source Lookup working 100%!")

        safe_print("\n=============================================================")
        safe_print("  FULL-STACK BIS ASSISTANT SYSTEM TEST PASSED 100%! SUCCESS! ")
        safe_print("=============================================================")

    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

if __name__ == "__main__":
    main()
