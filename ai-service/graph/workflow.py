import sys
import re
from pathlib import Path
from typing import TypedDict, List, Dict, Any, Optional

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

retrieval_dir = backend_dir / "retrieval"
if str(retrieval_dir) not in sys.path:
    sys.path.insert(0, str(retrieval_dir))

llm_dir = backend_dir / "llm"
if str(llm_dir) not in sys.path:
    sys.path.insert(0, str(llm_dir))

from retrieval.hybrid_service import hybrid_search
from llm.llm_service import generate_grounded_answer
from rag.rag_service import format_context_block, build_structured_sources

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

class QueryState(TypedDict):
    query: str
    top_k: int
    document_id: Optional[str]
    language: str
    product: str
    intent: str
    retrieved_chunks: List[Dict[str, Any]]
    context_text: str
    answer: str
    sources: List[Dict[str, Any]]
    chat_history: List[Dict[str, str]]

def detect_query_understanding(query: str, requested_lang: Optional[str] = None) -> Dict[str, str]:
    """Detect product category, query intent, and language."""
    q_lower = query.lower()

    # Product detection
    product = "General Product"
    if "mixer" in q_lower or "grinder" in q_lower or "juicer" in q_lower:
        product = "Electric Food Mixer"
    elif "cooker" in q_lower or "pressure" in q_lower:
        product = "Pressure Cooker"
    elif "bottle" in q_lower or "steel" in q_lower:
        product = "Stainless Steel Bottle"

    # Intent detection
    intent = "General Requirement"
    
    # Detect conversational / chitchat queries
    clean_q = q_lower.strip().replace("?", "").replace("!", "").replace(".", "").strip()
    
    chitchat_exact = {"hi", "hello", "hey", "who are you", "what are you", "how are you", "thanks", "thank you", "ok", "okay", "bye", "good morning", "good evening", "hi there"}
    chitchat_starters = ("hi ", "hello ", "hey ", "my name is ", "i am ", "who ", "thanks ", "thank you")
    
    is_chitchat = False
    if clean_q in chitchat_exact:
        is_chitchat = True
    elif len(clean_q.split()) <= 15 and any(clean_q.startswith(s) for s in chitchat_starters):
        is_chitchat = True
        
    if is_chitchat:
        intent = "Conversational"
    elif "safety" in q_lower or "electric" in q_lower or "shock" in q_lower:
        intent = "Safety Requirement"
    elif "test" in q_lower or "testing" in q_lower or "voltage" in q_lower:
        intent = "Testing Requirement"
    elif "standard" in q_lower or "number" in q_lower or "is " in q_lower:
        intent = "Standard Lookup"
    elif "certif" in q_lower or "license" in q_lower:
        intent = "Certification"

    # Language detection
    language = requested_lang or "English"
    if "marathi" in q_lower or "मराठी" in q_lower:
        language = "Marathi"
    elif "hindi" in q_lower or "हिंदी" in q_lower:
        language = "Hindi"

    return {"product": product, "intent": intent, "language": language}

# Node 1: Query Understanding
def query_understanding_node(state: QueryState) -> QueryState:
    res = detect_query_understanding(state["query"], state.get("language"))
    state["product"] = res["product"]
    state["intent"] = res["intent"]
    state["language"] = res["language"]
    return state

# Node 2: Hybrid Retrieval
def hybrid_retrieval_node(state: QueryState) -> QueryState:
    if state.get("intent") == "Conversational":
        state["retrieved_chunks"] = []
        return state

    chunks = hybrid_search(
        query=state["query"],
        top_k=state.get("top_k", 5),
        document_id=state.get("document_id")
    )
    state["retrieved_chunks"] = chunks
    return state

# Node 3: Rerank & Filter Context
def rerank_filter_node(state: QueryState) -> QueryState:
    chunks = state.get("retrieved_chunks", [])
    if chunks:
        state["context_text"] = format_context_block(chunks)
    else:
        state["context_text"] = ""
    return state

