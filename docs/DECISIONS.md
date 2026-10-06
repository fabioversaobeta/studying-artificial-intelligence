# Architectural Decisions

Lightweight ADR log. Each entry: context, decision, why, what it costs.
Newest first.

---

## Auth hardening: in-memory rate limiting, registration policy, strict CORS

**Decision**: (1) `/auth/login`, `/auth/register` and `/auth/refresh` are
rate limited by a small in-house sliding-window limiter
(`app/core/rate_limit.py`), per client IP (separate bucket per endpoint) and,
on login, per e-mail. Over the limit: 429 `rate_limited` in the standard
error format plus `Retry-After`. (2) `REGISTRATION_ENABLED=false` closes
signups (403); `REGISTRATION_INVITE_CODE`, when set, must be sent as
`invite_code` in the register body (constant-time compare, 403 otherwise).
`GET /auth/registration-info` publicly exposes `{enabled, invite_required}`
so the UI shows the invite field only when needed. (3) CORS allows only the
configured origins, methods `GET/POST/PUT/PATCH/DELETE/OPTIONS` and headers
`Authorization/Content-Type/Accept`; `CORS_ALLOW_ORIGINS` accepts JSON or
CSV and `*` is rejected at boot when `ENVIRONMENT=production`.
**Why in-house instead of `slowapi`**: three endpoints and one counter; a
~60-line limiter is trivially testable (settings are injected via a FastAPI
dependency, so tests turn it off by default) and avoids a dependency.
**Trade-offs**: state is per process, so N workers/replicas multiply the
effective limit and a restart resets it — acceptable for a single-instance
Railway deploy; move to Redis if the backend is ever scaled out.
**Proxy/IP**: `X-Forwarded-For` is ignored unless `TRUST_PROXY_HEADERS=true`
(otherwise clients could spoof it to evade limits). When trusted, the
*last* entry is used: it is the one appended by our own proxy; earlier
entries are client-controlled. Assumes exactly one trusted proxy hop.

---

## Lesson content: modular per-competency, module count scales with complexity

**Context**: manual testing surfaced that the platform had subject/
competency *metadata* (names, descriptions, links to external resources)
but no actual study material — nothing to learn from inside the platform
itself. A flat "one description paragraph per competency" fix would have
been dishonest about depth: SOLID Principles and, say, CAP Theorem do not
deserve the same amount of material.
**Decision**: each competency gets one or more `LearningResource` rows of
`type=LESSON` (markdown in a new `content` column), authored as ordered
modules — `LessonModule(title, content)` — in per-subject Python files
under `backend/app/seeds/lessons/`, wired into `backend/app/seeds/
content.py` via a `lesson_resources()` helper. Module count is a judgment
call per competency (1 for a narrow topic like "Technical Communication",
6 for SOLID — one per principle plus a synthesis module), not a fixed
number.
**Why**: content depth should track real topic complexity, not be forced
into a uniform template. Splitting by subject file (rather than one giant
content file) also let the authoring work be parallelized across
background agents without merge conflicts — each subject's lessons live in
their own file.
**Cost / gotcha hit during authoring**: markdown lesson bodies are Python
`r"""..."""` raw strings; embedding a bare Python docstring (`"""..."""`)
inside a code example within that string prematurely terminates the outer
string and causes a `SyntaxError`. Fixed by using `# comment` instead of
`"""docstring"""` in every embedded code example — documented in the
`lessons/` package so it isn't rediscovered.
**Also fixed alongside this**: `app.seeds.run`'s resource/challenge sync
was insert-only-if-title-missing, so editing an existing lesson's content
and re-running seeds silently did nothing. Changed to a true upsert
(update fields on the existing row by title, not just skip it).

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

## Quests complete on activity events; `GET /gamification/quests` is read-only

**Supersedes**: the earlier decision to auto-complete quests on read.
**Context**: completing quests (persisting a `QuestCompletion` and paying XP)
inside a GET made a read mutate state, delayed XP until someone happened to
open the quest list, and could not be reasoned about as idempotent.
**Decision**: progress is still computed fresh from existing activity data
(no denormalized counters), but completion is recorded when activity happens.
`gamification_service.settle_rewards` evaluates achievements and quests, pays
their XP, and loops until nothing new unlocks (a reward can satisfy another
criterion). It runs from `award_xp` and, for activity that awards no XP
(short study sessions, repeated challenge passes), is called directly by the
activity service. `quest_service.complete_due_quests` only records completions
and returns the quests; the gamification service pays the XP, so there is no
`award_xp` recursion. `GET /gamification/quests` only reads.
**Why**: GET is safe and idempotent, rewards arrive in real time, and the
JSON contract is unchanged.
**Revisit trigger**: if activity sources multiply, move `settle_rewards`
behind a domain event/outbox instead of explicit calls.

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

---

## Refresh-token rotation and revocation (Postgres denylist)

**Decision**:
- Every JWT has a `jti` (uuid4). Revocation is a Postgres denylist table
  `revoked_tokens` (`jti` unique, `user_id`, `token_type`, `expires_at`,
  `revoked_at`) -- no Redis. Tokens are only listed once revoked, so the
  table stays small; `auth_service.purge_expired_revocations()` deletes rows
  whose tokens have expired anyway (no scheduler; call it from a cron/CLI
  when wanted).
- `/auth/refresh` rotates: the presented refresh token is denylisted
  (INSERT ... ON CONFLICT DO NOTHING on the unique `jti`, so concurrent
  rotations of one token cannot both win) and a new access+refresh pair is
  issued.
- **Reuse detection**: presenting an already-used refresh token returns 401
  and sets `users.tokens_valid_after` to now (floored to the second); every
  token with `iat <=` that cutoff is rejected afterwards, which kills all
  sessions of that user (thief and victim) and forces a new login. A
  per-token "family" table was rejected as more machinery than a
  single-user-scale app needs; the cost is that a legitimate user with
  several devices is logged out everywhere on a suspected theft. Because JWT
  `iat` has one-second resolution, a login within the same second as the
  detection also gets rejected -- harmless, retry.
- `POST /auth/logout` (authenticated) denylists the access token's `jti` and
  the refresh token from the body (optional; ignored if invalid or owned by
  another user). `get_current_user` rejects denylisted access tokens and
  tokens issued before `tokens_valid_after`.
- Access-token lifetime reduced from 24h to 60 minutes
  (`ACCESS_TOKEN_EXPIRE_MINUTES`); the frontend already refreshes on 401, so
  this is invisible to users. Refresh tokens stay at 30 days.
- Tokens issued before this change have no `jti` and are rejected (users log
  in again once).
**Why**: closes the "stolen token is valid for 24h" gap documented in
`docs/PENDING.md` using only the existing database.
