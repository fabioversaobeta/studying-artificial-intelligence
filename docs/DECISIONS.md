# Architectural Decisions

Lightweight ADR log. Each entry: context, decision, why, what it costs.
Newest first.

---

## Local Postgres on port 5434, not 5432

**Context**: `docker compose up` failed — port 5432 was already bound by an
unrelated project's Postgres container on this machine.
**Decision**: map this project's Postgres to host port 5434
(`docker-compose.yml`), matched by `DATABASE_URL` in `.env.example`.
**Why**: avoid clobbering other local projects; keep this repo fully
self-contained regardless of what else is running.

---

## Sync SQLAlchemy, not async

**Context**: FastAPI supports both sync (`def`) and async (`async def`)
route handlers; SQLAlchemy 2.0 supports both sync and async engines/sessions.
**Decision**: sync `Session`, `psycopg` (v3) driver, plain `def` route
handlers for anything touching the database.
**Why**: FastAPI automatically runs `def` handlers in a thread pool, so
requests still don't block each other — the concurrency FastAPI is known
for isn't lost. What's gained is a codebase where nobody has to reason
about async session lifecycles, async context managers in every
repository, or the sharp edges of mixing sync and async SQLAlchemy. At
single-user scale, the throughput difference is irrelevant; the
readability difference is not — and readability matters more here because
this project is explicitly also a Python-learning vehicle for its owner
(see the "Python Learning Objective" in the original brief).
**Cost / revisit trigger**: if this ever needs to serve genuinely
concurrent multi-user load where DB-bound thread-pool contention becomes
the bottleneck, migrate to `AsyncSession` + `asyncpg`. The repository-layer
functions are the only place that would need `await` added; services and
API routes would need matching `async def` — a mechanical but real
refactor, not attempted preemptively.

---

## Enums stored as VARCHAR, not native Postgres enum types

**Context**: SQLAlchemy can map a Python enum to either a native Postgres
`CREATE TYPE ... AS ENUM` or a plain `VARCHAR` with a `CHECK` constraint.
**Decision**: `VARCHAR` + `CHECK` (`native_enum=False` on every enum column,
see `app.models.learning._enum` / `app.models.gamification._enum`).
**Why**: adding a new enum value to a native Postgres enum requires
`ALTER TYPE ... ADD VALUE`, which historically couldn't run inside a
transaction alongside other DDL and has other operational quirks. A
`VARCHAR` column with a `CHECK` constraint is a normal, fully-transactional
Alembic migration. Given this domain will keep growing new criterion
types, resource types, etc., minimizing migration friction wins over the
marginal storage/validation efficiency of a native enum.

---

## UUID primary keys everywhere

**Decision**: every table uses a UUID primary key, not an auto-increment
integer.
**Why**: IDs never leak row-count or creation-order information through the
API responses. Also removes any future friction around client-generated IDs
or merging data from multiple sources.
**Cost**: slightly larger index size than `BIGINT`; irrelevant at this
project's scale.

---

## Mastery and XP are computed independently, never conflated

**Decision**: `Mastery` (0-100 knowledge score) and `GamificationProfile.
total_xp` (activity ledger) are separate tables, separate services
(`mastery_service` vs. `gamification_service`), and neither reads the
other's value as an input.
**Why**: the original product brief is explicit that "XP measures activity,
mastery measures knowledge... do not mix the two concepts." If XP could
buy mastery, the system would reward time-spent over demonstrated
competence — exactly the failure mode a mastery system exists to prevent.
See `docs/DOMAIN.md` for both formulas.

---

## Quests auto-complete on read instead of exposing a "claim" endpoint

**Context**: quest progress could either be tracked incrementally (update a
progress counter on every relevant event) or computed fresh from existing
activity data whenever the quest list is requested.
**Decision**: compute fresh on every `GET /gamification/quests`, and
auto-complete (persist a `QuestCompletion`, award XP) the moment a quest's
target is met within that same request.
**Why**: no denormalized progress counter to keep in sync across every
place XP-worthy activity can happen (study sessions, challenges, reviews).
The tradeoff is that a completed quest's XP isn't awarded until the next
time the quest list happens to be fetched (e.g. on a dashboard visit) —
acceptable for a personal tool with no real-time notification requirement.
**Revisit trigger**: if quests need real-time "you just completed a quest!"
notifications, this needs an event-driven trigger instead of read-time
evaluation.

---

## Challenge submissions are self-assessed, not automatically graded

**Context**: the platform needs a "prove you can do it" mechanism per
competency, but automated grading (running code, LLM-based rubric scoring)
is a substantial system on its own.
**Decision**: v1 challenge submissions are self-reported pass/fail
(`ChallengeSubmissionStatus`), with XP awarded once per (user, challenge)
on first pass.
**Why**: honest v1 scope. An unimplemented "AI grading" stub that always
returns "passed" would be the exact kind of fake functionality the project
rules prohibit. Self-assessment is real, working, and honest about being
v1 — see `docs/PENDING.md` for automated grading as a future extension
point that the architecture doesn't block.

---

## Modular monolith, not microservices

**Decision**: one FastAPI service, one database, internal module boundaries
(`api → services → repositories → models`, one repository/service module
per aggregate) instead of separate deployable services.
**Why**: this is a single-owner personal tool. Microservices buy
independent deployability and failure isolation at the cost of operational
complexity (service discovery, distributed tracing, network calls where
function calls used to be) — costs with no matching benefit here. The
internal module boundaries are drawn *as if* they could become service
boundaries later, so the option isn't foreclosed, but nothing is built
prematurely for a split that may never happen.
