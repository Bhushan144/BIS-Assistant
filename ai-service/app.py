import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import spaces
import gradio as gr
from main import app

# ZeroGPU requires a decorated function linked to Gradio
@spaces.GPU
def gpu_runner(text: str = "") -> str:
    return "ZeroGPU Online"

# Status block so Hugging Face Space health check passes instantly
with gr.Blocks(title="BIS AI Assistant API") as demo:
    gr.Markdown("# ⚖️ BIS Assistant — AI Service API")
    gr.Markdown(
        "**Status**: 🟢 Online (16 GB RAM & ZeroGPU)\n\n"
        "FastAPI backend for BIS Standards & Services Assistant.\n\n"
        "All API routes are served under `/api` (`/api/documents`, `/api/chat`, `/api/search`, etc.)."
    )
    # Hidden component to register @spaces.GPU for Hugging Face ZeroGPU startup scanner
    dummy_input = gr.Textbox(visible=False)
    dummy_output = gr.Textbox(visible=False)
    dummy_btn = gr.Button(visible=False)
    dummy_btn.click(fn=gpu_runner, inputs=dummy_input, outputs=dummy_output)

# Mount Gradio onto the existing FastAPI application at root
# Hugging Face Spaces automatically runs Uvicorn on 'app:app' on port 7860
app = gr.mount_gradio_app(app, demo, path="/")
