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

    # Regex matching common Indian Standard pattern variations including year/edition
    patterns = [
        r"\b(IS(?:/IEC)?\s+\d+(?:[\-\:]\d+)*(?:\s*:\s*\d{4})?)\b",
        r"\b(IS\s+\d{3,6})\b"
    ]

    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            # Normalize whitespace e.g., "IS 2347 : 2023" -> "IS 2347:2023"
            std_num = match.group(1).upper()
            std_num = re.sub(r"\s*:\s*", ":", std_num)
            std_num = re.sub(r"\s+", " ", std_num)
            return std_num

    return None

def extract_document_bilingual_titles(first_few_pages_text: str, filename: str) -> Dict[str, Optional[str]]:
    """
    Attempt to extract both English official title and Hindi title from cover page.
    """
    if not first_few_pages_text:
        clean_fallback = filename.replace(".pdf", "").replace("_", " ")
        return {"title_en": clean_fallback, "title_hi": None}

    lines = [line.strip() for line in first_few_pages_text.split("\n") if line.strip()]

    hindi_lines = []
    english_lines = []

    for line in lines[:30]:
        # Skip standard headers like "Indian Standard", "BIS", IS numbers, administrative metadata
        if re.match(r"^(IS\s+\d+|ICS|UDC|Draft|Price|September|October|November|December|January|February|March|April|May|June|July|August|\d{4})", line, re.IGNORECASE):
            continue
        if re.search(r"(BUREAU OF INDIAN STANDARDS|MANAK BHAVAN|NEW DELHI|Free Standard|standardsbis|www\.bis)", line, re.IGNORECASE):
            continue
        if re.search(r"(भारतीय मानक ब्यूरो|मानक भवन|नई दिल्ली)", line):
            continue

        if re.search(r"[\u0900-\u097F]", line):
            # Devanagari Hindi text
            if len(line) > 3 and not re.search(r"^भारतीय मानक", line):
                hindi_lines.append(line)
        else:
            if not re.match(r"^(Indian Standard)$", line, re.IGNORECASE):
                if len(line) > 3:
                    english_lines.append(line)

    title_hi = " — ".join(hindi_lines[:2]) if hindi_lines else None
    
    title_en = None
    if english_lines:
        title_en = " ".join(english_lines[:2])
        title_en = re.sub(r"\s+", " ", title_en).strip()
    
    if not title_en:
        title_en = filename.replace(".pdf", "").replace("_", " ")

    return {"title_en": title_en, "title_hi": title_hi}

def extract_document_title(first_few_pages_text: str, filename: str) -> str:
    """
    Backward-compatible title extraction, returning the official English title.
    """
    titles = extract_document_bilingual_titles(first_few_pages_text, filename)
    return titles["title_en"]

def infer_product_category(title: str, text: str) -> str:
    """
    Deterministic rule-based product category lookup. 
    Returns 'Unknown' if no explicit match is found.
    """
    combined = (title + " " + text[:2000]).lower()

    category_keywords = {
        "Pressure Cookers": ["pressure cooker", "cooker"],
        "Water Heaters & Geysers": ["water heater", "geyser", "heating appliance"],
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

    titles = extract_document_bilingual_titles(full_text_sample, filename)
    doc_title = titles["title_en"]
    product_cat = infer_product_category(doc_title, full_text_sample)

    return {
        "standard_number": std_number,  # String or None
        "document_title": doc_title,
        "title_en": titles["title_en"],
        "title_hi": titles["title_hi"],
        "product_category": product_cat
    }
