# InvoiceIQ

Intelligent document processor powered by LLMs. Upload invoices, receipts, purchase orders, and bank statements — the system automatically classifies them, extracts structured data, detects anomalies, and lets you chat with your documents.

## Features

- **Batch Upload** — drag & drop multiple PDFs with file preview before uploading
- **Auto-Classification** — regex heuristics classify document type with LLM fallback
- **Data Extraction** — LLM-powered extraction of vendor, amounts, dates, line items, etc.
- **Anomaly Detection** — identifies missing fields, duplicate documents, and outliers
- **Anomaly Resolution** — mark anomalies as resolved/false positives from the document view
- **Export** — download extracted data as CSV or Excel
- **RAG Chat** — ask natural language questions about your documents, get answers with sources
- **Chat Sessions** — persistent conversations with history, rename, and multi-turn context
- **Dashboard** — stats cards, recent documents, and processing timeline

## Quick Start

### Option A: Docker (Recommended)
```bash
docker-compose up --build
```
Opens at [http://localhost:3000](http://localhost:3000). Redis, OCR, and poppler all handled inside containers.

### Option B: Native Setup

**Prerequisites:**
- Python 3.11+
- Node.js 18+
- Redis
- Hugging Face API key (free) — [get one here](https://huggingface.co/settings/tokens)

#### 1. Get Free Hugging Face API Key
Sign up at https://huggingface.co and generate a read token at https://huggingface.co/settings/tokens.

#### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Edit .env and add your HF_API_KEY
uvicorn app.main:app --reload --port 8000
```

#### 3. Start Celery Worker
```bash
cd backend
celery -A celery_worker worker -l info --pool=solo
```

#### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

#### 5. Open
Visit [http://localhost:3000](http://localhost:3000)

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| `HF_API_KEY` | Yes | Hugging Face API token for LLM extraction and chat |
| `HF_MODEL` | No | Model to use (default: `meta-llama/Llama-3.3-70B-Instruct`) |
| `GEMINI_API_KEY` | No | Google Gemini API key (fallback LLM) |
| `OLLAMA_BASE_URL` | No | Ollama server URL for local LLM fallback |
| `DATABASE_URL` | No | SQLite default, use PostgreSQL for production |
| `REDIS_URL` | No | Redis connection for Celery task queue |
| `CLASSIFICATION_CONFIDENCE_THRESHOLD` | No | Threshold for regex vs LLM classification (default: 0.7) |

## How It Works

```
Upload PDF → Extract Text → Classify Type → LLM Extraction → Validate → Anomaly Detect → Done
                                                                                ↓
                                                                        Chat with docs
```

1. **Text Extraction** — pdfplumber for machine-generated PDFs, PaddleOCR/Tesseract for scanned
2. **Classification** — regex keyword matching (~90% accuracy), LLM fallback when confidence < 0.7
3. **Data Extraction** — HuggingFace Llama-3.3-70B extracts vendor, amounts, dates, line items
4. **Validation** — checks extracted fields against expected schema
5. **Anomaly Detection** — SHA-256 duplicate detection, Z-score outliers, missing field checks
6. **RAG Chat** — answers questions using extracted document context via LLM

## Architecture

```
frontend/          Next.js 15 + Tailwind CSS + Recharts
    ↓ API calls
backend/           Python FastAPI + Celery workers
    ↓ background tasks
Redis              Task queue broker
    ↓
SQLite/PostgreSQL  Document storage
    ↓
HuggingFace API    LLM for extraction + chat (free tier)
```

- **Backend:** Python FastAPI + Celery + Redis for async PDF processing
- **Frontend:** React/Next.js 15 + Tailwind CSS + Recharts
- **PDF Extraction:** pdfplumber (machine-generated) + PaddleOCR/Tesseract (scanned)
- **LLM:** Hugging Face Inference API (primary, free) → Gemini (fallback) → Ollama (local)
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Task Queue:** Celery with Redis broker, solo pool on Windows

## API Endpoints

### Documents
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/documents/upload | Upload PDFs (multipart) |
| GET | /api/documents | List documents (paginated, filterable) |
| GET | /api/documents/{id} | Document detail with extracted data |
| GET | /api/documents/{id}/download | Download original PDF |
| DELETE | /api/documents/{id} | Delete document |
| POST | /api/documents/{id}/reprocess | Re-run extraction pipeline |
| PATCH | /api/documents/{id}/anomalies/{anomaly_id} | Resolve/unresolve anomaly |

### Chat
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/chat/sessions | List chat sessions |
| POST | /api/chat/sessions | Create new session |
| GET | /api/chat/sessions/{id} | Get session with messages |
| PATCH | /api/chat/sessions/{id} | Rename session |
| DELETE | /api/chat/sessions/{id} | Delete session |
| POST | /api/chat/sessions/{id}/messages | Send message and get response |

### Export & Dashboard
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/export/csv | Export extracted data as CSV |
| GET | /api/export/excel | Export extracted data as Excel |
| GET | /api/dashboard/stats | Dashboard statistics |
| GET | /api/dashboard/recent | Recent documents |
| GET | /api/dashboard/timeline | Processing timeline |
| GET | /api/health/services | Service health check |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React 19, Tailwind CSS, Recharts |
| Backend | Python 3.12, FastAPI, SQLAlchemy, Pydantic |
| Task Queue | Celery + Redis |
| LLM | HuggingFace Inference API (Llama-3.3-70B) |
| PDF Processing | pdfplumber, PaddleOCR, Tesseract |
| Database | SQLite (dev) / PostgreSQL (prod) |

## Optional Dependencies

**Ollama (local LLM fallback):**
```bash
ollama pull qwen2.5:3b
```

**Windows Redis:** Install via `winget install taizod1024.redis-windows-fork` or use Docker.

**OCR fallback:** Install Tesseract from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) if PaddleOCR fails.
