# Learning Platform

A personal learning management and career development platform: goals,
subjects, competencies, learning paths, study sessions, challenges, mastery
tracking, spaced repetition, and gamification (XP, levels, achievements,
quests, streaks), built to progressively evolve toward AI-assisted,
adaptive learning and interview/career readiness.

See [`docs/PRODUCT.md`](docs/PRODUCT.md) for the product vision,
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how the system is built,
and [`docs/ROADMAP.md`](docs/ROADMAP.md) for current status.

## Stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS — deployed to Vercel
- **Backend**: Python, FastAPI, SQLAlchemy, Alembic — deployed to Railway
- **Database**: PostgreSQL — hosted on Railway

## Quick start

```bash
docker compose up -d          # local PostgreSQL

cd backend
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -e ".[dev]"
cp .env.example .env
./.venv/Scripts/python.exe -m alembic upgrade head
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload

cd ../frontend
npm install
cp .env.example .env
npm run dev
```

Full developer instructions: [`CLAUDE.md`](CLAUDE.md) and
[`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).
