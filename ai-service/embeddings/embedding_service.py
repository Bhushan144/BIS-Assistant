import os
from typing import List, Optional
from sentence_transformers import SentenceTransformer

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model_instance: Optional[SentenceTransformer] = None

def get_embedding_model_name() -> str:
    """Get configured embedding model name from environment or default."""
    return os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL_NAME)

def get_embedding_model() -> SentenceTransformer:
    """
    Get or initialize singleton instance of SentenceTransformer model.
    Loads once and reuses the model for performance.
    """
    global _model_instance
    if _model_instance is None:
        model_name = get_embedding_model_name()
        print(f"[EmbeddingService] Loading SentenceTransformer model '{model_name}'...")
        _model_instance = SentenceTransformer(model_name)
        print(f"[EmbeddingService] Model '{model_name}' loaded successfully.")
    return _model_instance

def embed_text(text: str) -> List[float]:
    """Generate float vector embedding for a single text string."""
    if not text:
        text = " "
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()

def embed_documents(texts: List[str]) -> List[List[float]]:
    """Generate vector embeddings for a list of text strings."""
    if not texts:
        return []
    # Replace empty strings with space to avoid model issues
    processed_texts = [t if t and t.strip() else " " for t in texts]
    model = get_embedding_model()
    embeddings = model.encode(processed_texts, batch_size=32, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.tolist()
