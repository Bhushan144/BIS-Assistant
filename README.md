# AI-Powered BIS Standards & Services Assistant

Full-stack **GenAI + RAG Final-Year Engineering Project** designed to analyze official Bureau of Indian Standards (BIS) PDF documents and provide grounded answers with exact source & page citations.

---

## 📌 Phase 1 Scope

Phase 1 establishes the production-grade foundation for PDF document ingestion and registry:
* **Multi-PDF Upload**: Drag-and-drop file upload with validation for PDF magic headers.
* **Metadata Extraction**: Calculates SHA256 checksums, exact page count (via `pypdf`), file size, upload timestamp, and document UUIDs.
* **Duplicate Prevention**: Rejects duplicate document uploads based on SHA256 hash comparison.
* **Registry Database**: Stores structured document registry in `data/documents.json`.
* **Data Integrity**: Uploaded original PDF files are saved unchanged under `data/uploads/`.
* **Frontend Dashboard**: React + Vite UI with Document Library, status indicators, and RAG Chat shell.

---

## 🛠️ Project Structure

```text
bis-assistant/
│
├── backend/
│   ├── main.py                # FastAPI server entry point & CORS
│   ├── schemas.py             # Pydantic request/response models
│   ├── documents.py           # Document upload & query endpoints
│   ├── document_service.py    # PDF validation, page counting, SHA256 & JSON DB
│   └── health.py              # Health check endpoint
│
├── frontend/
│   ├── package.json           # React Vite dependencies
│   ├── index.html             # HTML template & fonts
│   ├── vite.config.js         # Vite proxy configuration
│   └── src/
│       ├── main.jsx           # React app mount
│       ├── App.jsx            # Header, Navigation, and Layout
│       ├── index.css          # BIS-themed Vanilla CSS design system
│       ├── components/
│       │   ├── PdfUpload.jsx  # Drag & drop upload component
│       │   └── DocumentList.jsx # Document library table
│       └── services/
│           └── api.js         # API integration client
│
├── data/
│   ├── uploads/               # Original uploaded PDF files
│   └── documents.json         # Document registry metadata store
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

## 🚀 Getting Started

### Prerequisites
* **Python**: 3.10+
* **Node.js**: 18+ & `npm`

---

### Backend Setup & Execution

1. Navigate to the project root:
   ```bash
   cd bis-assistant
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the FastAPI server:
   ```bash
   python backend/main.py
   ```
   * The API server will start on `http://127.0.0.1:8000`
   * Interactive API docs: `http://127.0.0.1:8000/docs`

---

### Frontend Setup & Execution

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd bis-assistant/frontend
   ```

2. Install npm packages:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   * Open `http://localhost:5173` in your browser.

---

## 🔗 Backend API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check returning status and server timestamp |
| `POST` | `/api/documents/upload` | Upload single or multiple PDF documents with validation & duplicate detection |
| `GET` | `/api/documents` | Retrieve all registered document metadata |
| `GET` | `/api/documents/{document_id}` | Retrieve metadata for a specific document by UUID |

---

## 🗺️ Roadmap (Future Phases)

* **Phase 2**: Structure-Aware PDF Extraction & Chunking
* **Phase 3**: Vector DB Indexing & Embeddings (Qdrant)
* **Phase 4**: Grounded LLM Generation & Retrieval Engine
* **Phase 5**: Citation Formatter & Source Document Side-Panel
* **Phase 6**: Hybrid Retrieval (Dense Vector + BM25 Sparse Search + Reranking)
* **Phase 7**: LangGraph Agent Workflow
* **Phase 8**: Multilingual Assistant Engine (English, Hindi, Marathi)
* **Phase 9**: Compliance Assistant & Standard Recommendation
* **Phase 10**: Benchmarking, Evaluation & Project Documentation
