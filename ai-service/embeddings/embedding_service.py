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

_model_instance: Optional[Any] = None

def get_embedding_model_name() -> str:
    """Get configured embedding model name from environment or default."""
    return os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL_NAME)

def get_embedding_model() -> Any:
    """
    Get or initialize singleton instance of embedding model using FastEmbed (ONNX).
    Forces threads=1 to prevent ONNX Runtime from spawning threads for all host CPU cores
    which causes immediate OOM crashes on shared cloud containers (Render Free 512MB).
    """
    global _model_instance
    if _model_instance is None:
        model_name = get_embedding_model_name()
        if not FASTEMBED_AVAILABLE:
            raise RuntimeError("FastEmbed is not installed. Please install fastembed>=0.3.0.")
        
        print(f"[EmbeddingService] Loading FastEmbed ONNX model '{model_name}' (single-thread mode)...")
        # threads=1 is crucial on Render: stops ONNX from creating 32-64 threads for host cores
        _model_instance = TextEmbedding(model_name=model_name, threads=1)
        print(f"[EmbeddingService] FastEmbed model '{model_name}' loaded successfully (~50MB RAM).")
    return _model_instance

def embed_text(text: str) -> List[float]:
    """Generate float vector embedding for a single text string."""
    if not text or not text.strip():
        text = " "
    model = get_embedding_model()
    vectors = list(model.embed([text]))
    return [float(x) for x in vectors[0]]

def embed_documents(texts: List[str]) -> List[List[float]]:
    """
    Generate vector embeddings for a list of text strings.
    Uses small batch_size=8 to prevent RAM spikes on low-memory servers.
    """
    if not texts:
        return []
    processed_texts = [t if t and t.strip() else " " for t in texts]
    model = get_embedding_model()
    # Batch size 8 prevents memory accumulation during bulk indexing
    vectors = list(model.embed(processed_texts, batch_size=8))
    return [[float(x) for x in v] for v in vectors]
