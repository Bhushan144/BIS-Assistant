import uuid
import re
from typing import List, Dict, Any, Optional
from text_cleaner import clean_text
from structure_detector import detect_section_and_clause

def create_chunks_from_pages(
    pages_data: List[Dict[str, Any]],
    document_id: str,
    document_name: str,
    document_title: str,
    standard_number: Optional[str],
    product_category: str,
    target_words: int = 600,
    overlap_words: int = 75
) -> List[Dict[str, Any]]:
    """
    Structure-Aware Chunker:
    Processes page-by-page extracted PDF text into meaningful chunks while:
    - Respecting section, clause, and page boundaries
    - Priority for section/paragraph splits over arbitrary word cuts
    - Attaching comprehensive chunk metadata (chunk_id, document_id, page_number, section, clause, standard_number)
    """
    chunks: List[Dict[str, Any]] = []

    current_section = "Unknown"
    current_clause = None

    for page in pages_data:
        page_num = page.get("page_number", 1)
        raw_text = page.get("text", "")
        cleaned_page_text = clean_text(raw_text)

        if not cleaned_page_text:
            continue

        # Split page text into paragraphs / structural blocks
        paragraphs = cleaned_page_text.split("\n\n")
        
        current_chunk_paragraphs = []
        current_chunk_words = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Check if paragraph introduces a new section or clause
            first_line = para.split("\n")[0]
            sec, clause = detect_section_and_clause(first_line)
            if sec:
                current_section = sec
            if clause:
                current_clause = clause

            para_words = len(para.split())

            # If adding this paragraph exceeds target word limit and we already have content,
            # emit current chunk first (prioritizing paragraph/section boundary)
            if current_chunk_words > 0 and (current_chunk_words + para_words > target_words):
                chunk_content = "\n\n".join(current_chunk_paragraphs)
                chunks.append({
                    "chunk_id": str(uuid.uuid4()),
                    "document_id": document_id,
                    "document_name": document_name,
                    "document_title": document_title,
                    "page_number": page_num,
                    "section": current_section,
                    "clause": current_clause,
                    "standard_number": standard_number,
                    "product_category": product_category,
                    "source": document_name,
                    "word_count": len(chunk_content.split()),
                    "content": chunk_content
                })

                # Prepare next chunk with overlap
                if overlap_words > 0 and len(current_chunk_paragraphs) > 1:
                    overlap_para = current_chunk_paragraphs[-1]
                    current_chunk_paragraphs = [overlap_para, para]
                    current_chunk_words = len(overlap_para.split()) + para_words
                else:
                    current_chunk_paragraphs = [para]
                    current_chunk_words = para_words
            else:
                current_chunk_paragraphs.append(para)
                current_chunk_words += para_words

        # Flush remaining paragraphs for the page
        if current_chunk_paragraphs:
            chunk_content = "\n\n".join(current_chunk_paragraphs)
            chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "document_id": document_id,
                "document_name": document_name,
                "document_title": document_title,
                "page_number": page_num,
                "section": current_section,
                "clause": current_clause,
                "standard_number": standard_number,
                "product_category": product_category,
                "source": document_name,
                "word_count": len(chunk_content.split()),
                "content": chunk_content
            })

    return chunks
