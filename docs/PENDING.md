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

**Question**: JWT access tokens are stateless and valid until they expire
(24h) — there's no server-side revocation list. Is that acceptable for a
personal tool?
**Current assumption**: yes. "Logout" is client-side (discard the tokens).
**Options if revisited**: a Redis-backed denylist of revoked token IDs
(`jti` claim), or shortening access-token lifetime further and relying on
refresh-token rotation.
**Impact of the current assumption**: a stolen access token remains valid
for up to 24h with no way to kill it server-side. Low risk for a
single-user tool behind HTTPS, not acceptable if this ever has real
multi-user stakes.

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

**Question**: which LLM provider(s) should the planned AI Mentor use, and
what should the provider-agnostic interface look like?
**Current assumption**: not started. When built, it must sit behind an
abstraction (`app.services.ai_service` or similar) so the rest of the
application never imports a provider SDK directly — see the original
brief's "AI Architecture" section.
**Impact**: none yet; no code depends on this.

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
