# EREX Frontend (Next.js/React)

A modern UI for interacting with the EREX pipeline APIs (upload, run pipeline, inspect summaries, and request tech insights).

## Prerequisites
- Node.js 18+
- Backend running (see `../backend`, endpoints exposed on the same host/port as your env config)

## Setup
```bash
cd frontend
npm install
```

## Development
```bash
npm run dev
```
- Default dev server: http://localhost:3000
- API base URL: configure via env (`VITE_API_BASE`, defaults to same origin). Create `.env.local` if needed:
  ```bash
  VITE_API_BASE=http://localhost:8000
  ```

## Available Scripts
- `npm run dev` — start dev server
- `npm run build` — production build
- `npm run preview` — preview production build

## Backend Endpoints Used
- `GET /pipeline/config`
- `POST /pipeline/upload` (multipart files[])
- `DELETE /pipeline/files`
- `POST /pipeline/run`
- `POST /pipeline/tech-insight`

## Notes
- No external LLM key is required on the frontend; all model calls go through backend (`/pipeline/tech-insight`).
- Ensure backend `OPENAI_API_KEY` is set when using tech insight; otherwise the UI should display an error from the API.
