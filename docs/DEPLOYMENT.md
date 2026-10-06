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
| `CORS_ALLOW_ORIGINS` | `["https://<your-vercel-app>.vercel.app"]` | JSON array (or comma-separated list). `*` is rejected when `ENVIRONMENT=production`. **Also the allow-list for the CSRF `Origin`/`Referer` check on `/auth/refresh` and `/auth/logout`**, so it must contain the exact public origin of the frontend (including any custom domain) even though requests are same-origin through the Vercel rewrite. Update after the frontend's Vercel URL is known — see step 4 below. |
| `TRUST_PROXY_HEADERS` | `true` on Railway | Makes rate limiting use the `X-Forwarded-For` entry added by our own proxies. Leave `false` when not behind a trusted proxy (the header is spoofable). |
| `TRUSTED_PROXY_HOPS` | `2` | Proxies that append to `X-Forwarded-For`: Railway + the Vercel rewrite in front of it = 2. With the default `1` every user would share the Vercel egress IP as rate-limit key. |
| `COOKIE_SECURE` | forced `true` | Forced on when `ENVIRONMENT=production` (the refresh cookie is then named `__Secure-refresh_token`). |
| `COOKIE_SAMESITE` | `strict` (default) | Keep `strict` (or `lax`) with the same-origin rewrite. `none` only for a cross-site setup and requires `COOKIE_SECURE=true`; browsers may still block such cookies. |
| `COOKIE_DOMAIN` | *(unset)* | Leave unset: a host-only cookie is the tightest. |
| `RATE_LIMIT_ENABLED` / `RATE_LIMIT_MAX_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` | `true` / `10` / `60` (defaults) | In-memory limit on `/auth/login`, `/register`, `/refresh` (per IP; login also per e-mail); 429 when exceeded. Per process. |
| `REGISTRATION_ENABLED` | `true` (default) | Set `false` to close signups (403). |
| `REGISTRATION_INVITE_CODE` | *(unset)* | If set, `/auth/register` requires this code. Recommended for a public deploy. |
| `LOG_FORMAT` | `json` on Railway (default `text`) | `json` prints one JSON object per line (`timestamp`, `level`, `logger`, `message`, `request_id`) for log aggregators. |
| `LOG_LEVEL` | `INFO` (default) | Standard logging level. Every request is logged at INFO by the `app.access` logger (method, path, status, duration in ms). |
| `SENTRY_DSN` | *(unset)* | Optional. Needs the extra: `pip install ".[observability]"`. If set without the package installed the app logs a warning and runs without Sentry. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` (default) | Memory-only access token lifetime; the frontend refreshes transparently. |
| `AI_PROVIDER` | `fake` (default) / `claude` | `fake` is deterministic and needs no key. `claude` uses the Anthropic API. With `ENVIRONMENT=production` and `AI_PROVIDER=claude` the app **refuses to boot** without `ANTHROPIC_API_KEY`. |
| `ANTHROPIC_API_KEY` | *(unset)* | **Set only in the Railway variables** (never in the repo or a committed `.env`). Never logged or returned by the API; `GET /api/v1/ai/status` only says `configured: true/false`. |
| `AI_MODEL` | `claude-sonnet-5-5` (default) | Claude model id used by the AI layer. |
| `AI_TIMEOUT_SECONDS` / `AI_MAX_RETRIES` | `30` / `2` (defaults) | Per-call timeout and SDK retry count (429/5xx/connection). |
| `AI_MAX_OUTPUT_TOKENS` | `4096` (default) | Cap applied to every request's `max_tokens`. |
| `AI_DAILY_TOKEN_LIMIT` | `0` (default = off) | Optional per-user daily ceiling (input+output tokens, UTC day). Usage is always measured in `ai_usage`; set a positive number to start blocking (the feature degrades to "AI unavailable"). |
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

### 2. Same-origin API via a Vercel rewrite (required)

The refresh token is an `HttpOnly` cookie, which only works reliably when it
is **first-party**. Vercel (frontend) and Railway (backend) are different
sites, so a direct cross-site call would need `SameSite=None` cookies that
Safari (ITP) and Chrome's third-party-cookie phase-out block. Instead the
browser only ever talks to the Vercel origin, and Vercel proxies `/api/*`:

1. In `frontend/vercel.json`, replace the placeholder host
   `REPLACE-WITH-RAILWAY-BACKEND-HOST.up.railway.app` in the first rewrite
   (`/api/:path*`) with the real Railway host. The `/api/...` path is
   forwarded unchanged, so the cookie `Path=/api/v1/auth` matches.
2. **Do not set `VITE_API_URL`** (leave it unset/empty): the frontend then
   calls relative `/api/...` URLs. Setting it makes the browser call the
   backend directly and cross-site, defeating the design.
3. On Railway set `CORS_ALLOW_ORIGINS` to the Vercel origin (see above; it is
   needed for the CSRF origin check) and `TRUSTED_PROXY_HOPS=2`.

The same file sets the security headers for the frontend: a strict
`Content-Security-Policy` (scripts only from `'self'`, no inline script;
styles/fonts additionally allow Google Fonts, which `src/index.css` imports),
`X-Content-Type-Options`, `X-Frame-Options`/`frame-ancestors`,
`Referrer-Policy`, `Permissions-Policy`, `Cross-Origin-Opener-Policy` and HSTS.
If a new third-party origin is ever needed (analytics, fonts, images), it must
be added to the CSP deliberately. The rewrite proxies request/response bodies
(Vercel's proxy timeout applies; the API has no long-running calls).

Local development uses the same shape: Vite proxies `/api` to the backend
(`server.proxy` in `vite.config.ts`, target `http://127.0.0.1:8000`, override
with `API_PROXY_TARGET`), also for `npm run preview`.

> Status: configuration is ready and was tested locally (build + preview with
> the production headers + proxy); the real deployment is deferred.

### 3. Verify

Visit the deployed URL, register an account, and confirm the dashboard
loads with no console errors. In DevTools > Application > Cookies,
`__Secure-refresh_token` must be `HttpOnly`, `Secure`, `SameSite=Strict`,
`Path=/api/v1/auth`, and Local/Session Storage must hold no token. Reload the
page: you stay signed in (a `POST /api/v1/auth/refresh` restores the session).
If `/auth/refresh` answers 403, `CORS_ALLOW_ORIGINS` does not contain the
frontend origin.

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
