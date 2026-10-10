import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

vectorstore_dir = backend_dir / "vectorstore"
if str(vectorstore_dir) not in sys.path:
    sys.path.insert(0, str(vectorstore_dir))

from qdrant_service import similarity_search
from bm25_service import bm25_search

def hybrid_reciprocal_rank_fusion(
    vector_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    top_k: int = 5,
    rrf_k: int = 60
) -> List[Dict[str, Any]]:
    """
    Reciprocal Rank Fusion (RRF) algorithm:
    Combines dense vector search ranks and BM25 sparse keyword ranks.
    RRF_Score(doc) = 1/(k + rank_vector) + 1/(k + rank_bm25)
    """
    combined_scores: Dict[str, float] = {}
    chunk_map: Dict[str, Dict[str, Any]] = {}

    # 1. Process Dense Vector results
    for rank, chunk in enumerate(vector_results, 1):
        cid = chunk.get("chunk_id") or chunk.get("text", "")[:30]
        chunk_map[cid] = chunk
        rrf_score = 1.0 / (rrf_k + rank)
        combined_scores[cid] = combined_scores.get(cid, 0.0) + rrf_score

    # 2. Process Sparse BM25 results
    for rank, chunk in enumerate(bm25_results, 1):
        cid = chunk.get("chunk_id") or chunk.get("text", "")[:30]
        if cid not in chunk_map:
            chunk_map[cid] = chunk
        rrf_score = 1.0 / (rrf_k + rank)
        combined_scores[cid] = combined_scores.get(cid, 0.0) + rrf_score

    # 3. Sort chunks by fused RRF score
    fused_list = []
    for cid, rrf_score in combined_scores.items():
        chunk = dict(chunk_map[cid])
        chunk["rrf_score"] = round(rrf_score, 5)
        # Use fused score as overall match score
        chunk["score"] = round(rrf_score, 4)
        fused_list.append(chunk)

    fused_list.sort(key=lambda x: x["rrf_score"], reverse=True)
    return fused_list[:top_k]

def hybrid_search(
    query: str,
    top_k: int = 5,
    document_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Execute Hybrid Retrieval combining Qdrant Dense Vector Search and BM25 Sparse Keyword Search.
    """
    if not query or not query.strip():
        return []

    # Fetch top 10 candidates from each retriever
    dense_candidates = similarity_search(query=query, top_k=10, document_id=document_id)
    sparse_candidates = bm25_search(query=query, top_k=10, document_id=document_id)

    # Perform Reciprocal Rank Fusion
    fused_results = hybrid_reciprocal_rank_fusion(
        vector_results=dense_candidates,
        bm25_results=sparse_candidates,
        top_k=top_k
    )

    return fused_results
