# Roadmap

Statuses: `NOT_STARTED` | `IN_PROGRESS` | `BLOCKED` | `COMPLETED`

Last updated: 2026-08-15

## v1 — Foundation (current milestone)

Target: the "Definition of Done" flow — register, log in, see the
dashboard, set a goal, study a competency, complete an activity, earn XP,
see progress and mastery, come back later and continue.

| Feature | Status | Notes |
|---|---|---|
| Monorepo scaffold, Docker Postgres, docs structure | COMPLETED | |
| Backend foundation (FastAPI, config, DB session, health checks) | COMPLETED | Sync SQLAlchemy 2.0 — see docs/DECISIONS.md |
| Auth (register/login/refresh/me, Argon2 + JWT) | COMPLETED | Tested end-to-end |
| Core domain schema + migrations (20 tables) | COMPLETED | |
| Learning services (subjects/competencies/skill-tree state, paths, study sessions, goals) | COMPLETED | |
| Mastery scoring (engagement + practice + retention) | COMPLETED | Formula in docs/DOMAIN.md |
| Spaced repetition (SM-2-lite) | COMPLETED | Review due-list + recall submission |
| Gamification (XP, levels, streaks, achievements, quests) | COMPLETED | Quests auto-complete on read — see docs/DECISIONS.md |
| Dashboard aggregate endpoint | COMPLETED | |
| Seed data (7 subjects, 30 competencies, 3 paths, 9 achievements, 4 quests) | COMPLETED | Idempotent (`app.seeds.run`) |
| Backend test suite | COMPLETED | 51 tests: domain unit tests + API integration tests |
| Backend lint/type-check clean (ruff + mypy) | COMPLETED | |
| Frontend scaffold (React + TS + Vite + Tailwind) | IN_PROGRESS | |
| Frontend auth flow | NOT_STARTED | |
| Frontend dashboard + learning UI | NOT_STARTED | |
| Deployment config (Vercel + Railway) | NOT_STARTED | |
| GitHub repository created + pushed | NOT_STARTED | |

## Explicitly deferred past v1

These are real product goals (see `docs/PRODUCT.md`) intentionally not
built yet, to keep v1 shippable. Tracked here so they're not forgotten, not
because they're blocked.

| Feature | Status | Notes |
|---|---|---|
| Assessments / question bank (formal quizzes) | NOT_STARTED | See docs/PENDING.md |
| Automated challenge grading | NOT_STARTED | Self-assessed for now — docs/DECISIONS.md |
| AI Mentor / AI abstraction layer | NOT_STARTED | Provider-agnostic interface, not started — docs/PENDING.md |
| Adaptive "what should I study today" recommendation engine | NOT_STARTED | |
| Interview simulation (guided sessions, scoring) | NOT_STARTED | `InterviewSession` not yet modeled |
| Project tracking (`Project` entity) | NOT_STARTED | |
| Career readiness scoring against a job description | NOT_STARTED | |
| Token revocation / logout denylist | NOT_STARTED | docs/PENDING.md |
| Deeper observability (tracing/metrics) beyond health checks | NOT_STARTED | Revisit once actually deployed |

## Next up (in priority order)

1. Finish frontend scaffold, wire up the API client and routing shell.
2. Auth flow: login/register pages, token storage, protected routes.
3. Dashboard page against the real `/dashboard` endpoint.
4. Subjects/skill-tree browsing UI, study session logging UI, challenge
   submission UI.
5. Deployment configuration for Vercel (frontend) and Railway
   (backend + Postgres), plus `docs/DEPLOYMENT.md`.
6. Create the GitHub repository and push.
