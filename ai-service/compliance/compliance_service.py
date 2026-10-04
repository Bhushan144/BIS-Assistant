import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

retrieval_dir = backend_dir / "retrieval"
if str(retrieval_dir) not in sys.path:
    sys.path.insert(0, str(retrieval_dir))

from hybrid_service import hybrid_search
from retrieval.bm25_service import load_all_processed_chunks

def check_product_compliance(product_name: str) -> Dict[str, Any]:
    """
    Generate a structured BIS Product Compliance & Certification Report.
    Analyzes uploaded BIS standards and returns required testing, certification scheme, 
    and documentation checklists.
    """
    if not product_name or not product_name.strip():
        raise ValueError("Product name cannot be empty.")

    p_clean = product_name.strip()
    
    # Execute hybrid search for compliance rules
    chunks = hybrid_search(query=f"{p_clean} requirements tests certification marking safety", top_k=6)

    if not chunks:
        return {
            "product_name": p_clean,
            "compliance_status": "No Standard Found",
            "standard_number": None,
            "document_title": "No matching BIS Standard uploaded.",
            "certification_scheme": "Unknown",
            "mandatory_tests": [],
            "required_documents": [
                "Official BIS Standard Document (Upload PDF in Document Management)"
            ],
            "marking_requirements": "Marking requirements not available in uploaded documents."
        }

    # Extract standard number and doc title from top match
    top_chunk = chunks[0]
    std_num = top_chunk.get("standard_number") or "BIS Standard"
    doc_title = top_chunk.get("document_title") or top_chunk.get("document_name") or p_clean

    # Add LLM validation step to ensure retrieved chunks actually match the product requested
    try:
        from llm.llm_service import get_groq_client, get_groq_model
        client = get_groq_client()
        prompt = (
            f"You are a validation assistant. A user searched for the product: '{p_clean}'.\n"
            f"The search engine returned a document titled: '{doc_title}' (Standard: {std_num}).\n\n"
            f"Context from document: {chunks[0].get('text', '')[:500]}\n\n"
            f"Question: Does this document clearly and specifically cover the product '{p_clean}'? "
            f"Respond with exactly one word: YES or NO."
        )
        response = client.chat.completions.create(
            model=get_groq_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=10
        )
        answer = response.choices[0].message.content.strip().upper()
        if "NO" in answer:
            return {
                "product_name": p_clean,
                "compliance_status": "No Standard Found",
                "standard_number": None,
                "document_title": f"No matching BIS Standard found for '{p_clean}'.",
                "certification_scheme": "Unknown",
                "mandatory_tests": [],
                "required_documents": [
                    "Official BIS Standard Document (Upload PDF in Document Management)"
                ],
                "marking_requirements": "Marking requirements not available in uploaded documents."
            }
    except Exception as e:
        print(f"[Compliance Service] LLM Validation failed: {e}")
        # Proceed with heuristic extraction if validation fails

    # Aggregate extracted test names and requirements from matching chunks
    mandatory_tests = []
    required_docs = [
        "BIS Product Certification Application Form",
        "Factory Test Equipment Calibration Certificates",
        "Raw Material Test & Quality Inspection Reports",
        "Factory Layout Plan & Scheme of Inspection and Testing (SIT)"
    ]

    for c in chunks:
        text = c.get("text", "")
        # Search for test headers e.g. "5.1 High Voltage", "Insulation Test", "Pressure Release"
        for line in text.split("\n"):
            line_s = line.strip()
            if any(kw in line_s.lower() for kw in ["test", "resistance", "voltage", "pressure", "leakage", "temperature"]):
                if len(line_s) > 10 and len(line_s) < 120 and line_s not in mandatory_tests:
                    mandatory_tests.append(line_s)

    if not mandatory_tests:
        mandatory_tests = [
            "Electrical Safety & Insulation Resistance Test",
            "High Voltage Withstand Test",
            "Temperature Rise & Performance Test"
        ]

    return {
        "product_name": p_clean,
        "compliance_status": "Standard Found & Analyzed",
        "standard_number": std_num,
        "document_title": doc_title,
        "certification_scheme": "ISI Mark Certification (Scheme I - Type Testing & Factory Audit)",
        "mandatory_tests": mandatory_tests[:6],
        "required_documents": required_docs,
        "marking_requirements": f"Every unit shall be legibly marked with ISI Mark, Standard Number ({std_num}), Manufacturer Trademark, and Technical Ratings."
    }
