# PaperCraft Backend
 
FastAPI backend service for PaperCraft. Python 3.12+, managed with [uv](https://docs.astral.sh/uv/).

## Setup

```bash
cd backend
cp .env.example .env   # fill in Supabase, Postgres, and Gemini API values
uv sync
```

## Run

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Alternative: `uv run python app/main.py`

## Day-to-day Commands

| Task | Command |
| :--- | :--- |
| Install / update deps | `uv sync` |
| Install ingestion deps | `uv sync --extra ingest` |
| Add a dependency | `uv add <package>` |
| Lint | `uv run ruff check .` |
| Tests | `uv run pytest` |
| DB migrations | `uv run alembic upgrade head` |

Env vars are read from `.env` via `app.config.settings` — do not call `os.getenv` in app code.

