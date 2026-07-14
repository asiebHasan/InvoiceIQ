# InvoiceIQ

Agentic Document Processor — upload PDFs, auto-classify, extract structured data, detect anomalies, export results.

## Quick Start

### Option A: Docker (Recommended — works on Windows, Mac, Linux)
```bash
docker-compose up --build
```
Opens at [http://localhost:3000](http://localhost:3000). Redis, OCR, and poppler all handled inside containers.

### Option B: Native Setup

**Prerequisites:**
- Python 3.11+
- Node.js 18+
- Redis
- Gemini API key (free) — get one at https://aistudio.google.com/apikey

#### 1. Get Free Gemini API Key
Sign up at https://aistudio.google.com and generate an API key. No credit card needed.

#### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env  # Edit .env and add your GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```

#### 3. Start Celery Worker
```bash
cd backend
celery -A celery_worker worker -l info
```

#### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

#### 5. Open
Visit [http://localhost:3000](http://localhost:3000)

**Optional — Local LLM (Ollama):** If you have 8GB+ free RAM, you can also run Ollama as a fallback:
```bash
ollama pull qwen2.5:3b
```

---

## Windows Notes

**Redis:** Install via Docker Desktop, or use WSL:
```bash
wsl sudo apt install redis-server
wsl sudo service redis-server start
```

**OCR (PaddleOCR):** Works on Windows via pip. If install fails, the app falls back to Tesseract automatically. Install Tesseract from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).

**Poppler (PDF to images):** Only needed for scanned PDFs on native Windows. Download from [poppler releases](https://github.com/oschwartz10612/poppler-windows/releases), extract, and add `bin/` to your PATH. Or just use Docker — the container has it built in.

**Easiest path on Windows:** Just use `docker-compose up --build`. Everything runs inside Linux containers.

---

## Architecture
- **Backend:** Python FastAPI + Celery + Redis
- **Frontend:** React/Next.js + Tailwind CSS + Recharts
- **PDF Extraction:** pdfplumber (machine-generated) + PaddleOCR/Tesseract (scanned)
- **LLM:** Gemini 2.5 Flash free tier (primary), Ollama local (optional fallback)
- **Database:** SQLite (dev) / PostgreSQL (prod)

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/documents/upload | Upload PDFs |
| GET | /api/documents | List documents |
| GET | /api/documents/{id} | Document detail |
| DELETE | /api/documents/{id} | Delete document |
| POST | /api/documents/{id}/reprocess | Reprocess |
| GET | /api/export/csv | Export CSV |
| GET | /api/export/excel | Export Excel |
| GET | /api/dashboard/stats | Dashboard stats |
| GET | /api/health/services | Service health |
