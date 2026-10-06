# Deployment

Target architecture: frontend on **Vercel**, backend + PostgreSQL on
**Railway**. Both platforms deploy from this Git repository.

## Backend — Railway

### 1. Create the project

1. In Railway, create a new project and add a **PostgreSQL** plugin — this
   provisions a database and injects a `DATABASE_URL` environment variable
   into every service in the project automatically.
2. Add a second service for the backend, pointing at this repository with
   **root directory `backend/`**.

### 2. Configuration Railway picks up automatically

- `backend/railway.toml` sets the start command:
  ```
  alembic upgrade head && python -m app.seeds.run && uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```
  Migrations run before the server starts on every deploy. Re-running seeds
  on every deploy is intentional and safe — `app.seeds.run` is idempotent
  (upserts by slug/code), so it keeps catalog content in sync with whatever
  is currently in `app/seeds/content.py` without ever duplicating rows.
- `backend/.python-version` pins the build to Python 3.12.
- Nixpacks installs dependencies from `backend/pyproject.toml`
  automatically (no `requirements.txt` needed).

### 3. Required environment variables

| Variable | Value | Notes |
|---|---|---|
| `DATABASE_URL` | *(auto-injected by the Postgres plugin)* | The app normalizes `postgres://`/`postgresql://` to the `postgresql+psycopg://` scheme it needs — see `app.core.config`. Don't edit this manually. |
| `SECRET_KEY` | a long random string | Generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"`. **Never reuse the local dev default.** With `ENVIRONMENT=production` the app refuses to boot if this is the dev default or shorter than 32 characters. |
| `ENVIRONMENT` | `production` | |
| `DEBUG` | `false` | Defaults to `false`; with `ENVIRONMENT=production` the app refuses to boot if `DEBUG=true`. |
| `CORS_ALLOW_ORIGINS` | `["https://<your-vercel-app>.vercel.app"]` | JSON array (or comma-separated list). `*` is rejected when `ENVIRONMENT=production`. Update after the frontend's Vercel URL is known — see step 4 below. |
| `TRUST_PROXY_HEADERS` | `true` on Railway | Makes rate limiting use the `X-Forwarded-For` entry added by Railway's proxy. Leave `false` when not behind a trusted proxy (the header is spoofable). |
| `RATE_LIMIT_ENABLED` / `RATE_LIMIT_MAX_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` | `true` / `10` / `60` (defaults) | In-memory limit on `/auth/login`, `/register`, `/refresh` (per IP; login also per e-mail); 429 when exceeded. Per process. |
| `REGISTRATION_ENABLED` | `true` (default) | Set `false` to close signups (403). |
| `REGISTRATION_INVITE_CODE` | *(unset)* | If set, `/auth/register` requires this code. Recommended for a public deploy. |
| `LOG_FORMAT` | `json` on Railway (default `text`) | `json` prints one JSON object per line (`timestamp`, `level`, `logger`, `message`, `request_id`) for log aggregators. |
| `LOG_LEVEL` | `INFO` (default) | Standard logging level. Every request is logged at INFO by the `app.access` logger (method, path, status, duration in ms). |
| `SENTRY_DSN` | *(unset)* | Optional. Needs the extra: `pip install ".[observability]"`. If set without the package installed the app logs a warning and runs without Sentry. |
| `AI_PROVIDER` | `fake` (default) / `claude` | `fake` is deterministic and needs no key. `claude` uses the Anthropic API. With `ENVIRONMENT=production` and `AI_PROVIDER=claude` the app **refuses to boot** without `ANTHROPIC_API_KEY`. |
| `ANTHROPIC_API_KEY` | *(unset)* | **Set only in the Railway variables** (never in the repo or a committed `.env`). Never logged or returned by the API; `GET /api/v1/ai/status` only says `configured: true/false`. |
| `AI_MODEL` | `claude-sonnet-5-5` (default) | Claude model id used by the AI layer. |
| `AI_TIMEOUT_SECONDS` / `AI_MAX_RETRIES` | `30` / `2` (defaults) | Per-call timeout and SDK retry count (429/5xx/connection). |
| `AI_MAX_OUTPUT_TOKENS` | `4096` (default) | Cap applied to every request's `max_tokens`. |
| `AI_DAILY_TOKEN_LIMIT` | `0` (default = off) | Optional per-user daily ceiling (input+output tokens, UTC day). Usage is always measured in `ai_usage`; set a positive number to start blocking (the feature degrades to "AI unavailable"). |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (default) | Override only if you want a different session length. |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | `43200` (default) | |

Full list with descriptions: `backend/.env.example`.

### 4. After the frontend is deployed

Update `CORS_ALLOW_ORIGINS` on the Railway backend service to include the
real Vercel URL, then redeploy. Until this is set correctly, the frontend
will be able to reach the API from a browser's perspective (CORS is
enforced by the browser, not a network boundary) but every request will be
rejected by the CORS preflight.

### 5. Verify

- `GET https://<railway-app>.up.railway.app/health` → `{"status": "ok"}`
- `GET https://<railway-app>.up.railway.app/health/ready` → confirms DB
  connectivity
- `GET https://<railway-app>.up.railway.app/docs` → interactive API docs
- After enabling Claude (`AI_PROVIDER=claude` + `ANTHROPIC_API_KEY`):
  `GET /api/v1/ai/status` (authenticated) should show `provider: "claude"`,
  `configured: true`. The `anthropic` package is a regular dependency, so no
  build-command change is needed.

## Frontend — Vercel

### 1. Import the project

Import this repository into Vercel with **root directory `frontend/`**.
`frontend/vercel.json` sets the build command (`npm run build`), output
directory (`dist`), and SPA rewrites (every path serves `index.html` so
React Router's client-side routing works on refresh/deep links).

### 2. Required environment variable

| Variable | Value |
|---|---|
| `VITE_API_URL` | `https://<railway-app>.up.railway.app` (no trailing slash) |

Set this in the Vercel project's Environment Variables settings before the
first deploy — Vite inlines `VITE_*` variables at build time, so changing
it later requires a redeploy, not just a restart.

### 3. Verify

Visit the deployed URL, register an account, and confirm the dashboard
loads with no console errors. If requests fail with a CORS error, revisit
backend step 4 above.

## Local production-build sanity check

Before deploying, confirm both sides actually build cleanly:

```bash
cd backend && ./.venv/Scripts/python.exe -m pytest && ./.venv/Scripts/python.exe -m mypy app
cd ../frontend && npm run build
```

## Rollback

Both Railway and Vercel keep prior deploys and support one-click rollback
to the previous successful deploy from their respective dashboards. There
is no destructive migration in this project's history yet (no dropped
columns/tables) — if one is ever added, note the rollback plan for that
specific migration in its `docs/DECISIONS.md` entry.
