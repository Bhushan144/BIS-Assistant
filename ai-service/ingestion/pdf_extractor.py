import os
from pathlib import Path
from typing import List, Dict, Any

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


def extract_pages_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract text page by page from a PDF file preserving original 1-indexed page numbers.
    Uses PyMuPDF (fitz) primarily, falling back to pypdf if PyMuPDF is unavailable or fails.

    Returns:
        List of dicts: [
            {
                "page_number": 1,
                "text": "...",
                "char_count": int,
                "word_count": int,
                "error": str or None
            }
        ]
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found at path: {pdf_path}")

    pages_data: List[Dict[str, Any]] = []

    # Strategy 1: Try PyMuPDF (fitz)
    if PYMUPDF_AVAILABLE:
        try:
            doc = fitz.open(str(path))
            for i, page in enumerate(doc):
                page_num = i + 1
                try:
                    text = page.get_text("text") or ""
                    cleaned = text.strip()
                    pages_data.append({
                        "page_number": page_num,
                        "text": cleaned,
                        "char_count": len(cleaned),
                        "word_count": len(cleaned.split()),
                        "error": None
                    })
                except Exception as page_err:
                    pages_data.append({
                        "page_number": page_num,
                        "text": "",
                        "char_count": 0,
                        "word_count": 0,
                        "error": f"Error extracting page {page_num}: {str(page_err)}"
                    })
            doc.close()
            return pages_data
        except Exception as doc_err:
            print(f"[Warning] PyMuPDF extraction failed for '{pdf_path}': {doc_err}. Trying pypdf fallback.")
            pages_data.clear()

    # Strategy 2: Fallback to pypdf
    if PYPDF_AVAILABLE:
        try:
            reader = PdfReader(str(path))
            for i, page in enumerate(reader.pages):
                page_num = i + 1
                try:
                    text = page.extract_text() or ""
                    cleaned = text.strip()
                    pages_data.append({
                        "page_number": page_num,
                        "text": cleaned,
                        "char_count": len(cleaned),
                        "word_count": len(cleaned.split()),
                        "error": None
                    })
                except Exception as page_err:
                    pages_data.append({
                        "page_number": page_num,
                        "text": "",
                        "char_count": 0,
                        "word_count": 0,
                        "error": f"Error extracting page {page_num}: {str(page_err)}"
                    })
            return pages_data
        except Exception as pypdf_err:
            raise RuntimeError(f"Both PyMuPDF and pypdf extraction failed for '{pdf_path}': {pypdf_err}")

    raise ImportError("Neither PyMuPDF ('fitz') nor 'pypdf' is installed for PDF text extraction.")
