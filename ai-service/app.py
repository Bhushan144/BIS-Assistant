import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import gradio as gr
from main import app

# Status block so Hugging Face Space health check passes instantly
with gr.Blocks(title="BIS AI Assistant API") as demo:
    gr.Markdown("# ⚖️ BIS Assistant — AI Service API")
    gr.Markdown(
        "**Status**: 🟢 Online (16 GB RAM)\n\n"
        "FastAPI backend for BIS Standards & Services Assistant.\n\n"
        "All API routes are served under `/api` (`/api/documents`, `/api/chat`, `/api/search`, etc.)."
    )

# Mount Gradio onto the existing FastAPI application
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
