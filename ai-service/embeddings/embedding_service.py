import os
from typing import List, Optional, Any

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Prefer fastembed (ONNX runtime, ~75MB RAM) for low-memory cloud production
# Fallback to sentence_transformers if fastembed is not installed
try:
    from fastembed import TextEmbedding
    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        SentenceTransformer = None

_model_instance: Optional[Any] = None

def get_embedding_model_name() -> str:
    """Get configured embedding model name from environment or default."""
    return os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL_NAME)

def get_embedding_model() -> Any:
    """
    Get or initialize singleton instance of embedding model.
    Uses fastembed (ONNX) when available, fallback to SentenceTransformer.
    """
    global _model_instance
    if _model_instance is None:
        model_name = get_embedding_model_name()
        if FASTEMBED_AVAILABLE:
            print(f"[EmbeddingService] Loading lightweight FastEmbed model '{model_name}' (ONNX Runtime)...")
            _model_instance = TextEmbedding(model_name=model_name)
            print(f"[EmbeddingService] FastEmbed model '{model_name}' loaded successfully (~75MB RAM).")
        elif SentenceTransformer is not None:
            print(f"[EmbeddingService] Loading SentenceTransformer model '{model_name}' (PyTorch)...")
            _model_instance = SentenceTransformer(model_name)
            print(f"[EmbeddingService] SentenceTransformer model '{model_name}' loaded successfully.")
        else:
            raise RuntimeError("Neither fastembed nor sentence-transformers is installed.")
    return _model_instance

def embed_text(text: str) -> List[float]:
    """Generate float vector embedding for a single text string."""
    if not text or not text.strip():
        text = " "
    model = get_embedding_model()
    if FASTEMBED_AVAILABLE:
        vectors = list(model.embed([text]))
        return [float(x) for x in vectors[0]]
    else:
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

def embed_documents(texts: List[str]) -> List[List[float]]:
    """Generate vector embeddings for a list of text strings."""
    if not texts:
        return []
    processed_texts = [t if t and t.strip() else " " for t in texts]
    model = get_embedding_model()
    if FASTEMBED_AVAILABLE:
        vectors = list(model.embed(processed_texts, batch_size=32))
        return [[float(x) for x in v] for v in vectors]
    else:
        embeddings = model.encode(processed_texts, batch_size=32, show_progress_bar=False, convert_to_numpy=True)
        return embeddings.tolist()
