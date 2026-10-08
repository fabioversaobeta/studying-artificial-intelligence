# Roadmap

Statuses: `NOT_STARTED` | `IN_PROGRESS` | `BLOCKED` | `COMPLETED`

Last updated: 2026-08-15 (lesson content pass)

## v1 — Foundation (current milestone)

Target: the "Definition of Done" flow — register, log in, see the
dashboard, set a goal, study a competency, complete an activity, earn XP,
see progress and mastery, come back later and continue. **This flow is now
fully implemented and verified end-to-end in a real browser against the
real backend and database.**

| Feature | Status | Notes |
|---|---|---|
| Monorepo scaffold, Docker Postgres, docs structure | COMPLETED | |
| Backend foundation (FastAPI, config, DB session, health checks) | COMPLETED | Sync SQLAlchemy 2.0 — see docs/DECISIONS.md |
| Auth (register/login/refresh/me, Argon2 + JWT) | COMPLETED | Tested end-to-end |
| Core domain schema + migrations (20 tables) | COMPLETED | |
| Learning services (subjects/competencies/skill-tree state, paths, study sessions, goals) | COMPLETED | |
| Mastery scoring (engagement + practice + retention) | COMPLETED | Formula in docs/DOMAIN.md |
| Spaced repetition (SM-2-lite) | COMPLETED | Review due-list + recall submission; not yet surfaced in the frontend UI |
| Gamification (XP, levels, streaks, achievements, quests) | COMPLETED | Quests auto-complete on read — see docs/DECISIONS.md |
| Dashboard aggregate endpoint | COMPLETED | |
| Seed data (7 subjects, 30 competencies, 3 paths, 9 achievements, 4 quests) | COMPLETED | Idempotent (`app.seeds.run`); verified against a fresh DB |
| In-platform lesson content (all 30 competencies) | COMPLETED | 77 markdown modules (`backend/app/seeds/lessons/`), module count scaled to real topic complexity (1-6 per competency) — see docs/DOMAIN.md |
| Backend test suite | COMPLETED | 51 tests: domain unit tests + API integration tests |
| Backend lint/type-check clean (ruff + mypy) | COMPLETED | Verified clean after the S1 lint pass (alembic/versions excluded via ruff extend-exclude) |
| Frontend scaffold (React + TS + Vite + Tailwind) | COMPLETED | Dark theme adapted from fabiobandacheski.com |
| Frontend auth flow | COMPLETED | Register/login/logout, protected routes, session restore via refresh cookie, auto token refresh on 401 |
| Frontend dashboard + learning UI | COMPLETED | Dashboard, subjects, skill tree, study sessions, challenges, goals, and rendered lesson content (react-markdown + remark-gfm) — verified live in-browser, zero console errors |
| Deployment config (Vercel + Railway) | COMPLETED | `frontend/vercel.json`, `backend/railway.toml`; DATABASE_URL scheme auto-normalized for Railway's Postgres plugin — see docs/DEPLOYMENT.md |
| GitHub repository created + pushed | COMPLETED | Private repo: https://github.com/fabioversaobeta/studying-artificial-intelligence |

## Not yet in the frontend (backend already supports these)

| Feature | Status | Notes |
|---|---|---|
| Spaced-repetition review UI (due list, recall submission) | DONE | `/reviews` page (G1) + dashboard shortcut |
| Achievements / quests UI | DONE | `/achievements` page (G2) |
| Learning paths UI | DONE | `/learning-paths` and `/learning-paths/:slug` (G3) |
| Assessments / question bank (quizzes) | DONE | I2: translatable questions (en/pt-BR), deterministic grading, self-graded short answers, anti-farm XP, Practice mastery signal; `/quizzes` UI; pilot of 12 questions (bulk generation is I6) — docs/DOMAIN.md |
| User content-language preference + Settings page | DONE | J6: `PATCH /users/me`, `/settings` |
| UI localisation (en / pt-BR) | DONE | J7: typed dictionaries in `frontend/src/i18n/`, no library; follows `preferred_language`, switches instantly from Settings — docs/DECISIONS.md |

## Explicitly deferred past v1

These are real product goals (see `docs/PRODUCT.md`) intentionally not
built yet, to keep v1 shippable. Tracked here so they're not forgotten, not
because they're blocked.

| Feature | Status | Notes |
|---|---|---|
| Automated challenge grading | NOT_STARTED | Self-assessed for now — docs/DECISIONS.md |
| AI Mentor / AI abstraction layer | NOT_STARTED | Provider-agnostic interface, not started — docs/PENDING.md |
| Adaptive "what should I study today" recommendation engine | NOT_STARTED | |
| Interview simulation (guided sessions, scoring) | NOT_STARTED | `InterviewSession` not yet modeled |
| Project tracking (`Project` entity) | NOT_STARTED | |
| Career readiness scoring against a job description | NOT_STARTED | |
| Token revocation / logout denylist | DONE | docs/DECISIONS.md (C3) |
| Tokens: HttpOnly refresh cookie, in-memory access token, CSRF, same-origin proxy, CSP/security headers | DONE | docs/DECISIONS.md (C5); real deploy of the rewrite deferred |
| Deeper observability (tracing/metrics) beyond health checks | NOT_STARTED | Revisit once actually deployed |

## Next up (in priority order)

1. Actually deploy to Railway + Vercel using docs/DEPLOYMENT.md and verify
   the production flow end-to-end.
2. Frontend UI for spaced-repetition reviews, achievements/quests, and
   learning paths (backend already supports all three).
3. Frontend test suite (component/integration tests) — none exist yet;
   the frontend has been verified manually in-browser but not automated.
4. Then: pick up the "Explicitly deferred past v1" list based on what's
   most useful for the owner's interview-prep timeline.
