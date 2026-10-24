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
    """Initialize or get singleton Qdrant DB client (supports local Docker and Qdrant Cloud)."""
    global _qdrant_client
    if _qdrant_client is None:
        qdrant_url = os.getenv("QDRANT_URL", "localhost")
        qdrant_api_key = os.getenv("QDRANT_API_KEY", None)
        if qdrant_api_key or qdrant_url.startswith("http://") or qdrant_url.startswith("https://"):
            print(f"[QdrantService] Connecting to Qdrant Cloud/Remote at {qdrant_url}...")
            _qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
            print(f"[QdrantService] Connecting to local Qdrant at {qdrant_url}:{qdrant_port}...")
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
    
    # Ensure keyword indices on payload fields for query filtering
    try:
        client.create_payload_index(collection_name=col_name, field_name="document_id", field_schema=rest.PayloadSchemaType.KEYWORD)
        client.create_payload_index(collection_name=col_name, field_name="standard_number", field_schema=rest.PayloadSchemaType.KEYWORD)
    except Exception:
        pass

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

    import gc
    total_indexed = 0
    batch_size = 5

    print(f"[QdrantService] Indexing {len(chunks)} chunks in micro-batches of {batch_size}...")

    for i in range(0, len(chunks), batch_size):
        chunk_batch = chunks[i:i + batch_size]
        batch_docs = [c.get("content", "").strip() or " " for c in chunk_batch]
        batch_embeddings = embed_documents(batch_docs)

        batch_points = []
        for j, chunk in enumerate(chunk_batch):
            chunk_id = chunk.get("chunk_id", str(uuid.uuid4()))
            try:
                point_id = str(uuid.UUID(chunk_id))
            except ValueError:
                point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))

            payload = {k: v for k, v in chunk.items() if v is not None}
            batch_points.append(
                PointStruct(
                    id=point_id,
                    vector=batch_embeddings[j],
                    payload=payload
                )
            )

        client.upsert(
            collection_name=col_name,
            points=batch_points
        )
        total_indexed += len(batch_points)
        # Reclaim memory immediately after each micro-batch
        del batch_docs
        del batch_embeddings
        del batch_points
        gc.collect()

    print(f"[QdrantService] Successfully indexed {total_indexed} vectors into '{col_name}'.")
    return total_indexed

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
