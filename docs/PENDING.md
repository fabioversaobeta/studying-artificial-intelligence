# Pending Decisions

None of these block ongoing development — each has a current working
assumption. Revisit if/when the trigger condition is hit, or whenever the
project owner has an opinion.

---

## GitHub repository creation — RESOLVED (2026-08-15)

Owner confirmed: private repo, matching the directory name. Created and
pushed: https://github.com/fabioversaobeta/studying-artificial-intelligence
(`master` branch, tracking `origin/master`).

---

## Token revocation / logout

**Status**: RESOLVED (roadmap item C3). See "Refresh-token rotation and
revocation (Postgres denylist)" in `docs/DECISIONS.md`.
**Resolution**: tokens carry a `jti`; refresh tokens are rotated on every
`/auth/refresh` (reuse is rejected and revokes all of the user's sessions);
`POST /auth/logout` revokes the current access token and the refresh token
server-side via a Postgres `revoked_tokens` table (no Redis). Access tokens
now live 60 minutes instead of 24h.

---

## Token storage: residual risks (C5)

**Status**: RESOLVED in design; residual risks accepted. See "Tokens: in-memory
access token plus HttpOnly refresh cookie" in `docs/DECISIONS.md`.
- An XSS can still act as the user while the page is open (it can call the API
  with the in-memory access token or call `/auth/refresh`); it can no longer
  steal a token for later use. The CSP in `frontend/vercel.json` is the
  mitigation; Google Fonts (`fonts.googleapis.com`/`fonts.gstatic.com`) are the
  only third-party origins allowed. Self-hosting the font would let the CSP drop
  them (needs an npm font package; not done).
- Logging out in one tab does not sign out other open tabs immediately (no
  `BroadcastChannel` sync); their access token expires within 60 minutes and
  they cannot refresh.
- Browsers without the Web Locks API fall back to in-tab deduplication only, so
  two tabs reloading at the same instant could trigger reuse detection (all
  sessions revoked, log in again). All current browsers support Web Locks.
- Every load by a signed-out visitor makes one failing `/auth/refresh` call that
  counts against the per-IP refresh rate limit (10/min by default).
- A request carrying the CSRF header but neither `Origin` nor `Referer` is
  accepted (non-browser clients); a browser cannot send that cross-site.
- The Vercel rewrite has a placeholder Railway host in `frontend/vercel.json`
  that must be replaced at deploy time (deploy is deferred), and
  `CORS_ALLOW_ORIGINS` must contain the real frontend origin or `/auth/refresh`
  returns 403.

---

## Automated challenge grading

**Question**: should challenge submissions eventually be graded
automatically (code execution, LLM-based rubric scoring) instead of
self-assessed?
**Current assumption**: self-assessment stays as-is until there's a real
need; see `docs/DECISIONS.md`.
**Recommended direction**: an LLM-as-judge grader behind the same AI
abstraction layer planned for the AI Mentor (`docs/PRODUCT.md`), evaluated
with a golden-dataset regression suite before trusting it to award XP
automatically.

---

## AI Mentor / AI abstraction layer

**Status (I1 done, 2026-10-06)**: the foundation exists in
`backend/app/services/ai/` (provider `claude` or `fake`, guardrails, usage
measurement, `GET /ai/status`); see `docs/ARCHITECTURE.md` and the decision in
`docs/DECISIONS.md`. Owner decisions: Claude/Anthropic, no budget cap for now.
**Still open**:
- The owner must set `AI_PROVIDER=claude` and `ANTHROPIC_API_KEY` in Railway
  to enable the real provider; until then everything runs on the fake one.
  Not yet exercised against the real API (the suite is 100% mocked) -- do a
  smoke call via the first feature, then check `GET /ai/status` and `ai_usage`.
- Pick a real `AI_DAILY_TOKEN_LIMIT` once production usage is measured.
- Price table (`services/ai/pricing.py`) must be updated when models/prices change.
- No product feature uses the layer yet (mentor, grader I5, interview I4).
**Impact**: none on existing flows.

---

## Assessments / question bank

**Question**: the original domain brief lists `Assessment` and `Question`
as core entities (quizzes distinct from self-assessed challenges). Should
these be modeled now or deferred?
**Current assumption**: deferred. Not in the v1 schema. Challenges cover
the "prove you understand this" need for v1; a formal quiz/assessment
system with a question bank is a distinct, larger feature.
**Impact**: `docs/ROADMAP.md` tracks this as `NOT_STARTED`. Adding it later
is additive (new tables, new endpoints) — nothing in the current schema
needs to change to support it.

---

## Multi-user support

**Question**: the domain model already scopes everything by `user_id`, so
multiple users technically work today — but there's no invite flow, no
admin tooling, and the catalog (subjects/competencies) is global, not
per-user.
**Current assumption**: single-owner tool. Not a design goal to support
arbitrary signups at this stage.
**Impact**: registration is currently open (no invite code / admin
approval). Acceptable for a personal deployment not advertised publicly.

---

## Observability beyond health checks

**Question**: what request tracing / metrics / log aggregation should exist
once this is actually deployed to Railway?
**Current assumption**: structured logging + `/health` + `/health/ready`
is enough until there's a deployed environment generating real traffic to
observe. Revisit once `docs/DEPLOYMENT.md` steps have actually been run
against a live Railway project.
**Update (H2)**: implemented per-request `X-Request-ID`, access log,
`LOG_FORMAT=text|json` / `LOG_LEVEL`, and optional Sentry (`SENTRY_DSN`,
extra `[observability]`). Still pending, all dependent on a live deploy (H1):
validating Sentry against a real project, choosing a log aggregator, metrics
(Prometheus/latency histograms) and distributed tracing — deliberately not
built yet.

---

## Study sessions under 10 minutes earn no XP (and no streak)

**Question**: a study session shorter than 10 minutes earns 0 XP, so it never
calls `award_xp`; as a side effect it doesn't count for the streak and can't
trigger achievements. Is that intended?
**Current assumption**: unintended side effect, not a decision. Found by the
backend test pass (roadmap F3, 2026-10-06).
**Options**: (a) count any session for the streak even with 0 XP;
(b) keep as is and document it; (c) award a minimum of 1 XP.

---

## Accessibility follow-ups (roadmap G5, 2026-10-06)

Fixed in G5: skip link, labelled `nav`, `main` landmark, `role="alert"` on
`ErrorAlert`, visible `:focus-visible` outline, 3:1 form-control borders,
primary-button contrast (dark text on accent), `aria-expanded` on toggles,
progress-bar roles. Left open because they are design decisions:

- **Light theme / `prefers-color-scheme`**: only a dark theme exists. Offering
  a light one needs a second token set; not done.
- **Per-route document titles and focus move on navigation**: the SPA keeps a
  single `<title>` and does not move focus to the new page heading after a
  route change (WCAG 2.4.2 / best practice for SPAs). Needs a small
  route-announcer component; deferred.
- **Muted badge/text tones**: `fg-muted` on `surface-raised` is ~6:1 and passes,
  but the 15%-tint badge tones were checked only by estimate, not with a tool.
- **Automated a11y checks** (axe in Vitest/Playwright) are not wired up.
