# CLAUDE.md

Instructions for any Claude Code session working in this repository.

## What this project is

A personal Learning & Career Development platform (see `docs/PRODUCT.md`).
Monorepo: `backend/` (FastAPI + PostgreSQL) and `frontend/` (React + TypeScript
+ Vite). Full context lives in `docs/` — read `docs/ARCHITECTURE.md` and
`docs/DOMAIN.md` before making structural changes, and check
`docs/ROADMAP.md` for current status before starting new work.

The original autonomous-development brief is preserved at
`Claude Code — Master Prompt for Learning Platform.md` in the repo root —
treat it as background context, not a live spec; `docs/` is the current
source of truth and supersedes it where they differ.

## Ground rules

- **Modular monolith.** No microservices unless justified in `docs/DECISIONS.md`.
- **Clean Architecture layering in the backend**: `api` (HTTP) → `services`
  (business logic / use cases) → `repositories` (persistence) → `models`
  (ORM). Routers never touch the ORM directly; services never import FastAPI.
- **Content is data.** Subjects, competencies, learning paths, challenges,
  questions, achievements, quests are rows in the database (seeded via
  `backend/app/seeds/`), never hardcoded in application logic.
- **XP measures activity. Mastery measures knowledge.** Never conflate them.
- **UUID primary keys** everywhere; timestamps in UTC.
- **Sync SQLAlchemy** (not async) — see `docs/DECISIONS.md` for why. Route
  handlers that touch the DB are plain `def`, not `async def`, so FastAPI
  runs them in the thread pool.
- Enums are stored as `VARCHAR` (`native_enum=False`), not native Postgres
  enum types, so adding a value is a normal migration instead of `ALTER TYPE`.
- Never commit `.env` files or secrets. `.env.example` files document every
  required variable.

## Commit discipline

Commit after every meaningful increment (a working migration, a passing
endpoint, a finished component) — don't batch unrelated work into one commit,
and don't leave the working tree dirty for long stretches. This is how the
project owner tracks progress, not just a style preference.

## Local development

```bash
# 1. Start Postgres (mapped to host port 5434 to avoid clashing with other
#    local projects — see docker-compose.yml)
docker compose up -d

# 2. Backend
cd backend
python -m venv .venv && ./.venv/Scripts/python.exe -m pip install -e ".[dev]"
cp .env.example .env
./.venv/Scripts/python.exe -m alembic upgrade head
./.venv/Scripts/python.exe -m app.seeds.run   # populate initial content
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload

# 3. Frontend
cd frontend
npm install
cp .env.example .env
npm run dev
```

Backend tests: `cd backend && ./.venv/Scripts/python.exe -m pytest`
Frontend tests: `cd frontend && npm test`

## Quality gates before calling anything "done"

1. `ruff format` + `ruff check` (backend), `eslint` (frontend)
2. Type checks: `mypy app` (backend), `tsc --noEmit` (frontend)
3. `pytest` (backend), frontend test suite
4. `alembic upgrade head` runs cleanly against a fresh database
5. `npm run build` succeeds
6. Manually verify the affected flow (curl or browser) — don't trust green
   tests alone for UI changes
7. Update `docs/ROADMAP.md` (and `docs/DECISIONS.md` / `docs/PENDING.md` if
   relevant)

## Autonomous operation

This project is developed autonomously per the instructions in the master
prompt file. Ambiguity that isn't destructive, irreversible, security-, or
finance-critical should be resolved with the best reasonable engineering
judgment, documented in `docs/DECISIONS.md` or `docs/PENDING.md`, and
implementation should continue without waiting for sign-off.
