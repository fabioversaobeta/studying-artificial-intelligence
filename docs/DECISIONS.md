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

## Observability: stdlib logging + pure-ASGI request-id middleware, optional Sentry

**Decision**: request ids and access logs come from a pure ASGI middleware
(`app/core/middleware.py`) that sets a `ContextVar`; a `logging.Filter` copies
it onto every record, and `LOG_FORMAT=text|json` picks a stdlib formatter
(`app/core/logging.py`). Sentry is optional: `sentry-sdk[fastapi]` lives in the
`observability` extra, is imported lazily, and is initialised only if
`SENTRY_DSN` is set.
**Why**: no new runtime dependency and no vendor lock-in for a single-owner
app; pure ASGI (not `BaseHTTPMiddleware`) keeps contextvars intact for
sync endpoints running in the thread pool. Incoming `X-Request-ID` is only
trusted if it matches `[A-Za-z0-9._-]{1,64}`, otherwise a UUID is generated
(prevents log injection). The global 500 handler runs outside user middleware,
so it reads the id from `request.state` and adds `error.request_id` (additive)
plus the header itself. Metrics and tracing are deferred until a live deploy
exists (see `docs/PENDING.md`).

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
- `POST /auth/logout` denylists the access token's `jti` and the refresh token
  (since C5 the latter comes from the HttpOnly cookie, not the body; both are
  optional; ignored if invalid or owned by another user). `get_current_user` rejects denylisted access tokens and
  tokens issued before `tokens_valid_after`.
- Access-token lifetime reduced from 24h to 60 minutes
  (`ACCESS_TOKEN_EXPIRE_MINUTES`); the frontend already refreshes on 401, so
  this is invisible to users. Refresh tokens stay at 30 days.
- Tokens issued before this change have no `jti` and are rejected (users log
  in again once).
**Why**: closes the "stolen token is valid for 24h" gap documented in
`docs/PENDING.md` using only the existing database.

## Composite per-user indexes (E2), added only with EXPLAIN evidence

**Decision**: one migration (`b7e1c4a9d3f5`) adds composite indexes and
drops the single-column `user_id` indexes they extend:

- `study_sessions (user_id, occurred_at DESC)` and `(user_id, competency_id)`
- `xp_awards (user_id, created_at)`
- `challenge_submissions (user_id, challenge_id)` and `(user_id, submitted_at)`

Not added (no evidence of benefit): `reviews`, `learning_goals`,
`mastery_records`, `quest_completions` -- their per-user row counts are
bounded by the catalog size or tiny, the existing `user_id` / unique
indexes already give sub-millisecond plans, and `quest_completions` /
`reviews` / `mastery_records` already have `(user_id, ...)` unique indexes.

**Evidence** (local Postgres container, `EXPLAIN (ANALYZE)`, synthetic data: 2000
users, ~300k study sessions, 300k+30k xp awards, 66k submissions, 80k
reviews/mastery rows; one "heavy" user with ~30k sessions, ~30k xp awards,
~6k submissions; both runs after `VACUUM ANALYZE`, best of 2 runs):

| Query (repository) | Before (`ix_*_user_id` only) | After |
|---|---|---|
| list sessions newest-first, LIMIT 50 | Bitmap scan 30k rows + top-N sort, ~7 ms | Index scan in index order, ~0.45 ms |
| count sessions since (quests/achievements) | scan 30k rows, filter, ~11 ms | index-only scan, ~0.2 ms |
| minutes for (user, competency) (mastery) | 30k rows, filter, ~4 ms | `(user_id, competency_id)` bitmap, ~1 ms |
| sum XP since | 30k rows, filter, ~10 ms | range on `(user_id, created_at)`, ~1.1 ms |
| newest XP awards, LIMIT 20 | bitmap + sort, ~10-15 ms | backward index scan, ~0.1 ms |
| passed challenges for competency | user_id + challenge_id BitmapAnd, ~1-6 ms | `(user_id, challenge_id)`, ~0.4 ms |
| passed challenges since | 6k rows filtered, ~1.8 ms | `(user_id, submitted_at)`, ~0.28 ms |

For a typical user (~150 rows) every query was already <2 ms before the
change, so the benefit is for heavy/long-lived users and keeps write cost in
check (three single-column indexes were replaced, not stacked). The count of
all sessions (`COUNT(*)` per user, pagination total) stays ~2 ms either way.
**Why**: per-user activity tables grow without bound while the old
`user_id`-only index forced reading every row of the user and sorting or
filtering in memory.

## Deleting study sessions and goals: hard delete, no XP refund (D6)

**Decision (owner, 2026-10-06)**: `DELETE /study-sessions/{id}` and
`DELETE /goals/{id}` return 204; a missing id or one owned by another user
returns 404 (existence is not leaked). Deleting a session does **not** refund
XP: `xp_awards` (the ledger), `gamification_profile.total_xp`, level, streak,
and already-earned achievements/quest completions are untouched. XP measures
activity that actually happened; removing the record of it later does not
un-happen it, and refunding would also make levels and achievements move
backwards. **Mastery** measures knowledge, so it is recomputed for the
session's competency (`mastery_service.recompute_mastery`) -- it drops, or
returns to 0 if that was the last session.

