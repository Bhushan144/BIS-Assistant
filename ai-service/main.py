import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend directory to Python sys.path so app modules import cleanly
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

# Load .env file from project root or backend directory
root_env = backend_dir.parent / ".env"
if root_env.exists():
    load_dotenv(root_env)
else:
    load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from document_service import ensure_directories
from health import router as health_router
from documents import router as documents_router
from search import router as search_router
from rag_router import router as rag_router
from sources import router as sources_router
from compliance_router import router as compliance_router

app = FastAPI(
    title="AI-Powered BIS Standards & Services Assistant API",
    description="Full-stack GenAI + RAG system with PDF Ingestion, Hybrid Retrieval, LangGraph Agent Workflow, Grounded LLM Generation, Citations, Multilingual Engine, and BIS Compliance Inspector.",
    version="1.0.0"
)

# Enable CORS for React frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event handler to ensure required data directories exist
@app.on_event("startup")
def on_startup():
    ensure_directories()

# Register API routes under /api
app.include_router(health_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(rag_router, prefix="/api")
app.include_router(sources_router, prefix="/api")
app.include_router(compliance_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
