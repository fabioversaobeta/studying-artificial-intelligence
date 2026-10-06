# Architecture

## Shape: modular monolith

One backend service, one database, one frontend app. Internally organized
around clear module boundaries (learning, gamification, auth) so those
boundaries *could* become service boundaries later — but there is currently
no reason to pay the operational cost of microservices for a single-owner
personal tool. See `docs/DECISIONS.md`.

```
                    ┌──────────────┐
                    │   Frontend   │  React + TS + Vite + Tailwind
                    │   (Vercel)   │
                    └──────┬───────┘
                           │ HTTPS / JSON
                    ┌──────▼───────┐
                    │   FastAPI    │  api -> services -> repositories -> models
                    │  (Railway)   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  PostgreSQL  │  (Railway)
                    └──────────────┘
```

## Backend layering

```
app/
  api/            HTTP layer: FastAPI routers, request/response wiring only.
  schemas/        Pydantic models: request/response shapes, validation.
  services/       Business logic / use cases. Orchestrates repositories and
                  domain logic. This is where transactions are committed.
  domain/         Pure functions, no I/O: leveling curve, mastery formula,
                  spaced-repetition algorithm, skill-tree state derivation.
                  Trivial to unit test in isolation (see tests/domain/).
  repositories/   Persistence: SQLAlchemy queries, one module per aggregate.
                  No business logic here — just data access.
  models/         SQLAlchemy ORM models (the schema).
  core/           Cross-cutting: config, security (JWT/hashing), exceptions.
  infrastructure/ Database engine/session setup.
  seeds/          Idempotent seed data (content.py) + runner (run.py).
tests/
  domain/         Pure unit tests, no database.
  test_*.py       Integration tests against a real Postgres test database.
```

**Dependency direction is one-way**: `api → services → repositories → models`,
and `services → domain`. Routers never import SQLAlchemy models directly;
services never import FastAPI; domain modules never import SQLAlchemy at
all. This is what "Clean Architecture" means in this codebase — not ports
and adapters for their own sake, but a rule that keeps business logic
testable without a database and keeps the ORM swappable in theory (even if
that's never actually exercised).

### Why sync SQLAlchemy, not async

FastAPI is async-native, but the ORM layer here is synchronous
(`sqlalchemy.orm.Session`, `psycopg` driver). Route handlers that touch the
database are declared `def`, not `async def` — FastAPI automatically runs
`def` handlers in a worker thread pool, so requests still don't block each
other. This trades a small amount of raw throughput (irrelevant at
single-user scale) for a codebase that's dramatically simpler to write,
read, and debug — no `async`/`await` threading through every repository and
service call, no async session lifecycle edge cases. See `docs/DECISIONS.md`
for the full reasoning and the migration path if it's ever needed.

### IDs, timestamps, enums

- **UUID primary keys** everywhere (not auto-increment integers) — IDs
  never leak row-count/sequence information through the API.
- **Timestamps** are `TIMESTAMPTZ`, always UTC.
- **Enums** are stored as `VARCHAR` with `native_enum=False` (a Postgres
  `CHECK` constraint via SQLAlchemy, not a native `CREATE TYPE`). Adding a
  new enum value is a trivial migration; a native Postgres enum would
  require `ALTER TYPE ... ADD VALUE`, which has its own transactional
  quirks.

## Frontend structure

```
frontend/src/
  app/          App shell, providers, router root.
  routes/       Route definitions / route-level components.
  pages/        Top-level page components (one per route).
  features/     Feature-scoped logic + components (auth, dashboard, learning...).
  components/   Shared, reusable presentational components.
  hooks/        Shared React hooks.
  services/     API client (typed fetch wrapper).
  lib/          Small framework-agnostic utilities.
  types/        Shared TypeScript types (mirrors backend schemas where useful).
  layouts/      Page layout shells (authenticated app shell, auth pages shell).
```

## Authentication

JWT-based: a short-lived access token (24h) and a longer-lived refresh
token (30 days), issued on register/login. Passwords are hashed with
Argon2 (via `argon2-cffi`), OWASP's current recommendation over bcrypt/PBKDF2
for new applications. The frontend stores tokens and attaches
`Authorization: Bearer <token>` to API requests; there is no server-side
session store — logout is client-side token discardal (see
`docs/PENDING.md` for token revocation, which is intentionally deferred).

## AI layer (`app/services/ai/`, roadmap I1)

Provider-agnostic foundation; no product feature uses it yet. Nothing outside
this package imports a provider SDK.

- `base.py` — narrow contract: `AIProvider.complete(AIRequest) -> AIResponse`
  (messages, system, `max_tokens`, optional `temperature`, optional Pydantic
  `output_schema`, `language`, `purpose`).
- `fake_provider.py` — deterministic (queue/rules/fixtures, or a minimal
  instance generated from the schema); default when `AI_PROVIDER=fake`.
- `claude_provider.py` — Anthropic SDK (lazy import, injectable client,
  SDK timeout/retries, structured output via `output_config.format`); maps SDK
  errors to `AIProviderError` / `AIRateLimited` / `AIUnavailable`.
- `service.py` — the facade features call (`get_ai_service(settings).complete(db, ...)`).
  Implements the guardrails once: system prompt built with an injection
  preamble and the response-language rule (`language` is a parameter, `en`
  default, `pt-BR` supported); `max_tokens` cap; schema validation with exactly
  one repair retry (`AIInvalidOutput` after that); usage row per provider call
  (`ai_usage`: tokens, latency, status, estimated cost, `request_id`); optional
  per-user daily token ceiling (`AIUsageLimitExceeded`); logs carry ids, sizes,
  latency, tokens and model, never prompt or response text.
- `prompts.py` — `delimit()` / `build_user_message()` fence user input as
  `<user_data name="...">` blocks (delimiter look-alikes neutralised). Callers
  must put user-controlled text only there, never in `system`.
- `pricing.py` — price table (data) for cost estimates; `status.py` backs
  `GET /ai/status`.

Model output is data: it is validated and never executed. All `AIError`s are
`AppError`s (429/502/503) so features can catch `AIError` and degrade.

## Cross-cutting concerns

- **Errors**: domain code raises typed exceptions (`app.core.exceptions`);
  a single FastAPI exception handler translates them to a consistent JSON
  shape (`{"error": {"code": ..., "message": ...}}`).
- **Config**: all runtime config comes from environment variables via
  `pydantic-settings` (`app.core.config.Settings`), loaded once and cached.
  Never hardcode a secret or environment-specific value.
- **Observability**: structured logging via the standard library `logging`
  module; `/health` (liveness) and `/health/ready` (DB connectivity) probes.
  Deeper tracing/metrics are deferred (`docs/PENDING.md`) until there's a
  deployed environment to observe.