Hard delete rather than soft delete: nothing references `study_sessions` or
`learning_goals` by foreign key. `xp_awards.reference_id` is a plain nullable
UUID without a FK, so the ledger row simply keeps pointing at an id that no
longer exists (no migration needed). A `deleted_at` column would force every
read/aggregate (mastery minutes, quests, achievements counts, dashboards) to
filter it for no benefit. Consequences: counts derived from sessions
(e.g. the "study sessions" achievement criterion, weekly quest progress)
may decrease after a delete, but anything already earned stays earned. The
spaced-repetition `reviews` row is not touched (it is review state, not
session history).

## Tokens: in-memory access token plus HttpOnly refresh cookie (same-origin API)

**Decision** (roadmap item C5; owner directive: pick the best security
solution, not the easy or merely popular one):

- **Refresh token** (30 days) lives only in a cookie: `HttpOnly`, `Secure`
  (forced when `ENVIRONMENT=production`), `SameSite=Strict` by default
  (`COOKIE_SAMESITE`), `Path=/api/v1/auth`, host-only (no `Domain`). JavaScript
  can never read it, so XSS cannot exfiltrate the long-lived credential, and
  the browser sends it only to the four auth routes. Name: `__Secure-refresh_token`
  when Secure, `refresh_token` on plain-http dev. The `__Host-` prefix would
  be stricter but requires `Path=/`, which would send the cookie to every
  API route; the narrow path matters more, so `__Secure-` it is.
- `/auth/login`, `/register` and `/refresh` return only `{access_token,
  token_type}`; the refresh token is no longer in any JSON body. `/refresh`
  takes no body and reads the cookie; it rotates it (C3 rotation, reuse
  detection, `revoked_tokens`, `tokens_valid_after` and the rate limit are
  unchanged). A failed refresh also expires the dead cookie.
- **Access token** (60 min) lives only in a JS module variable
  (`frontend/src/lib/session.ts`): never `localStorage`/`sessionStorage`/
  IndexedDB. A page load restores the session with `POST /auth/refresh`;
  the 401 -> refresh -> retry flow and in-tab deduplication stay. `token-storage.ts`
  (localStorage) was removed; its tests became `session.test.ts`.
- `POST /auth/logout` no longer requires a Bearer token: it is cookie-driven
  (CSRF-protected), revokes the cookie's refresh token and, if a valid Bearer
  token is also sent, its access token, and always answers 204 + expires the
  cookie. This way logout works after the access token expired or on a fresh
  tab, which a Bearer-only logout could not do.
- **CSRF** (only `/auth/refresh` and `/auth/logout` use the ambient cookie;
  all other endpoints need `Authorization: Bearer`, which cross-site requests
  cannot attach): (1) `SameSite=Strict`; (2) required custom header
  `X-CSRF-Protection: 1` (cannot be sent cross-origin without a CORS
  preflight, which only `CORS_ALLOW_ORIGINS` pass); (3) if the browser sent
  `Origin` (or else `Referer`) it must be in `CORS_ALLOW_ORIGINS`, `null` is
  rejected. Chosen over double-submit-cookie / synchronizer tokens: those
  need a second, JS-readable secret (a cookie readable by JS, or a
  token endpoint plus state) and work correctly only if subdomains are
  trusted; the header + Origin + SameSite combination is stateless, has no
  secret to leak, and is what OWASP lists for JSON APIs called by script. A
  request with neither Origin nor Referer but with the header is allowed
  (non-browser client; a browser cannot produce it cross-site).
- **First-party cookies via same origin**: Vercel and Railway are different
  sites; cross-site cookies need `SameSite=None`, which Safari ITP and
  Chrome's third-party-cookie phase-out block. The browser therefore talks only
  to the frontend origin: Vercel rewrite `/api/:path*` -> Railway in
  `frontend/vercel.json` in production, Vite `server.proxy` (and `preview.proxy`)
  to `http://127.0.0.1:8000` in dev, `VITE_API_URL` empty (relative URLs).
  `SameSite=None` stays configurable but is not the supported path.
  Rate limiting needs `TRUSTED_PROXY_HOPS=2` behind Vercel + Railway, otherwise
  every user would share the Vercel egress IP.
- **Cross-tab refresh race**: tabs share one cookie jar, and rotation burns
  the token on use; two tabs refreshing in the same instant would look like
  token theft and revoke every session. Refreshes are serialised across tabs
  with the Web Locks API (`navigator.locks`), plus in-tab deduplication.
