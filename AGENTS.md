# Repository Guidelines

## Project Structure & Module Organization
`backend/app` contains the FastAPI service; `main.py` exposes `/` and `/health`, `utils/config.py` centralizes environment settings, and `utils/logging.py` defines structured logging. Dependencies live in `backend/pyproject.toml` and `uv.lock`, while runtime artifacts land in the gitignored `logs/` directory. System references are stored in `docs/architecture/`, and container assets reside in `infra/docker-compose.yml`. Place automated tests in `tests/`, mirroring module names (`app/foo.py` → `tests/test_foo.py`).

## Build, Test, and Development Commands
- `cd backend && uv sync` — install dependencies from `pyproject.toml`.
- `cd backend && uv run uvicorn app.main:app --reload --port 8000` — run the API locally with live reload.
- `cd backend && uv run pytest` — execute the FastAPI test suite.
- `docker compose -f infra/docker-compose.yml up --build myapp` — build and run the containerized stack.

## Coding Style & Naming Conventions
Target Python 3.10+, four-space indents, and type hints on public functions. Keep modules small, grouping related routers or services together; use `snake_case` for functions/variables and `PascalCase` for classes. Run `uv run ruff check --fix` before committing and rely on the shared `logger`, enabling JSON logs by setting `LOG_FORMAT=json` in `.env`.

## Testing Guidelines
Use `pytest` and `httpx.AsyncClient` for async route assertions. Name files `tests/test_<module>.py` and include fixtures capturing success and failure paths. Enforce ≥80% coverage on touched modules via `uv run pytest --cov=app --cov-report=term-missing`, and add payload examples that align with `docs/architecture/system-overview.md`.

## Commit & Pull Request Guidelines
Follow Conventional Commits (`feat: add health check`, `chore: bump deps`) with focused scope and wrap summaries at 72 characters. PRs should link issues, describe architecture or configuration impacts, and list the commands executed (tests, `uvicorn`, docker compose). Attach screenshots or `curl` traces for API-facing changes so reviewers can replay them quickly.

## Security & Configuration Tips
Keep `.env` files local only; rely on defaults in `Config` or pass secrets via orchestration. When enabling `LOG_TO_FILE=true`, confirm `logs/` stays writable yet untracked. Validate new settings via `Config.summary()` in tests to ensure unsafe defaults never reach production.
