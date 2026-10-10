import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

vectorstore_dir = backend_dir / "vectorstore"
if str(vectorstore_dir) not in sys.path:
    sys.path.insert(0, str(vectorstore_dir))

llm_dir = backend_dir / "llm"
if str(llm_dir) not in sys.path:
    sys.path.insert(0, str(llm_dir))

from qdrant_service import similarity_search
from llm_service import generate_grounded_answer

def get_default_top_k() -> int:
    try:
        return int(os.getenv("RAG_TOP_K", "5"))
    except ValueError:
        return 5

def format_context_block(chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved vector chunks into structured context text for the LLM."""
    context_parts = []
    for idx, chunk in enumerate(chunks, 1):
        doc_name = chunk.get("document_name", "BIS Document")
        std_num = chunk.get("standard_number") or "Unknown Standard"
        page_num = chunk.get("page_number", 1)
        section = chunk.get("section", "Unknown Section")
        clause = chunk.get("clause") or ""
        text = chunk.get("text", "").strip()

        clause_str = f" | Clause: {clause}" if clause and clause != "None" else ""
        header = f"--- Document Chunk {idx} [{doc_name} | {std_num} | Page {page_num} | Section: {section}{clause_str}] ---"
        context_parts.append(f"{header}\n{text}")

    return "\n\n".join(context_parts)

def generate_snippet(text: str, max_chars: int = 250) -> str:
    """Generate a clean excerpt/snippet from chunk text."""
    clean = " ".join(text.split())
    if len(clean) <= max_chars:
        return clean
    return clean[:max_chars].rstrip() + "..."

def build_structured_sources(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Construct deterministic source citation objects from actual retrieved chunks.
    Guarantees citation accuracy with snippet excerpts and PDF viewer links.
    """
    sources = []
    seen_keys = set()

    for chunk in chunks:
        doc_id = chunk.get("document_id", "")
        doc_name = chunk.get("document_name", "Unknown Document")
        std_num = chunk.get("standard_number")
        if std_num == "None":
            std_num = None
        page_num = chunk.get("page_number", 1)
        section = chunk.get("section", "Unknown")
        clause = chunk.get("clause")
        if clause == "None":
            clause = None
        chunk_id = chunk.get("chunk_id", "")
        chunk_text = chunk.get("text", "")
        snippet = generate_snippet(chunk_text)
        pdf_url = f"/api/documents/{doc_id}/file#page={page_num}" if doc_id else ""

        # Deduplicate identical page/section sources if present
        dedup_key = f"{doc_id}_{page_num}_{section}_{clause}"
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)

        sources.append({
            "document_id": doc_id,
            "document_name": doc_name,
            "standard_number": std_num,
            "page_number": page_num,
            "section": section,
            "clause": clause,
            "chunk_id": chunk_id,
            "snippet": snippet,
            "pdf_url": pdf_url
        })

    return sources

def query_rag_pipeline(
    query: str,
    top_k: Optional[int] = None,
    document_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute full Phase 4 & Phase 5 RAG pipeline:
    1. Retrieve top-k relevant vector chunks from Qdrant
    2. Format structured context
    3. Call Groq LLM with strict grounding prompt
    4. Construct structured citation metadata with text snippets & PDF links
    """
    if not query or not query.strip():
        raise ValueError("Query string cannot be empty.")

    k = top_k if top_k is not None and top_k > 0 else get_default_top_k()

    # Step 1: Retrieve matching chunks from Qdrant vectorstore
    retrieved_chunks = similarity_search(
        query=query.strip(),
        top_k=k,
        document_id=document_id
    )

    if not retrieved_chunks:
        return {
            "query": query,
            "answer": "I could not find sufficient information in the uploaded BIS documents to answer this reliably.",
            "sources": [],
            "retrieved_chunks": 0
        }

    # Step 2: Format context text
    context_text = format_context_block(retrieved_chunks)

    # Step 3: Generate grounded answer via Groq LLM
    answer = generate_grounded_answer(query.strip(), context_text)

    # Step 4: Construct verified sources list from retrieved metadata
    sources = build_structured_sources(retrieved_chunks)

    return {
        "query": query,
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": len(retrieved_chunks)
    }
