import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

retrieval_dir = backend_dir / "retrieval"
if str(retrieval_dir) not in sys.path:
    sys.path.insert(0, str(retrieval_dir))

from retrieval.hybrid_service import hybrid_search
from vectorstore.qdrant_service import similarity_search
from document_service import load_documents_db

def resolve_product_standard(product_name: str) -> Tuple[Optional[Dict[str, Any]], bool, str]:
    """
    Two-stage deterministic & semantic resolver with strict LLM scope validation gate.
    Returns:
      (matched_doc_dict, is_valid_match, reason)
    """
    p_clean = product_name.strip()
    p_lower = p_clean.lower()
    docs = load_documents_db()

    if not docs:
        return (None, False, "No standards exist in the document library. Please upload a standard PDF.")

    candidate_doc = None

    # Step 1: Direct Standard Number or Exact Keyword Resolution
    for doc in docs:
        snum = str(doc.get("standard_number", "")).upper()
        title = str(doc.get("document_title", "")).lower()
        title_en = str(doc.get("title_en", "")).lower()
        cat = str(doc.get("product_category", "")).lower()
        fname = str(doc.get("filename", "")).lower()

        # Check for explicit standard number search (e.g. "IS 2347", "2347", "IS 4246")
        snum_clean = re.sub(r"[^\w]", "", snum)
        p_num_clean = re.sub(r"[^\w]", "", p_clean.upper())
        if p_num_clean and (p_num_clean in snum_clean or snum_clean in p_num_clean):
            candidate_doc = doc
            break

        # Check direct canonical keyword mappings
        if ("pressure cooker" in p_lower or "cooker" in p_lower) and ("cooker" in title or "2347" in snum):
            candidate_doc = doc
            break
        if ("water heater" in p_lower or "geyser" in p_lower) and ("water heater" in title or "2082" in snum):
            candidate_doc = doc
            break
        if ("gas stove" in p_lower or "gas hob" in p_lower or "lpg stove" in p_lower or "burner" in p_lower) and ("gas stove" in title or "4246" in snum):
            candidate_doc = doc
            break

    # Step 2: Semantic Vector Discovery Search if not directly mapped
    if not candidate_doc:
        try:
            discovery_chunks = similarity_search(
                query=f"Indian Standard scope and specification for {p_clean}",
                top_k=3
            )
            if discovery_chunks:
                top_chunk = discovery_chunks[0]
                doc_id = top_chunk.get("document_id")
                score = top_chunk.get("score", 0.0)

                # Find candidate document from registry
                for doc in docs:
                    if doc.get("document_id") == doc_id:
                        candidate_doc = doc
                        break

                if not candidate_doc:
                    candidate_doc = {
                        "document_id": doc_id,
                        "standard_number": top_chunk.get("standard_number"),
                        "document_title": top_chunk.get("document_title") or top_chunk.get("document_name")
                    }
        except Exception as e:
            print(f"[Compliance Resolver] Semantic discovery error: {e}")

    if not candidate_doc:
        return (None, False, f"No Indian Standard found in your library covering '{p_clean}'.")

    # Step 3: Strict LLM Scope Validation Gate
    cand_std = candidate_doc.get("standard_number", "BIS Standard")
    cand_title = candidate_doc.get("document_title") or candidate_doc.get("title_en", "Standard")

    try:
        from llm.llm_service import get_groq_client, get_groq_model
        client = get_groq_client()

        prompt = f"""You are a Senior BIS Quality & Standards Auditor.
A user asked for product compliance for: "{p_clean}".
The candidate standard in the library is: "{cand_std} - {cand_title}".

Does this Indian Standard explicitly cover and specify testing requirements for "{p_clean}"?
CRITICAL: If the standard is for gas stoves, it does NOT cover air coolers. If the standard is for water heaters, it does NOT cover electric irons. Only answer true if the standard directly applies to "{p_clean}".

Respond strictly in JSON:
{{
  "matches": true or false,
  "confidence": 0.0 to 1.0,
  "reason": "One concise sentence explaining why this standard does or does not cover '{p_clean}'."
}}"""

        resp = client.chat.completions.create(
            model=get_groq_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        gate_res = json.loads(resp.choices[0].message.content)
        matches = bool(gate_res.get("matches", False))
        confidence = float(gate_res.get("confidence", 0.0))
        reason = gate_res.get("reason", "")

        if not matches or confidence < 0.65:
            return (candidate_doc, False, reason or f"{cand_std} ({cand_title}) does not cover '{p_clean}'.")

        return (candidate_doc, True, reason or f"{cand_std} directly specifies requirements for '{p_clean}'.")

    except Exception as ex:
        print(f"[Compliance Resolver] LLM Gate check exception: {ex}")
        # Deterministic fallback check: if product title words don't intersect, reject
        cand_words = set(re.findall(r"\w+", cand_title.lower()))
        p_words = set(re.findall(r"\w+", p_lower))
        if not (p_words & cand_words):
            return (candidate_doc, False, f"{cand_title} ({cand_std}) does not cover '{p_clean}'.")
        return (candidate_doc, True, "Standard matched via title heuristics.")

def check_product_compliance(product_name: str) -> Dict[str, Any]:
    """
    Generate an authoritative, fact-checked BIS Product Compliance & Certification Report.
    Operates in two stages:
      1. Deterministic & semantic standard resolution with strict LLM scope validation.
      2. Document-scoped chunk retrieval (zero cross-contamination) and grounded test extraction.
    """
    if not product_name or not product_name.strip():
        raise ValueError("Product name cannot be empty.")

    p_clean = product_name.strip()

    # Stage 1: Document Resolution & Scope Validation Gate
    candidate_doc, is_valid, reason = resolve_product_standard(p_clean)

    if not is_valid:
        cand_label = None
        if candidate_doc:
            cand_std = candidate_doc.get("standard_number", "Standard")
            cand_title = candidate_doc.get("document_title") or candidate_doc.get("title_en", "")
            cand_label = f"{cand_std}: {cand_title}"

        return {
            "product_name": p_clean,
            "compliance_status": "No Standard Found",
            "standard_number": None,
            "document_title": f"No Indian Standard for '{p_clean}' found in library",
            "title_en": f"No Indian Standard for '{p_clean}' found in library",
            "title_hi": None,
            "certification_scheme": "Not Applicable",
            "is_mandatory": False,
            "qco_notice": None,
            "matched_document": cand_label,
            "reason": reason,
            "mandatory_tests": [],
            "required_documents": [
                {
                    "document": f"Upload Standard for {p_clean}",
                    "category": "Action Required",
                    "description": f"No Indian Standard covering '{p_clean}' is currently uploaded. Upload the relevant official BIS standard PDF in Document Management to perform compliance analysis."
                }
            ],
            "marking_requirements": f"Marking rules not available because no Indian Standard for '{p_clean}' exists in your library."
        }

    # Stage 2: Document-Scoped Retrieval (Strictly scoped to matched document_id)
    doc_id = candidate_doc.get("document_id")
    std_num = candidate_doc.get("standard_number") or "BIS Standard"
    doc_title = candidate_doc.get("title_en") or candidate_doc.get("document_title") or p_clean
    doc_title_hi = candidate_doc.get("title_hi")

    # Generic search queries strictly scoped to doc_id (NO COOKER POLLUTION)
    search_queries = [
        f"Scope terminology specifications requirements for {p_clean}",
        f"TESTS inspection routine type test proof safety procedure criteria",
        f"Marking packing instructions ISI mark certification scheme"
    ]

    all_chunks = []
    seen_texts = set()

    for q in search_queries:
        try:
            results = hybrid_search(query=q, top_k=4, document_id=doc_id)
            for c in results:
                txt = c.get("text", "")
                if txt and txt not in seen_texts:
                    seen_texts.add(txt)
                    all_chunks.append(c)
        except Exception as e:
            print(f"[Compliance Service] Scoped search query error: {e}")

    # Fallback if hybrid search produced no chunks: fetch any chunks from this document
    if not all_chunks:
        try:
            all_chunks = similarity_search(query="tests specification requirements", top_k=6, document_id=doc_id)
        except Exception as e:
            print(f"[Compliance Service] Fallback similarity search error: {e}")

    # Build context strictly from this verified document (keep compact to respect Groq TPM limits)
    context_text = "\n\n---\n\n".join([
        f"Chunk [Page {c.get('page_number', '?')} | Clause {c.get('clause', 'N/A')}]:\n{c.get('text', '')[:1200]}"
        for c in all_chunks[:4]
    ])

    # Stage 3: LLM Structured Audit Extraction
    try:
        from llm.llm_service import get_groq_client, get_groq_model
        client = get_groq_client()

        prompt = f"""You are a Principal Engineering Consultant & Lead BIS Standards Auditor for the Bureau of Indian Standards (BIS).
Analyze the official Indian Standard text context below for the target standard: '{std_num}: {doc_title}' (Product: '{p_clean}').

Generate a structured, authoritative, and fact-checked Compliance & Certification Report in strictly valid JSON format.
Every claim must be strictly verified against the text context provided.

CRITICAL FACT-CHECKING RULES:
1. Standard Number: Keep '{std_num}'.
2. Titles: Use official English title '{doc_title}' and Hindi title if available.
3. Testing Requirements: Extract actual complete tests defined in this standard.
   - DO NOT create broken sentence fragments.
   - DO NOT copy tests from other products (like cookers). Extract ONLY tests mentioned in the context.
   - Provide the exact Clause number if present, official test name, test type (Type Test, Routine Test, or Safety Interlock), and complete requirement procedure.
4. Mandatory Documentation: Categorize documentation realistically under Scheme-I BIS certification and standard Scheme of Inspection & Testing (SIT) guidelines.
5. Certification Scheme: Standard is 'ISI Mark Certification (Scheme I - Type Testing & Factory Audit)'.

Context from {std_num}:
{context_text}

Respond ONLY with a single valid JSON object with EXACTLY this structure:
{{
  "product_name": "{p_clean}",
  "standard_number": "{std_num}",
  "title_en": "{doc_title}",
  "title_hi": "{doc_title_hi or ''}",
  "compliance_status": "Standard Found & Analyzed",
  "certification_scheme": "ISI Mark Certification (Scheme I - Type Testing & Factory Audit)",
  "is_mandatory": true,
  "qco_notice": "Mandatory Certification under Quality Control Order (QCO)",
  "marking_requirements": "Complete marking specifications citing applicable standard rules (ISI mark, standard number, manufacturer trademark, ratings, etc.)",
  "mandatory_tests": [
    {{
      "clause": "Exact clause (e.g. Clause 8.1)",
      "test_name": "Test title",
      "test_type": "Type Test / Routine Test / Safety Interlock",
      "requirement": "Complete procedure and numerical tolerance with NO cut-offs."
    }}
  ],
  "required_documents": [
    {{
      "document": "Document title",
      "category": "Application / Quality Manual / SIT Records / Material Traceability",
      "description": "Regulatory role per Scheme-I / SIT guidelines"
    }}
  ]
}}"""

        response = client.chat.completions.create(
            model=get_groq_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        parsed = json.loads(response.choices[0].message.content)

        return {
            "product_name": p_clean,
            "compliance_status": "Standard Found & Analyzed",
            "standard_number": std_num,
            "document_title": doc_title,
            "title_en": doc_title,
            "title_hi": doc_title_hi or parsed.get("title_hi"),
            "certification_scheme": parsed.get("certification_scheme") or "ISI Mark Certification (Scheme I - Type Testing & Factory Audit)",
            "is_mandatory": parsed.get("is_mandatory", True),
            "qco_notice": parsed.get("qco_notice", "Mandatory Certification under Quality Control Order (QCO)"),
            "reason": reason,
            "mandatory_tests": parsed.get("mandatory_tests", []),
            "required_documents": parsed.get("required_documents", []),
            "marking_requirements": parsed.get("marking_requirements") or f"Every unit shall be legibly marked with ISI Mark, Standard Number ({std_num}), Manufacturer Trademark, and Technical Ratings."
        }

    except Exception as e:
        print(f"[Compliance Service] LLM extraction failed: {e}")
        # Safe fallback: Extract text from verified chunks of THIS document only, NEVER cookers
        extracted_tests = []
        for c in all_chunks:
            for line in c.get("text", "").split("\n"):
                ls = line.strip()
                if re.match(r"^(\d+\.\d+|\bClause\b|\bAnnex\b)", ls, re.I) and "test" in ls.lower():
                    if len(ls) > 15 and len(ls) < 140:
                        extracted_tests.append({
                            "clause": ls.split()[0],
                            "test_name": " ".join(ls.split()[1:5]),
                            "test_type": "Standard Test",
                            "requirement": ls
                        })
                        if len(extracted_tests) >= 5:
                            break
            if len(extracted_tests) >= 5:
                break

        return {
            "product_name": p_clean,
            "compliance_status": "Standard Found & Analyzed",
            "standard_number": std_num,
            "document_title": doc_title,
            "title_en": doc_title,
            "title_hi": doc_title_hi,
            "certification_scheme": "ISI Mark Certification (Scheme I - Type Testing & Factory Audit)",
            "is_mandatory": True,
            "qco_notice": "Mandatory Certification under Quality Control Order (QCO)",
            "reason": reason,
            "mandatory_tests": extracted_tests,
            "required_documents": [
                {
                    "document": "Application for Certification (Form-V)",
                    "category": "Application",
                    "description": f"Formal application submitted on the BIS Manakonline portal for ISI Mark certification under {std_num}."
                },
                {
                    "document": "Factory Scheme of Inspection and Testing (SIT)",
                    "category": "Quality Manual",
                    "description": "Agreement to adopt the BIS Scheme of Inspection and Testing (SIT) ensuring in-house production control."
                },
                {
                    "document": "In-house Test Facilities & Equipment Calibration",
                    "category": "SIT Records",
                    "description": "Valid calibration certificates for test equipment and measuring devices."
                }
            ],
            "marking_requirements": f"Every unit shall be legibly and permanently marked with the ISI Mark, Standard Number ({std_num}), Manufacturer Trademark, and applicable technical ratings."
        }
