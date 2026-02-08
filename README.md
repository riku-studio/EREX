# EREX

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

[![License: PolyForm Noncommercial](https://img.shields.io/badge/license-PolyForm%20Noncommercial-blue)](LICENSE.md)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.x-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/docker-compose-2496ED?logo=docker&logoColor=white)
![GPU](https://img.shields.io/badge/semantic-CUDA%20ready-76B900?logo=nvidia&logoColor=white)

Semantic email extraction platform powered by configurable NLP pipelines and embedding-based understanding.

## Features

- Semantic filtering with Sentence-Transformers embeddings.
- Lightweight line filtering to remove signatures/disclaimers/noise.
- Block splitting for multi-position emails.
- Configurable keyword extraction and rule-based classification.
- Aggregated analytics and optional LLM-based tech insight.
- Frontend + backend architecture (React/Vite + FastAPI).

## Quick Start

### Prerequisites

- Docker / Docker Compose
- `.env` file at repository root (based on `.env.example`)

### Run with Docker

```bash
cd infra
docker compose up --build
```

### Access

- Frontend: `http://localhost:8002`
- Backend: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`

## GPU / CPU Mode

Configure in `.env`:

- `SEMANTIC_ACCELERATOR=cpu|gpu|auto`
- `SEMANTIC_DEVICE=` (optional, e.g. `cuda:0`)

Check GPU in container:

```bash
cd infra
docker compose exec backend nvidia-smi
```

## Core API

- `GET /pipeline/config`
- `POST /pipeline/upload`
- `GET /pipeline/files`
- `DELETE /pipeline/files`
- `POST /pipeline/run`
- `POST /pipeline/run/start`
- `GET /pipeline/run/{job_id}/progress`
- `GET /pipeline/run/{job_id}/result`
- `POST /pipeline/history`
- `GET /pipeline/history`
- `GET /pipeline/history/{id}`
- `DELETE /pipeline/history/{id}`
- `POST /pipeline/tech-insight`

## Development

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Configuration Source

Pipeline configuration is loaded from file by default.
If database storage is available, runtime source becomes `db`; otherwise fallback remains `file`.

## Project Structure

- `backend/app/services/` core pipeline modules
- `backend/config/` semantic templates, dictionaries, rules
- `frontend/` web UI
- `infra/` Docker assets
- `docs/` architecture and module documentation

## License

See `LICENSE.md`.
