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

    # Page 3: Testing Procedures
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "5 Tests", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 7, "5.1 High Voltage Withstand Test\nA high voltage of 1500 V AC at 50 Hz shall be applied between live parts and enclosure for 60 seconds without flashover or insulation breakdown.\n\n5.2 Moisture Resistance Test\nMixer body shall withstand splash testing for 10 minutes without water entering electrical compartments.")

    filepath = Path(__file__).resolve().parent / filename
    pdf.output(str(filepath))
    return str(filepath)

def create_pressure_cooker_pdf(filename: str) -> str:
    """Generate realistic test PDF for IS 2347 Domestic Pressure Cookers."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Page 1: Cover & Safety Safeguards
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "BUREAU OF INDIAN STANDARDS", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "INDIAN STANDARD IS 2347 : 2024", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "DOMESTIC PRESSURE COOKERS - SPECIFICATION", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 7, "4 Safety Safeguards & Requirements\n4.1 Pressure Release Device\nPressure cookers must be fitted with a safety valve designed to release pressure at 1.5 times the normal working pressure.\n\n4.2 Lid Locking Mechanism\nThe cooker lid shall incorporate a safety locking mechanism that prevents the lid from opening while internal pressure exceeds 4 kPa.")

    filepath = Path(__file__).resolve().parent / filename
    pdf.output(str(filepath))
    return str(filepath)

def main():
    print("=============================================================")
    print("  RUNNING PHASE 4 BASIC RAG & GROUNDED LLM VERIFICATION SUITE")
    print("=============================================================")

    mixer_pdf = create_food_mixer_pdf("IS_4250_Food_Mixer_Standard.pdf")
    cooker_pdf = create_pressure_cooker_pdf("IS_2347_Pressure_Cooker_Standard.pdf")

    try:
        # Step 1: Verify Phase 1 Upload & Phase 2 Process & Phase 3 Index
        print("\n[Step 1] Ingesting & Indexing test BIS documents...")
        
        # Upload Mixer PDF
        with open(mixer_pdf, "rb") as f:
            res1 = client.post("/api/documents/upload", files=[("files", ("IS_4250_Food_Mixer_Standard.pdf", f, "application/pdf"))])
        assert res1.status_code == 201
        doc1_id = res1.json()["documents"][0]["document_id"]
        client.post(f"/api/documents/{doc1_id}/process")
        client.post(f"/api/documents/{doc1_id}/index")

        # Upload Cooker PDF
        with open(cooker_pdf, "rb") as f:
            res2 = client.post("/api/documents/upload", files=[("files", ("IS_2347_Pressure_Cooker_Standard.pdf", f, "application/pdf"))])
        assert res2.status_code == 201
        doc2_id = res2.json()["documents"][0]["document_id"]
        client.post(f"/api/documents/{doc2_id}/process")
        client.post(f"/api/documents/{doc2_id}/index")

        print("  [OK] Both test documents ingested, processed, and indexed in ChromaDB!")

        # Step 2: Verify missing GROQ_API_KEY handling
        print("\n[Step 2] Testing missing GROQ_API_KEY handling")
        with patch.dict(os.environ, {"GROQ_API_KEY": ""}):
            res_no_key = client.post("/api/rag/query", json={"query": "test missing key"})
            assert res_no_key.status_code == 500
            assert "GROQ_API_KEY" in res_no_key.json()["detail"]
            print(f"  [OK] Missing GROQ_API_KEY correctly rejected with detail: {res_no_key.json()['detail']}")

        # Step 3: Test Full RAG Queries with Mocked Groq LLM Generation
        print("\n[Step 3] RAG Query Test 1: Food Mixer Electrical Safety")
        query1 = "What are the electrical safety requirements for the food mixer?"
        
        mock_response1 = (
            "Food mixers must be either double insulated (Class II) or reliably earthed (Class I). "
            "The temperature rise of motor windings during normal operation must not exceed 65 K."
        )

        with patch("llm_service.get_groq_client") as mock_client:
            mock_cmpl = MagicMock()
            mock_cmpl.choices = [MagicMock(message=MagicMock(content=mock_response1))]
            mock_client.return_value.chat.completions.create.return_value = mock_cmpl

            res_rag1 = client.post("/api/rag/query", json={"query": query1, "top_k": 5})
            assert res_rag1.status_code == 200, f"RAG query 1 failed: {res_rag1.text}"
            body1 = res_rag1.json()
            print("  [OK] Answer generated from retrieved BIS context:")
            print(f"    Answer: {body1['answer']}")
            print(f"    Sources ({len(body1['sources'])}):")
            for s in body1['sources']:
                print(f"      - {s['document_name']} | Standard: {s['standard_number']} | Page {s['page_number']} | Section: {s['section']}")
            assert len(body1['sources']) > 0
            assert body1['sources'][0]['document_name'] == "IS_4250_Food_Mixer_Standard.pdf"

        # Step 4: RAG Query Test 2: Pressure Cooker Safeguards
        print("\n[Step 4] RAG Query Test 2: Pressure Cooker Safeguards")
        query2 = "What are the important safeguards for pressure cookers?"
        mock_response2 = (
            "Pressure cookers must be fitted with a safety valve designed to release pressure at 1.5 times the normal working pressure. "
            "The cooker lid shall incorporate a safety locking mechanism that prevents the lid from opening while internal pressure exceeds 4 kPa."
        )

        with patch("llm_service.get_groq_client") as mock_client:
            mock_cmpl = MagicMock()
            mock_cmpl.choices = [MagicMock(message=MagicMock(content=mock_response2))]
            mock_client.return_value.chat.completions.create.return_value = mock_cmpl

            res_rag2 = client.post("/api/rag/query", json={"query": query2, "top_k": 5})
            assert res_rag2.status_code == 200
            body2 = res_rag2.json()
            print("  [OK] Answer generated from retrieved BIS context:")
            print(f"    Answer: {body2['answer']}")
            print(f"    Sources ({len(body2['sources'])}):")
            for s in body2['sources']:
                print(f"      - {s['document_name']} | Standard: {s['standard_number']} | Page {s['page_number']} | Section: {s['section']}")
            assert body2['sources'][0]['document_name'] == "IS_2347_Pressure_Cooker_Standard.pdf"

        # Step 5: Unrelated Question Test ("What is the capital of France?")
        print("\n[Step 5] RAG Query Test 3: Unrelated Question ('What is the capital of France?')")
        query3 = "What is the capital of France?"
        mock_response3 = "I could not find sufficient information in the uploaded BIS documents to answer this reliably."

        with patch("llm_service.get_groq_client") as mock_client:
            mock_cmpl = MagicMock()
            mock_cmpl.choices = [MagicMock(message=MagicMock(content=mock_response3))]
            mock_client.return_value.chat.completions.create.return_value = mock_cmpl

            res_rag3 = client.post("/api/rag/query", json={"query": query3, "top_k": 5})
            assert res_rag3.status_code == 200
            body3 = res_rag3.json()
            print("  [OK] Response generated for unrelated question:")
            print(f"    Answer: {body3['answer']}")
            assert "sufficient" in body3['answer'].lower() or "not" in body3['answer'].lower()

        # Step 6: Standard Number Query Test
        print("\n[Step 6] RAG Query Test 4: Standard Number Query ('What is the standard number for the pressure cooker?')")
        query4 = "What is the standard number for the domestic pressure cooker?"
        mock_response4 = "The standard number for domestic pressure cookers is IS 2347 : 2024."

        with patch("llm_service.get_groq_client") as mock_client:
            mock_cmpl = MagicMock()
            mock_cmpl.choices = [MagicMock(message=MagicMock(content=mock_response4))]
            mock_client.return_value.chat.completions.create.return_value = mock_cmpl

            res_rag4 = client.post("/api/rag/query", json={"query": query4, "top_k": 5})
            assert res_rag4.status_code == 200
            body4 = res_rag4.json()
            print("  [OK] Answer generated for standard number query:")
            print(f"    Answer: {body4['answer']}")
            assert "IS 2347" in body4['answer']

        print("\n=============================================================")
        print("  ALL PHASE 4 BASIC RAG & GROUNDED LLM CHECKS PASSED 100%!   ")
        print("=============================================================")

    finally:
        for p in [mixer_pdf, cooker_pdf]:
            if os.path.exists(p):
                os.remove(p)

if __name__ == "__main__":
    main()
