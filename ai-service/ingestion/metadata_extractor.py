import re
from typing import Dict, Optional, Any, List

def detect_standard_number(text: str) -> Optional[str]:
    """
    Search text for Indian Standard (IS) numbers using regex patterns.
    Examples:
    - IS 4250
    - IS 302
    - IS 1234:2025
    - IS 302-2-3:2007
    - IS/IEC 60335-1

    Returns standard_number string or None if not reliably detected.
    """
    if not text:
        return None

    # Regex matching common Indian Standard pattern variations
    patterns = [
        r"\b(IS(?:/IEC)?\s+\d+(?:[\-\:]\d+)*(?:\:\d{4})?)\b",
        r"\b(IS\s+\d{3,6})\b"
    ]

    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            # Normalize whitespace e.g., "IS 4250: 2025" -> "IS 4250:2025"
            std_num = match.group(1).upper()
            std_num = re.sub(r"\s*:\s*", ":", std_num)
            std_num = re.sub(r"\s+", " ", std_num)
            return std_num

    return None

def extract_document_title(first_few_pages_text: str, filename: str) -> str:
    """
    Attempt to extract document title from the cover page / first few pages, 
    or fall back to clean filename.
    """
    if not first_few_pages_text:
        return filename.replace(".pdf", "").replace("_", " ")

    lines = [line.strip() for line in first_few_pages_text.split("\n") if line.strip()]
    
    # Skip standard headers like "Indian Standard", "BIS", IS numbers
    candidate_lines = []
    for line in lines[:20]:
        if re.match(r"^(Indian Standard|Bureau of Indian Standards|IS\s+\d+|ICS|UDC|Draft|\d+)", line, re.IGNORECASE):
            continue
        if len(line) > 5 and len(line) < 150:
            candidate_lines.append(line)

    if candidate_lines:
        return " — ".join(candidate_lines[:2])

    return filename.replace(".pdf", "").replace("_", " ")

def infer_product_category(title: str, text: str) -> str:
    """
    Deterministic rule-based product category lookup. 
    Returns 'Unknown' if no explicit match is found.
    """
    combined = (title + " " + text[:2000]).lower()

    category_keywords = {
        "Pressure Cookers": ["pressure cooker", "cooker"],
        "Electrical Household Appliances": ["household electrical", "appliances", "mixer", "juicer", "grinder", "electric iron", "toaster"],
        "Stainless Steel Products": ["stainless steel", "water bottle", "steel vessel", "utensils"],
        "Footwear & Rubber": ["footwear", "safety shoes", "rubber"],
        "Cement & Building Materials": ["portland cement", "concrete", "building material"],
        "Electronics & Batteries": ["battery", "lithium-ion", "electronic equipment", "led lamp"]
    }

    for category, keywords in category_keywords.items():
        for kw in keywords:
            if kw in combined:
                return category

    return "Unknown"

def extract_document_metadata(pages_data: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
    """
    Aggregate metadata extraction across extracted document pages.
    """
    full_text_sample = "\n".join([p.get("text", "") for p in pages_data[:5]])
    
    std_number = detect_standard_number(full_text_sample)
    if not std_number:
        # Search all pages if not found in first 5
        full_doc_text = "\n".join([p.get("text", "") for p in pages_data])
        std_number = detect_standard_number(full_doc_text)

    doc_title = extract_document_title(full_text_sample, filename)
    product_cat = infer_product_category(doc_title, full_text_sample)

    return {
        "standard_number": std_number,  # String or None
        "document_title": doc_title,
        "product_category": product_cat
    }
