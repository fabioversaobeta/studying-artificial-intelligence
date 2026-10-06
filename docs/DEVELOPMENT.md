# Development Guide

## Prerequisites

- Python 3.11+ (developed against 3.14)
- Node.js 20+
- Docker (for local Postgres)

## First-time setup

```bash
# 1. Postgres (mapped to host port 5434 — see docs/DECISIONS.md for why
#    not the default 5432)
docker compose up -d

# 2. Create the dev + test databases
docker exec learning-platform-postgres createdb -U learning_platform learning_platform_test

# 3. Backend
cd backend
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e ".[dev]"
cp .env.example .env
./.venv/Scripts/python.exe -m alembic upgrade head
./.venv/Scripts/python.exe -m app.seeds.run
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload
# API now at http://127.0.0.1:8000, docs at /docs

# 4. Frontend (separate terminal)
cd frontend
npm install
cp .env.example .env
npm run dev
# App now at http://127.0.0.1:5173
```

(On macOS/Linux, use `.venv/bin/python` instead of `.venv/Scripts/python.exe`.)

## Everyday commands

| Task | Command |
|---|---|
| Run backend | `cd backend && ./.venv/Scripts/python.exe -m uvicorn app.main:app --reload` |
| Run backend tests | `cd backend && ./.venv/Scripts/python.exe -m pytest` |
| Lint backend | `cd backend && ./.venv/Scripts/python.exe -m ruff check app tests` |
| Format backend | `cd backend && ./.venv/Scripts/python.exe -m ruff format app tests` |
| Type-check backend | `cd backend && ./.venv/Scripts/python.exe -m mypy app` |
| New migration | `cd backend && ./.venv/Scripts/python.exe -m alembic revision --autogenerate -m "..."` |
| Apply migrations | `cd backend && ./.venv/Scripts/python.exe -m alembic upgrade head` |
| Re-run seeds (idempotent) | `cd backend && ./.venv/Scripts/python.exe -m app.seeds.run` |
| Run frontend | `cd frontend && npm run dev` |
| Build frontend | `cd frontend && npm run build` |
| Lint frontend | `cd frontend && npm run lint` |
| Type-check frontend | `cd frontend && npm run typecheck` |
| Test frontend (Vitest) | `cd frontend && npm test` (watch: `npm run test:watch`) |

## Testing strategy

- `tests/domain/` — pure unit tests against `app.domain.*` (leveling,
  mastery, spaced repetition). No database.
- `tests/test_*.py` — integration tests against a real Postgres database
  (`learning_platform_test`, created above). Each test runs inside a
  savepoint-based transaction that's rolled back afterward (see
  `tests/conftest.py`), so tests never leak state into each other and never
  touch the dev database.

Run everything: `cd backend && ./.venv/Scripts/python.exe -m pytest`

Frontend: Vitest + Testing Library + jsdom. `cd frontend && npm test` (single run)
or `npm run test:watch`. Tests live next to the code as `*.test.ts(x)`; the
jest-dom setup is in `src/test/setup.ts`.

## Before calling a change "done"

See the Quality Gates checklist in `CLAUDE.md` — format, lint, type-check,
test, migrations apply cleanly, frontend builds, manually verify the
affected flow.

## Common issues

- **`docker compose up` fails to bind port 5432/5434**: another local
  project is already using that port. Check `docker ps` and either stop it
  or change the host-side port mapping in `docker-compose.yml` (and the
  matching `DATABASE_URL` in `.env`).
- **`alembic upgrade head` can't connect**: confirm the Postgres container
  is healthy (`docker compose ps`) and `.env`'s `DATABASE_URL` matches
  `docker-compose.yml`'s port mapping.
- **pytest can't connect to `learning_platform_test`**: that database isn't
  auto-created by `docker-compose.yml` (only the dev DB is, via
  `POSTGRES_DB`) — run the `createdb` command from setup step 2.
