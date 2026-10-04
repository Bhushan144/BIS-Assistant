import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from document_service import DATA_DIR

PROCESSED_DIR = DATA_DIR / "processed"

def tokenize_text(text: str) -> List[str]:
    """Simple alphanumeric tokenizer for BM25 text indexing."""
    if not text:
        return []
    return re.findall(r"\w+", text.lower())

def load_all_processed_chunks() -> List[Dict[str, Any]]:
    """Scan data/processed/*/chunks.json and load all processed chunks."""
    all_chunks = []
    if not PROCESSED_DIR.exists():
        return all_chunks

    for doc_dir in PROCESSED_DIR.iterdir():
        if doc_dir.is_dir():
            chunks_path = doc_dir / "chunks.json"
            if chunks_path.exists():
                try:
                    with open(chunks_path, "r", encoding="utf-8") as f:
                        doc_chunks = json.load(f)
                        all_chunks.extend(doc_chunks)
                except Exception:
                    continue
    return all_chunks

def bm25_search(
    query: str,
    top_k: int = 10,
    document_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Perform BM25 sparse keyword search across indexed document chunks.
    """
    if not BM25_AVAILABLE:
        print("[BM25 Warning] rank-bm25 package not installed. Skipping BM25 search.")
        return []

    if not query or not query.strip():
        return []

    chunks = load_all_processed_chunks()
    if document_id:
        chunks = [c for c in chunks if c.get("document_id") == document_id]

    if not chunks:
        return []

    # Corpus tokenization
    corpus_tokens = [tokenize_text(c.get("content", "")) for c in chunks]
    query_tokens = tokenize_text(query)

    if not query_tokens:
        return []

    bm25 = BM25Okapi(corpus_tokens)
    scores = bm25.get_scores(query_tokens)

    # Pair chunks with scores
    scored_chunks = []
    for idx, score in enumerate(scores):
        if score > 0.001:  # Filter zero match scores
            chunk = dict(chunks[idx])
            chunk["score"] = round(float(score), 4)
            chunk["text"] = chunk.get("content", "")
            scored_chunks.append(chunk)

    # Sort descending by BM25 score
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]
