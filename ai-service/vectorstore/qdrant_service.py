import os
import sys
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from qdrant_client.models import PointStruct, VectorParams, Distance

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

embeddings_dir = backend_dir / "embeddings"
if str(embeddings_dir) not in sys.path:
    sys.path.insert(0, str(embeddings_dir))

from embeddings.embedding_service import embed_text, embed_documents

DEFAULT_COLLECTION_NAME = "bis_documents"
# Dimension for sentence-transformers/all-MiniLM-L6-v2 is usually 384
VECTOR_DIMENSION = 384 

_qdrant_client: Optional[QdrantClient] = None

def get_qdrant_client() -> QdrantClient:
    """Initialize or get singleton Qdrant DB client."""
    global _qdrant_client
    if _qdrant_client is None:
        qdrant_url = os.getenv("QDRANT_URL", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        print(f"[QdrantService] Initializing Qdrant client at {qdrant_url}:{qdrant_port}...")
        _qdrant_client = QdrantClient(host=qdrant_url, port=qdrant_port)
    return _qdrant_client

def get_collection_name() -> str:
    return os.getenv("QDRANT_COLLECTION_NAME", DEFAULT_COLLECTION_NAME)

def ensure_collection_exists():
    """Ensure the Qdrant collection exists before using it."""
    client = get_qdrant_client()
    col_name = get_collection_name()
    
    if not client.collection_exists(collection_name=col_name):
        print(f"[QdrantService] Collection '{col_name}' not found. Creating...")
        client.create_collection(
            collection_name=col_name,
            vectors_config=VectorParams(size=VECTOR_DIMENSION, distance=Distance.COSINE),
        )
    return col_name

def add_chunks_to_vectorstore(chunks: List[Dict[str, Any]]) -> int:
    """
    Embed and upsert list of chunks into Qdrant collection.
    Returns number of chunks indexed.
    """
    if not chunks:
        return 0

    client = get_qdrant_client()
    col_name = ensure_collection_exists()

    points = []
    documents = []
    
    # First, collect content for batch embedding
    for chunk in chunks:
        content = chunk.get("content", "").strip()
        if content:
            documents.append(content)

    if not documents:
        return 0

    print(f"[QdrantService] Generating embeddings for {len(documents)} chunks...")
    embeddings = embed_documents(documents)

    idx = 0
    for chunk in chunks:
        content = chunk.get("content", "").strip()
        if not content:
            continue
            
        # Ensure UUID format for Qdrant ID
        chunk_id = chunk.get("chunk_id", str(uuid.uuid4()))
        try:
            point_id = str(uuid.UUID(chunk_id))
        except ValueError:
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))
            
        payload = {k: v for k, v in chunk.items() if v is not None}
        
        points.append(
            PointStruct(
                id=point_id,
                vector=embeddings[idx],
                payload=payload
            )
        )
        idx += 1

    print(f"[QdrantService] Upserting {len(points)} vectors into collection '{col_name}'...")
    client.upsert(
        collection_name=col_name,
        points=points
    )

    return len(points)

def delete_document_chunks(document_id: str) -> None:
    """Remove all vectors associated with a document_id from Qdrant."""
    try:
        client = get_qdrant_client()
        col_name = ensure_collection_exists()
        
        client.delete(
            collection_name=col_name,
            points_selector=rest.Filter(
                must=[
                    rest.FieldCondition(
                        key="document_id",
                        match=rest.MatchValue(value=document_id)
                    )
                ]
            )
        )
        print(f"[QdrantService] Deleted existing vectors for document '{document_id}'.")
    except Exception as e:
        print(f"[QdrantService Warning] Vector deletion for '{document_id}' encountered: {e}")

def similarity_search(
    query: str,
    top_k: int = 5,
    document_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search Qdrant for vector similarity against a user query string.
    """
    if not query or not query.strip():
        return []

    client = get_qdrant_client()
    col_name = ensure_collection_exists()
    
    query_embedding = embed_text(query)

    query_filter = None
    if document_id:
        query_filter = rest.Filter(
            must=[
                rest.FieldCondition(
                    key="document_id",
                    match=rest.MatchValue(value=document_id)
                )
            ]
        )

    res = client.query_points(
        collection_name=col_name,
        query=query_embedding,
        query_filter=query_filter,
        limit=top_k,
        with_payload=True
    )

    results = []
    for hit in res.points:
        meta = hit.payload or {}
        score = hit.score
        
        clean_chunk = {
            "chunk_id": meta.get("chunk_id", str(hit.id)),
            "document_id": meta.get("document_id", ""),
            "document_name": meta.get("document_name", ""),
            "document_title": meta.get("document_title", ""),
            "page_number": meta.get("page_number", 1),
            "section": meta.get("section", "Unknown"),
            "clause": meta.get("clause", "None"),
            "standard_number": meta.get("standard_number", "None"),
            "product_category": meta.get("product_category", "Unknown"),
            "source": meta.get("source", ""),
            "text": meta.get("content", ""),
            "score": round(score, 4)
        }
        results.append(clean_chunk)

    return results
