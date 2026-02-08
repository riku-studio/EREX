# EREX

Language: [中文](README.md) | **English** | [日本語](README.ja.md)

## About
EREX is a semantic email extraction platform focused on semantic understanding.  
It uses Transformer embeddings to perform semantic matching, block-level splitting, and intent-aware extraction on large email datasets (PST/MSG/EML), then converts results into structured data.

### Core Capabilities
- Semantic filtering with Sentence-Transformers similarity + template matching.
- Lightweight line filtering to remove noise (signatures, disclaimers, decorations).
- Block splitting by markers such as `案件` / `案件名` for multi-position messages.
- Keyword extraction and classification with configurable dictionaries/rules.
- Aggregation and insights, including optional OpenAI/LiteLLM tech insights.
- Full-stack UI with FastAPI backend + React/Vite frontend.

## Quick Start (Docker)
### 1. Prerequisites
- Docker / Docker Compose installed.
- Create `.env` at repo root (based on `.env.example`).
- Configure required values:
  - `OPENAI_API_KEY` (optional, for tech insight)
  - Service settings (ports/log/db/etc.)

### 2. Build and Run
```bash
cd infra
docker compose up --build
```

### 2.1 CPU / GPU switch for semantic processing
Set in `.env`:
- `SEMANTIC_ACCELERATOR=cpu|gpu|auto`
- `SEMANTIC_DEVICE=` (optional, e.g. `cuda:0`)

Check GPU inside container:
```bash
cd infra
docker compose exec backend nvidia-smi
```

### 3. Access
- Frontend: `http://localhost:8002`
- Backend API: `http://localhost:8000` (`/docs` for OpenAPI)

## Main API Endpoints
- `GET /pipeline/config` - current runtime config.
- `POST /pipeline/upload` / `GET /pipeline/files` / `DELETE /pipeline/files` - file management.
- `POST /pipeline/run` - run full pipeline.
- `POST /pipeline/run/start` + progress/result endpoints - async execution.
- `POST /pipeline/history` and history endpoints - manual result save/manage.
- `POST /pipeline/tech-insight` - LLM-based keyword explanation.

## Development
- Backend: `cd backend && uv run uvicorn app.main:app --reload --port 8000`
- Frontend: `cd frontend && npm install && npm run dev`

## Config Source (DB / File)
Pipeline config defaults to files.  
If DB is available, frontend save writes to DB and response source becomes `db`; otherwise fallback is `file`.

## Key Directories
- `backend/app/services/` - core pipeline modules.
- `backend/config/` - templates, keyword dictionaries, rules.
- `frontend/` - React UI.
- `infra/` - Docker Compose and deployment assets.
