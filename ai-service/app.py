import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import gradio as gr
from main import app

# Status dashboard for Hugging Face Space
with gr.Blocks(title="BIS AI Assistant API") as demo:
    gr.Markdown("# ⚖️ BIS Assistant — AI Service API")
    gr.Markdown(
        "**Status**: 🟢 Online (16 GB RAM)\n\n"
        "FastAPI backend for BIS Standards & Services Assistant.\n\n"
        "All API routes are served under `/api` (`/api/documents`, `/api/chat`, `/api/search`, etc.)."
    )

# Mount Gradio onto the existing FastAPI application at root
app = gr.mount_gradio_app(app, demo, path="/")