- **Security headers**: frontend (`vercel.json`): CSP with `script-src 'self'`
  (no inline script; the Vite build emits none), `style-src 'self'` +
  Google Fonts (what `index.css` imports), `connect-src 'self'`,
  `object-src 'none'`, `base-uri`/`form-action 'self'`, `frame-ancestors 'none'`,
  `upgrade-insecure-requests`; plus nosniff, X-Frame-Options, Referrer-Policy,
  Permissions-Policy, COOP, HSTS. Backend (`SecurityHeadersMiddleware`, pure
  ASGI): nosniff, X-Frame-Options, `Referrer-Policy: no-referrer`, CORP,
  API CSP `default-src 'none'` (not on `/docs`/`/redoc`), `Cache-Control:
  no-store` on `/auth/*`, HSTS in production.

**Alternatives rejected**:
- *Keep localStorage + CSP only*: one XSS (or a compromised dependency) steals
  a 30-day refresh token; CSP reduces but does not remove the risk.
- *Both tokens in HttpOnly cookies*: then every API call is cookie-authenticated
  and needs CSRF protection everywhere; keeping Bearer for the API shrinks the
  CSRF surface to two endpoints.
- *Cross-site cookies with `SameSite=None`*: blocked or unreliable in Safari/Chrome.
- *Custom domain with a shared parent (`app.x.com` / `api.x.com`)*: also
  first-party, but needs a domain the owner does not have and `COOKIE_DOMAIN`
  widens the cookie to all subdomains.
- *Double-submit CSRF token*: see above.
- *In-memory refresh token / service-worker or BFF token handling*: loses the
  session on reload or adds a whole proxy tier; the cookie is simpler and safer.
- *Server-side grace window for rotated tokens* (to tolerate multi-tab races):
  weakens reuse detection; Web Locks solve it client-side.

**Consequences / trade-offs**: an XSS can still *use* the session while the
page is open (call the API with the in-memory access token or hit
`/auth/refresh`), it just cannot steal it for later; CSP is the line of defence
against that. Every page load for a signed-out visitor costs one 401 on
`/auth/refresh` (counted by the refresh rate limit). The Vercel rewrite adds a
proxy hop to every API call. Logout in one tab does not instantly sign out other
open tabs (their access token lives up to 60 min; they cannot refresh).


## AI layer: provider-agnostic `app/services/ai`, Claude first (I1)

**Decision**: one package owns every LLM interaction. Provider chosen by
`AI_PROVIDER=fake|claude` (default `fake`, so tests/dev/CI never need a key or
network). Claude (Anthropic API) is the first real provider, per the owner's
Track I decision D1; the key lives only in Railway variables.
- **Default model `claude-sonnet-5-5`**, overridable with `AI_MODEL`: current
  Sonnet, $2/$10 per MTok -- fits tutoring/grading volume. Sampling parameters
  (`temperature`) are only sent when a caller sets them because the newest
  models reject non-default values; thinking is left at the model default, so
  callers budget `max_tokens` accordingly.
- **Structured output** via `output_config.format` (JSON schema, adapted by
  `anthropic.transform_schema`) validated again with Pydantic, plus one repair
  retry (the repair prompt names failing fields, never echoes values).
- **`anthropic` is a runtime dependency, not an extra**: enabling Claude on
  Railway is then only an env-var change (no build-command edit). The import is
  still lazy and confined to `claude_provider.py`, so the app boots without it.
- **Measurement, not budget (owner D2)**: every provider call (also failures)
  writes `ai_usage` (no content). Cost is an *estimate* from a price table in
  code (`pricing.py`); billing console is authoritative. A per-user daily token
  ceiling exists but is **off by default** (`AI_DAILY_TOKEN_LIMIT=0`); when on,
  it raises `AIUsageLimitExceeded` so features degrade instead of breaking.
- **Language (owner D3)** is a parameter of every call (`en` default, `pt-BR`);
  the layer instructs the model to answer in it. It does not read the user's
  profile; features pass the user's preference in.
- **Production boot guard**: `ENVIRONMENT=production` + `AI_PROVIDER=claude`
  without `ANTHROPIC_API_KEY` fails at startup, like the other insecure-config
  checks.
- Usage rows are committed immediately by the layer so a later failure in the
  caller does not erase the record of a billed call.

## Streak measures consistency, XP measures effort (short sessions keep the streak)

**Context:** the streak was updated inside `award_xp`, which only runs when a
study session earns XP (>= 10 minutes). A 5-minute session, every day, never
built a streak even though the learner showed up daily.

**Decision (owner, option a):** decouple them. `gamification_service.record_activity`
updates the streak without awarding XP; `log_study_session` calls it when the
session earns 0 XP, then runs `settle_rewards` so quests/achievements still
advance. XP rules are unchanged.

**Rejected:** (b) keep as is -- the streak would silently require >= 10 minutes;
(c) minimum 1 XP per session -- pays for logging rather than effort and invites
farming with 1-minute sessions.

**Scope:** only study sessions. Failed challenge attempts and other zero-XP events
do not count for the streak (they are not "showing up to study"). No XP is ever
refunded (see the delete decision).
