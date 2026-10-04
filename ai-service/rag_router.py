import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from schemas import RagQueryRequest, RagQueryResponse

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

graph_dir = backend_dir / "graph"
if str(graph_dir) not in sys.path:
    sys.path.insert(0, str(graph_dir))

from graph.workflow import run_bis_langgraph_workflow

router = APIRouter(prefix="/rag", tags=["RAG Services"])

class ExtendedRagQueryRequest(RagQueryRequest):
    language: Optional[str] = Field(default="English", description="Target output language (English | Hindi | Marathi)")

@router.post("/query", response_model=RagQueryResponse)
def rag_query(req: ExtendedRagQueryRequest):
    """
    Execute full LangGraph agent RAG workflow state machine:
    - Query understanding (Product, Intent, Language)
    - Hybrid Dense + Sparse BM25 retrieval
    - Grounded LLM generation (EN / HI / MR)
    - Verified source citation metadata
    """
    if not req.query or not req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )

    try:
        res = run_bis_langgraph_workflow(
            query=req.query.strip(),
            top_k=req.top_k or 5,
            document_id=req.document_id,
            language=req.language or "English",
            chat_history=req.chat_history or []
        )
        return RagQueryResponse(
            query=res["query"],
            answer=res["answer"],
            sources=res["sources"],
            retrieved_chunks=res["retrieved_chunks"]
        )

    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LangGraph RAG workflow error: {str(e)}"
        )
