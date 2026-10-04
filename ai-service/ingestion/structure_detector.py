import re
from typing import Dict, Optional, Tuple, List,Any

# Known standard BIS section names
STANDARD_BIS_SECTIONS = [
    "Foreword", "Scope", "Normative References", "References",
    "Terminology", "Terms and Definitions", "Definitions",
    "Requirements", "General Requirements", "Specific Requirements",
    "Sampling", "Tests", "Testing", "Methods of Test",
    "Marking", "Packing", "Packaging", "Packaging and Marking",
    "Compliance", "Certification"
]

def detect_section_and_clause(line: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Attempt to detect section title and clause number from a single line of text.

    Returns:
        (section, clause) tuple if matched, or (None, None).
    """
    line_clean = line.strip()
    if not line_clean:
        return None, None

    # Pattern 1: Numbered Section / Clause e.g., "4 Requirements", "4.1 General", "4.1.2 Insulation Test"
    match_clause = re.match(r"^(\d+(?:\.\d+)*)\s+([A-Z][A-Za-z0-9\s\,\-\(\)]+)$", line_clean)
    if match_clause:
        num_str = match_clause.group(1)
        title_str = match_clause.group(2).strip()
        # If it's a top-level section like "1 Scope" or "4 Requirements"
        if "." not in num_str:
            return f"{num_str} {title_str}", num_str
        else:
            return title_str, num_str

    # Pattern 2: Annex pattern e.g., "Annex A", "ANNEX B (Normative)", "Annex A Methods of Testing"
    match_annex = re.match(r"^(Annex\s+[A-Z])(?:\s+[\(\-\:\s]?([A-Za-z0-9\s]+)[\)]?)?", line_clean, re.IGNORECASE)
    if match_annex:
        annex_id = match_annex.group(1).title()
        extra_title = match_annex.group(2)
        if extra_title:
            return f"{annex_id} - {extra_title.strip()}", annex_id
        return annex_id, annex_id

    # Pattern 3: Standalone known BIS heading e.g., "FOREWORD", "SCOPE", "REQUIREMENTS"
    for sec_name in STANDARD_BIS_SECTIONS:
        if line_clean.lower() == sec_name.lower():
            return sec_name, None

    # Pattern 4: Standalone clause number e.g., "4.2.1"
    match_clause_only = re.match(r"^(\d+\.\d+(?:\.\d+)*)$", line_clean)
    if match_clause_only:
        return None, match_clause_only.group(1)

    return None, None


def extract_structure_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Parse full page text into structured blocks tagging detected sections and clauses.
    """
    blocks = []
    lines = text.split("\n")
    current_section = "Unknown"
    current_clause = None

    for line in lines:
        sec, clause = detect_section_and_clause(line)
        if sec:
            current_section = sec
        if clause:
            current_clause = clause

    return current_section, current_clause