# Node 4: Grounded Generation
def grounded_generation_node(state: QueryState) -> QueryState:
    context = state.get("context_text", "")
    query = state["query"]
    lang = state.get("language", "English")
    intent = state.get("intent", "")

    if intent == "Conversational":
        state["answer"] = generate_grounded_answer(
            query, 
            "", # No context needed for chitchat
            language=lang,
            chat_history=state.get("chat_history", []),
            is_conversational=True
        )
    elif not context:
        if lang == "Hindi":
            state["answer"] = "अपलोड किए गए बीआईएस दस्तावेजों में इसका उत्तर देने के लिए पर्याप्त जानकारी नहीं मिली।"
        elif lang == "Marathi":
            state["answer"] = "अपलोड केलेल्या बीआयएस दस्तऐवजांमध्ये याचे उत्तर देण्यासाठी पुरेशी माहिती आढळली नाही."
        else:
            state["answer"] = "I could not find sufficient information in the uploaded BIS documents to answer this reliably."
        state["retrieved_chunks"] = [] # Clear chunks so citations don't render
    else:
        state["answer"] = generate_grounded_answer(
            query, 
            context, 
            language=lang,
            chat_history=state.get("chat_history", [])
        )
        
        # If the LLM decided the context was insufficient and fell back, clear chunks
        ans = state.get("answer", "")
        if (
            "I could not find sufficient information" in ans or
            "अपलोड किए गए बीआईएस दस्तावेजों में" in ans or
            "अपलोड केलेल्या बीआयएस दस्तऐवजांमध्ये" in ans
        ):
            state["retrieved_chunks"] = []

    return state

# Node 5: Citation Verifier
def citation_verifier_node(state: QueryState) -> QueryState:
    chunks = state.get("retrieved_chunks", [])
    state["sources"] = build_structured_sources(chunks)
    return state

# Build compiled LangGraph Workflow
def build_bis_langgraph_app():
    if not LANGGRAPH_AVAILABLE:
        return None

    builder = StateGraph(QueryState)

    builder.add_node("query_understanding", query_understanding_node)
    builder.add_node("hybrid_retrieval", hybrid_retrieval_node)
    builder.add_node("rerank_filter", rerank_filter_node)
    builder.add_node("grounded_generation", grounded_generation_node)
    builder.add_node("citation_verifier", citation_verifier_node)

    builder.set_entry_point("query_understanding")
    builder.add_edge("query_understanding", "hybrid_retrieval")
    builder.add_edge("hybrid_retrieval", "rerank_filter")
    builder.add_edge("rerank_filter", "grounded_generation")
    builder.add_edge("grounded_generation", "citation_verifier")
    builder.add_edge("citation_verifier", END)

    return builder.compile()

# Global compiled graph runner
_compiled_graph = None

def run_bis_langgraph_workflow(
    query: str,
    top_k: int = 5,
    document_id: Optional[str] = None,
    language: str = "English",
    chat_history: List[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Execute full LangGraph agent state graph pipeline for user query.
    Falls back gracefully to procedural pipeline if langgraph is uncompiled.
    """
    global _compiled_graph
    if _compiled_graph is None and LANGGRAPH_AVAILABLE:
        try:
            _compiled_graph = build_bis_langgraph_app()
        except Exception as e:
            print(f"[LangGraph Warning] Failed to compile graph: {e}")

    initial_state: QueryState = {
        "query": query,
        "top_k": top_k,
        "document_id": document_id,
        "language": language,
        "product": "",
        "intent": "",
        "retrieved_chunks": [],
        "context_text": "",
        "answer": "",
        "sources": [],
        "chat_history": chat_history or []
    }

    if _compiled_graph:
        final_state = _compiled_graph.invoke(initial_state)
        return {
            "query": query,
            "answer": final_state.get("answer", ""),
            "product": final_state.get("product", ""),
            "intent": final_state.get("intent", ""),
            "language": final_state.get("language", language),
            "sources": final_state.get("sources", []),
            "retrieved_chunks": len(final_state.get("retrieved_chunks", []))
        }

    # Direct fallback runner if LangGraph compiled graph is not active
    s1 = query_understanding_node(initial_state)
    s2 = hybrid_retrieval_node(s1)
    s3 = rerank_filter_node(s2)
    s4 = grounded_generation_node(s3)
    s5 = citation_verifier_node(s4)

    return {
        "query": query,
        "answer": s5.get("answer", ""),
        "product": s5.get("product", ""),
        "intent": s5.get("intent", ""),
        "language": s5.get("language", language),
        "sources": s5.get("sources", []),
        "retrieved_chunks": len(s5.get("retrieved_chunks", []))
    }
