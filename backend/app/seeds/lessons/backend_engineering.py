"""Lesson content for the Backend Engineering subject.

Module count per competency tracks real topic complexity — REST API design
gets two modules (implementation + testing), auth gets three (hashing,
tokens, authorization models), Postgres fundamentals gets three (indexing,
transactions, isolation levels), and event-driven architecture gets two
(delivery semantics, idempotent consumers). See
app.seeds.lessons.types.LessonModule.
"""

from app.seeds.lessons.types import LessonModule

LESSONS: dict[str, list[LessonModule]] = {
    "rest-api-design": [
        LessonModule(
            title="Building a paginated, filterable, sortable list endpoint",
            content=r"""
## The problem with "just add `?page=1`"

Every list endpoint eventually needs three things: pagination (don't return
10 million rows), filtering (let clients narrow the set), and sorting (let
clients order it). Bolting these on ad hoc produces an endpoint whose
behavior is undocumented and inconsistent with every other list endpoint in
the API. Treat this as a pattern to apply uniformly, not a one-off decision
per resource.

## Offset pagination — simple, and simply broken at scale

```
GET /api/challenges?limit=20&offset=40
```

```python
def list_challenges(limit: int = 20, offset: int = 0, db: Session = ...) -> list[Challenge]:
    return (
        db.query(Challenge)
        .order_by(Challenge.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
```

Offset pagination is easy to implement and lets clients jump to an
arbitrary page ("go to page 7"). It has two real problems:

1. **Cost grows with offset.** `OFFSET 100000` still makes Postgres scan and
   discard the first 100,000 matching rows before returning the next 20 —
   an index on the sort column helps the scan, but the discard work is
   still `O(offset)`. For deep pagination on a large table this gets slow.
2. **Pages shift under concurrent writes.** If a row is inserted or deleted
   between two page requests, offset-based pages drift — a row can be
   skipped entirely or shown twice. For a "top of feed" style listing where
   new rows show up constantly, this is a real, user-visible bug, not a
   theoretical one.

## Cursor pagination — stable, but no "jump to page 7"

```
GET /api/challenges?limit=20&cursor=eyJjcmVhdGVkX2F0IjoiMjAyNi0wOC0xMFQxMjowMDowMFoiLCJpZCI6ImFiYzEyMyJ9
```

The cursor encodes the last-seen row's sort key (and a tiebreaker, since
`created_at` alone isn't unique):

```python
import base64
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Cursor:
    created_at: datetime
    id: UUID

    def encode(self) -> str:
        payload = {"created_at": self.created_at.isoformat(), "id": str(self.id)}
        return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()

    @classmethod
    def decode(cls, raw: str) -> "Cursor":
        payload = json.loads(base64.urlsafe_b64decode(raw))
        return cls(created_at=datetime.fromisoformat(payload["created_at"]), id=UUID(payload["id"]))


def list_challenges(limit: int, cursor: str | None, db: Session) -> list[Challenge]:
    query = db.query(Challenge).order_by(Challenge.created_at.desc(), Challenge.id.desc())
    if cursor is not None:
        c = Cursor.decode(cursor)
        # Keyset predicate: strictly "before" the last row of the previous page,
        # using the tiebreaker column to stay stable when timestamps collide.
        query = query.filter(
            (Challenge.created_at < c.created_at)
            | ((Challenge.created_at == c.created_at) & (Challenge.id < c.id))
        )
    return query.limit(limit).all()
```

This is a **keyset** query: `WHERE (created_at, id) < (last_created_at,
last_id)` (Postgres even supports that as a literal row-comparison
expression). It uses the index on `(created_at, id)` to seek directly to
the right starting point regardless of how deep the page is — cost is
`O(limit)`, not `O(offset)`. It's also stable under concurrent inserts:
a new row inserted at the top never shifts what page 3 shows, because
"page 3" is defined relative to a row, not a numeric position.

The tradeoff: no random access ("show me page 7") and no total-page-count
UI without a separate `COUNT(*)` query (which is itself expensive on large
tables — consider making it optional or approximate).

**Rule of thumb**: offset pagination for small, mostly-static admin tables
where jump-to-page matters; cursor pagination for anything large,
high-write, or infinite-scroll-shaped.

## Filtering and sorting: keep the response envelope consistent

```python
from enum import StrEnum

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel


class ChallengeSort(StrEnum):
    CREATED_AT_DESC = "-created_at"
    CREATED_AT_ASC = "created_at"
    DIFFICULTY_DESC = "-difficulty"


class ChallengeListResponse(BaseModel):
    items: list[ChallengeOut]
    next_cursor: str | None
    has_more: bool


router = APIRouter()


@router.get("/challenges", response_model=ChallengeListResponse)
def list_challenges_endpoint(
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = None,
    subject_id: UUID | None = None,
    difficulty: DifficultyLevel | None = None,
    sort: ChallengeSort = ChallengeSort.CREATED_AT_DESC,
    service: ChallengeService = Depends(get_challenge_service),
) -> ChallengeListResponse:
    result = service.list_challenges(
        limit=limit, cursor=cursor, subject_id=subject_id, difficulty=difficulty, sort=sort
    )
    return ChallengeListResponse(
        items=result.items,
        next_cursor=result.next_cursor,
        has_more=result.next_cursor is not None,
    )
```

Three consistency rules worth enforcing across *every* list endpoint in the
API, not just this one:

- **A fixed envelope shape.** Every list response has `items` plus
  pagination metadata (`next_cursor`/`has_more`, or `total`/`page` for
  offset-based endpoints) — never sometimes a bare array and sometimes a
  wrapped object. A bare array can't grow a `next_cursor` field later
  without a breaking change.
- **A hard cap on `limit`** (`le=100` above). Without one, a client can
  request `limit=1000000` and turn a list endpoint into an accidental
  denial-of-service against your own database.
- **Enum-validated `sort` and filter values**, not raw strings passed
  straight into an `order_by()` — an unvalidated sort field is a direct
  path to letting a client reference (or inject into) an arbitrary column.

## Key takeaways

- Offset pagination (`LIMIT`/`OFFSET`) is simple and supports random page
  access, but degrades at depth (`O(offset)` scan cost) and drifts under
  concurrent writes.
- Cursor/keyset pagination (`WHERE (sort_col, id) < (last_val, last_id)`)
  is `O(limit)` and stable under writes, at the cost of no jump-to-page and
  no free total count.
- Always cap `limit` server-side; never trust a client-supplied page size.
- Validate `sort` and filter fields against an enum — never interpolate a
  client-supplied string into `order_by()` or a raw filter clause.
- Keep the response envelope (items + pagination metadata) identical in
  shape across every list endpoint in the API.
""",
        ),
        LessonModule(
            title="Testing API endpoints well",
            content=r"""
## "Returns 200" is not a test

A test that only checks the status code catches almost nothing. It won't
catch a response that returns the wrong shape, leaks an internal field,
paginates incorrectly, or silently drops a filter. Writing a genuinely
useful API test means asserting on the same three things a careful code
reviewer would check: **status code, response shape, and behavior at the
edges.**

## A weak test

```python
def test_list_challenges(client: TestClient) -> None:
    response = client.get("/api/challenges")
    assert response.status_code == 200
```

This passes even if the endpoint returns an empty list when it shouldn't,
leaks a `password_hash` field on a nested user object, or ignores every
query parameter. It gives false confidence.

## A test that actually asserts something

```python
def test_list_challenges_returns_expected_shape(
    client: TestClient, db_session: Session, seed_challenges: list[Challenge]
) -> None:
    response = client.get("/api/challenges", params={"limit": 2})

    assert response.status_code == 200
    body = response.json()

    # Shape: exact keys, not "contains some keys".
    assert set(body.keys()) == {"items", "next_cursor", "has_more"}
    assert len(body["items"]) == 2

    # Content: assert on actual field values, not just "a list exists".
    first = body["items"][0]
    assert set(first.keys()) == {"id", "title", "difficulty", "subject_id", "created_at"}
    assert first["difficulty"] in {"beginner", "intermediate", "advanced"}

    # Ordering: the default sort is newest first — verify it, don't assume it.
    timestamps = [item["created_at"] for item in body["items"]]
    assert timestamps == sorted(timestamps, reverse=True)

    # Pagination metadata is internally consistent.
    assert body["has_more"] is (body["next_cursor"] is not None)
```

This test would catch: a leaked internal field, wrong pagination-flag
logic, wrong default sort order, and a wrong page size — none of which
"status code 200" would ever notice.

## The edge cases that separate a real test suite from a rubber stamp

**Empty results.** Not "no results because the endpoint is broken" but "no
results because the filter legitimately matched nothing":

```python
def test_list_challenges_empty_filter_returns_empty_list_not_error(client: TestClient) -> None:
    response = client.get("/api/challenges", params={"subject_id": str(uuid4())})
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["has_more"] is False
    assert body["next_cursor"] is None
```

A surprising number of hand-rolled pagination implementations throw an
index-out-of-range error or return `next_cursor` pointing nowhere when the
result set is empty. This is the single most-skipped case in real codebases.

**The last page.** Fetch until `has_more` is `False`, then verify the
cursor stops advancing and no items repeat:

```python
def test_pagination_terminates_without_duplicates(client: TestClient, seed_25_challenges: None) -> None:
    seen_ids: set[str] = set()
    cursor = None
    for _ in range(10):  # bound the loop so a bug can't hang the test suite
        response = client.get("/api/challenges", params={"limit": 10, "cursor": cursor})
        body = response.json()
        page_ids = {item["id"] for item in body["items"]}
        assert seen_ids.isdisjoint(page_ids), "pagination returned a duplicate row"
        seen_ids |= page_ids
        if not body["has_more"]:
            break
        cursor = body["next_cursor"]
    else:
        pytest.fail("pagination did not terminate within 10 pages")

    assert len(seen_ids) == 25
```

**Invalid filters and out-of-range params.** A malformed UUID, a
`limit=0`, a `limit=100000`, a `sort` value that isn't in the enum — each
should produce a `422` with a body that names the offending field, not a
`500`:

```python
@pytest.mark.parametrize(
    "params",
    [
        {"subject_id": "not-a-uuid"},
        {"limit": 0},
        {"limit": 10_000},
        {"sort": "definitely_not_a_real_sort"},
    ],
)
def test_list_challenges_rejects_invalid_params(client: TestClient, params: dict) -> None:
    response = client.get("/api/challenges", params=params)
    assert response.status_code == 422
    assert "detail" in response.json()
```

**Authorization boundaries.** If the endpoint is scoped to the current
user or tenant, prove it — fetch as user A, assert user B's rows never
appear, not just "as user A, I get *a* 200":

```python
def test_list_goals_only_returns_current_users_goals(
    client: TestClient, user_a_token: str, user_b_goal: Goal
) -> None:
    response = client.get("/api/goals", headers={"Authorization": f"Bearer {user_a_token}"})
    returned_ids = {item["id"] for item in response.json()["items"]}
    assert str(user_b_goal.id) not in returned_ids
```

## Key takeaways

- Asserting only `status_code == 200` catches almost no real bugs —
  assert on the full response shape (exact key set, not "contains a key")
  and on specific field values.
- Test empty results as a legitimate, non-error case — it's the
  most commonly missed edge case in hand-rolled pagination.
- Test the last page explicitly: pagination should terminate, and
  consecutive pages should never return duplicate or skipped rows.
- Test invalid input (bad filter types, out-of-range `limit`, invalid enum
  values) and assert `422` with a field-identifying error body, not a
  crash.
- If an endpoint is scoped by user or tenant, write a test that proves
  data from a different user/tenant is absent — not just that the request
  the current user made succeeded.
""",
        ),
    ],
    "authentication-authorization": [
        LessonModule(
            title="Password hashing done right",
            content=r"""
## Why "just hash it" is not enough

Storing `SHA256(password)` in the database is a common mistake that looks
secure and isn't. `SHA256`, `SHA512`, and `MD5` are all **fast** hash
functions — designed for checksums and signatures, where speed is a
feature. For password storage, speed is a liability: an attacker who
steals your `users` table can compute billions of `SHA256` guesses per
second on commodity GPU hardware, making a full dictionary-plus-mutation
attack against every password in the table a matter of hours.

## What a password hashing algorithm needs to be

1. **Slow by design**, with a tunable cost factor you can increase as
   hardware gets faster.
2. **Memory-hard**, so the "just buy more GPUs" attack stops scaling —
   GPUs have abundant compute but comparatively little fast memory per
   core.
3. **Salted automatically**, so two users with the same password get
   different hashes, and so precomputed rainbow tables are useless.

`bcrypt` satisfies (1) and (3) but is not memory-hard, which is why
GPU/ASIC cracking farms are still meaningfully effective against it.
`Argon2id` (the OWASP-recommended default as of the current guidance) adds
memory-hardness on top, and it's what this project uses:

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_password_hasher = PasswordHasher()  # tuned defaults: time cost, memory cost, parallelism


def hash_password(plain_password: str) -> str:
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
```

(See `backend/app/core/security.py` in this codebase for the real
implementation.) Notice the salt is not managed manually anywhere — `hash()`
generates a fresh random salt and embeds it directly in the output string
alongside the algorithm parameters:

```
$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ$hash...
```

`verify()` reads the embedded salt and parameters back out of that string,
so there's no separate `salt` column to manage, and no risk of a
developer accidentally reusing one static salt for every row (a mistake
that defeats the entire purpose of salting).

## Timing attacks, and why `==` is dangerous here

```python
# WRONG — even though it's comparing hashes, not plaintext, this pattern
# is worth understanding because the same mistake is common elsewhere
# (API key comparison, HMAC signature checks).
def unsafe_compare(a: str, b: str) -> bool:
    return a == b
```

Python's `==` on strings short-circuits at the first differing byte.
That means comparing `"abc123"` against `"abd456"` takes microseconds
longer than comparing it against `"zzzzzz"` — a difference an attacker on
a low-latency network can statistically detect over enough requests, byte
by byte, to reconstruct a secret without ever brute-forcing it directly.
This is a **timing attack**, and it's why `hmac.compare_digest()` exists in
the standard library — it always takes the same time regardless of where
the mismatch occurs.

This specific vector doesn't apply to `argon2.verify()` — you're not
diffing two hashes with `==`, you're re-deriving one from user input and
letting the library do the comparison internally, safely. But it directly
applies to comparing API keys, webhook signatures, or session tokens
against a stored value:

```python
import hmac

def verify_api_key(provided: str, expected: str) -> bool:
    return hmac.compare_digest(provided, expected)  # constant-time
```

## Why you never roll your own crypto

Every piece of this — the KDF, the salt generation, the constant-time
comparison, the parameter tuning that balances security against your
server's actual CPU/memory budget — has been analyzed, attacked, and
hardened by cryptographers over years, and the standard libraries
(`argon2-cffi`, `hmac`) encode the result of that process. A bespoke
"secure enough" hashing scheme is not competing against nothing; it's
competing against decades of published cryptanalysis it hasn't been
subjected to. The realistic failure mode isn't "your custom scheme is
slightly weaker" — it's "your custom scheme has a category of flaw that a
known, audited algorithm eliminated years ago and you didn't know to look
for."

## Key takeaways

- Never store passwords with a fast general-purpose hash (`MD5`, `SHA256`,
  `SHA512`) — they're designed for speed, which is exactly wrong for
  password storage.
- Use a purpose-built, slow, memory-hard KDF: Argon2id (current OWASP
  recommendation) or bcrypt as a fallback where Argon2 isn't available.
- Salting should be automatic and per-password, handled by the library
  (embedded in the hash string) — never a single static salt shared across
  users.
- Use constant-time comparison (`hmac.compare_digest`) for any secret
  comparison that isn't already handled internally by a verify function —
  API keys, HMAC signatures, session tokens.
- Don't design your own hashing or comparison scheme — the failure modes
  are subtle, well-studied, and already solved by audited libraries.
""",
        ),
        LessonModule(
            title="Sessions vs JWTs",
            content=r"""
## Two different models of "who is this request from"

**Stateful sessions**: the server generates a random session ID, stores
the session data (user ID, roles, expiry) server-side (in Postgres, Redis,
etc.), and gives the client only the opaque ID — usually in a cookie. Every
request, the server looks the ID up.

**Stateless tokens (JWTs)**: the server encodes the session data directly
into a signed token and gives the *whole thing* to the client. Every
request, the server verifies the signature and reads the claims out of the
token itself — no database lookup required to know who's asking.

## The tradeoff that actually matters: revocation

The entire practical tradeoff comes down to one question: **can you
invalidate access before it naturally expires?**

With a session store, revocation is trivial — delete the row, and the very
next request fails. With a JWT, the token is self-contained and valid
until its `exp` claim says otherwise; the server has no record of it and
no way to "delete" it. Log a user out, suspect their token is
compromised, or ban them mid-session, and a plain JWT scheme keeps
honoring that token until it expires on its own.

The two standard workarounds each reintroduce some statefulness:

- **Short-lived access tokens.** Cap the blast radius by making access
  tokens expire in minutes, not days — a stolen token that can't be
  revoked at least can't be used for long.
- **A revocation list.** Maintain a small server-side set of denylisted
  token IDs (or user IDs with a "tokens issued before this timestamp are
  invalid" cutoff) that you check on top of signature verification. This
  brings back a lookup, but a much cheaper one than a full session store.

## The access + refresh token pattern

Because short-lived access tokens would otherwise force the user to
re-enter credentials every few minutes, pair them with a longer-lived
refresh token used only to mint new access tokens:

```python
class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


def create_access_token(user_id: UUID) -> str:
    return _create_token(user_id, TokenType.ACCESS, timedelta(minutes=15))


def create_refresh_token(user_id: UUID) -> str:
    return _create_token(user_id, TokenType.REFRESH, timedelta(days=30))
```

(This project's `backend/app/core/security.py` implements exactly this
shape.) The access token is sent on every API request and verified
statelessly. The refresh token is sent only to a dedicated `/auth/refresh`
endpoint, which validates it, checks it against a revocation store (refresh
tokens are long-lived enough that revocability matters), and issues a
fresh access token. This gets you most of a JWT's statelessness benefit on
the hot path (every regular API call) while keeping a meaningful
revocation point (the refresh endpoint) for the sensitive, long-lived
credential.

## Where should the token live client-side?

Two realistic options, each with a different attack surface:

**`localStorage` (or any JS-readable storage)**

- Vulnerable to **XSS**: any script that runs on your page — including one
  injected via a dependency, a reflected-XSS bug, or a compromised
  third-party widget — can read `localStorage` and exfiltrate the token
  directly. There is no browser-level protection against this once
  arbitrary JS is running in your origin.
- *Not* vulnerable to CSRF, because the browser doesn't attach
  `localStorage` contents to requests automatically — your JS has to
  explicitly read the token and set the `Authorization` header.

**An `httpOnly`, `Secure`, `SameSite` cookie**

- *Not* readable by JavaScript at all (`httpOnly`), so a garden-variety
  XSS payload can't directly steal it out of storage.
- Vulnerable to **CSRF** instead: the browser attaches cookies to requests
  automatically, including ones triggered by a malicious third-party page
  the user happens to have open. `SameSite=Lax` or `Strict` mitigates most
  of this by refusing to send the cookie on cross-site requests; a CSRF
  token on top closes the rest of the gap for the cases `SameSite` doesn't
  cover (e.g. top-level navigations under `Lax`).

**The honest summary**: neither storage location is free of risk — it's
XSS-exposure vs CSRF-exposure, not "secure vs insecure." In practice,
`httpOnly` cookies plus `SameSite=Strict`/`Lax` plus a CSRF token for
state-changing requests is the combination most production systems land
on, because a determined XSS attacker who can read arbitrary JS-accessible
storage can usually also just make authenticated requests directly from
the compromised page anyway — cookie storage at least removes the token
itself from that blast radius.

## Key takeaways

- Sessions are server-stateful and trivially revocable; JWTs are
  stateless and cannot be revoked without reintroducing some state
  (a denylist or short expiry).
- The access-token/refresh-token pattern trades most of a session's
  revocability for most of a JWT's statelessness: short-lived access
  tokens minimize exposure, a longer-lived refresh token stays revocable.
- `localStorage` tokens are exposed to XSS (script can read them
  directly); cookie-stored tokens are exposed to CSRF (browser attaches
  them automatically) but can be marked `httpOnly` to block direct
  JS access.
- `httpOnly` + `Secure` + `SameSite` cookies, plus CSRF tokens on
  state-changing requests, is the common production default — not because
  it's risk-free, but because it removes the token from the easiest attack
  surface (arbitrary JS reading storage).
""",
        ),
        LessonModule(
            title="RBAC vs ABAC",
            content=r"""
## Role-Based Access Control: permissions attached to a role

RBAC assigns each user one or more **roles**, and each role carries a
fixed set of permissions. Access checks ask "does this user's role allow
this action?"

```python
class Role(StrEnum):
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"


ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.MEMBER: {"goal:read", "goal:create"},
    Role.ADMIN: {"goal:read", "goal:create", "goal:delete", "user:invite"},
    Role.OWNER: {"goal:read", "goal:create", "goal:delete", "user:invite", "billing:manage"},
}


def require_permission(user: User, permission: str) -> None:
    if permission not in ROLE_PERMISSIONS[user.role]:
        raise PermissionDeniedError(permission)
```

RBAC is simple to reason about, simple to audit ("show me everyone with
the `admin` role"), and maps naturally onto organizational structures.
Its weakness is granularity: real authorization requirements are often
*contextual*, not just role-based — "an admin can delete goals **in their
own tenant**," "a member can edit **their own** goal but not someone
else's," "a manager can approve expenses **under $500**." A pure role
check (`role == "admin"`) can't express any of that; you end up bolting on
ad hoc `if goal.user_id != current_user.id` checks scattered through the
codebase, which is exactly the kind of unstructured, easy-to-miss
authorization logic that produces security bugs.

## Attribute-Based Access Control: permissions as a function of context

ABAC evaluates a policy against **attributes** of the user, the resource,
and the environment — not just a role label:

```python
@dataclass
class AccessContext:
    user_id: UUID
    user_role: Role
    tenant_id: UUID
    resource_owner_id: UUID
    resource_tenant_id: UUID


def can_delete_goal(ctx: AccessContext) -> bool:
    if ctx.tenant_id != ctx.resource_tenant_id:
        return False  # tenant isolation, checked first and unconditionally
    if ctx.user_role in (Role.ADMIN, Role.OWNER):
        return True  # admins can delete any goal in their own tenant
    return ctx.user_id == ctx.resource_owner_id  # members: only their own
```

This expresses rules that RBAC alone cannot: tenant isolation, resource
ownership, and role all combine into one decision. ABAC scales to
arbitrary policy complexity (time-of-day restrictions, IP allowlists,
data-classification-based rules) but costs more to reason about and audit
— "who can do X" is no longer a static table you can read off; it depends
on the specific resource and request.

## A worked example: permission checks in a multi-tenant system

Consider this platform's own shape: users belong to (in a hypothetical
multi-tenant extension) an organization, have a role within it, and act on
resources — goals, learning paths — that belong to a specific user within
that organization. A permission check that's actually safe needs to
compose **three separate questions**, checked in this order:

```python
class AuthorizationError(Exception):
    pass


def authorize_goal_delete(current_user: User, goal: Goal, db: Session) -> None:
    # 1. Tenant isolation — checked first, unconditionally, before role or
    #    ownership even enter the picture. A bug here is a cross-tenant data
    #    leak, the most severe class of authorization failure.
    if goal.tenant_id != current_user.tenant_id:
        raise AuthorizationError("Resource not found")  # 404, not 403 — don't
        # confirm cross-tenant resource existence to an unauthorized caller.

    # 2. Role-based grant — coarse, fast, auditable.
    if current_user.role in (Role.ADMIN, Role.OWNER):
        return  # admins/owners can act on any resource within their tenant

    # 3. Attribute-based fallback — ownership, for roles without a blanket grant.
    if goal.owner_id != current_user.id:
        raise AuthorizationError("You do not own this resource")
```

Note the ordering is not arbitrary. Tenant isolation is checked first and
unconditionally, because it is the one failure mode with no acceptable
partial credit — leaking *whether a resource exists* across a tenant
boundary is itself a data leak, which is why the error path returns a
generic "not found" instead of "you don't have permission" (revealing the
resource's existence to someone outside the tenant is itself information
disclosure). Role and ownership checks only run once tenant scoping is
already settled.

## Which one, when

Most real systems use both, layered: RBAC for the coarse, auditable "what
kind of user is this" grant (member/admin/owner), and a thin layer of
ABAC-style contextual checks (tenant match, ownership match) for the
things a role alone can't express. Pure RBAC is fine for systems with flat,
non-hierarchical, single-tenant resources. Reach for ABAC — or at minimum,
explicit attribute checks layered on top of RBAC — as soon as "can this
user act on this specific resource" depends on anything beyond the user's
role: ownership, tenant, resource state, or time.

## Key takeaways

- RBAC: permissions attached to a role, checked as `role in
  allowed_roles`. Simple, auditable, but coarse — can't express
  ownership or tenant-scoped rules on its own.
- ABAC: permissions computed from attributes of the user, resource, and
  context. Expressive enough for ownership and multi-tenancy, at the cost
  of being harder to audit as a static table.
- Most production systems layer both: RBAC for coarse role grants, ABAC-
  style checks (tenant match, ownership match) for the rest.
- In multi-tenant systems, check tenant isolation first, unconditionally,
  before any role or ownership logic — and fail closed with a generic
  "not found" rather than confirming a resource's existence across a
  tenant boundary.
""",
        ),
    ],
    "postgresql-fundamentals": [
        LessonModule(
            title="Indexing: B-trees, write cost, and reading EXPLAIN ANALYZE",
            content=r"""
## What a B-tree index actually is

Postgres's default index type is a B-tree: a balanced, sorted tree
structure that lets the database find a row matching an equality or range
condition in `O(log n)` comparisons instead of scanning every row
(`O(n)`, a sequential scan). Conceptually, it's the same reason a phone
book lets you find "Smith" without reading every page — the entries are
sorted, so you can binary-search.

```sql
CREATE INDEX idx_challenges_subject_id ON challenges (subject_id);
```

This index makes `WHERE subject_id = '...'` fast by letting Postgres seek
directly to matching rows instead of scanning the whole table. It also
speeds up range queries (`WHERE created_at > '2026-01-01'`), sorting
(`ORDER BY subject_id`), and some joins.

## Indexes are not free — the write-cost tradeoff

An index is a second data structure that must stay in sync with the
table. Every `INSERT`, `UPDATE` (of an indexed column), or `DELETE` has to
update every index on that table, not just the table's heap. A table with
five indexes pays that maintenance cost five times over on every write.
This is why "just index everything" is wrong advice:

- **Read-heavy, rarely-written tables** (e.g. a `subjects` reference
  table): index generously — the write cost is paid rarely, the read
  benefit is paid constantly.
- **Write-heavy tables** (e.g. an `events` or `audit_log` table taking
  thousands of inserts per second): every unnecessary index is a direct
  tax on insert throughput. Index only the columns actually driving `WHERE`
  /`JOIN`/`ORDER BY` clauses in real queries — not every column that
  *might* be queried someday.

Indexes also cost storage and cache space — a large index that doesn't
fit in shared memory has to be read from disk on lookup, eroding the
benefit it exists to provide.

## Composite index column order matters

A composite (multi-column) index is only efficiently searchable as a
*prefix match* — the leftmost columns first:

```sql
CREATE INDEX idx_attempts_user_challenge ON attempts (user_id, challenge_id);
```

This index efficiently serves:

- `WHERE user_id = ?` (uses the leading column alone)
- `WHERE user_id = ? AND challenge_id = ?` (uses both, in order)

It does **not** efficiently serve:

- `WHERE challenge_id = ?` alone — the index is sorted by `user_id`
  first, so without a `user_id` predicate, Postgres can't use the tree
  structure to narrow the search and typically falls back to a sequential
  scan (or a much less selective index scan).

Rule of thumb: order composite index columns by **equality columns before
range columns**, and put the column with the query patterns that need it
standalone first. If you query both `WHERE user_id = ?` alone and `WHERE
user_id = ? AND challenge_id = ?` together, `(user_id, challenge_id)` in
that order serves both. If you also frequently query `challenge_id` alone,
you likely need a second, separate index — a composite index cannot serve
as an efficient substitute for an index on its non-leading column.

## Reading EXPLAIN ANALYZE

```sql
EXPLAIN ANALYZE
SELECT * FROM attempts WHERE user_id = '11111111-1111-1111-1111-111111111111';
```

```
Index Scan using idx_attempts_user_challenge on attempts
  (cost=0.42..8.44 rows=3 width=64) (actual time=0.031..0.034 rows=3 loops=1)
  Index Cond: (user_id = '11111111-1111-1111-1111-111111111111'::uuid)
Planning Time: 0.112 ms
Execution Time: 0.058 ms
```

vs. the same query on an unindexed column:

```
Seq Scan on attempts (cost=0.00..2140.00 rows=3 width=64)
                      (actual time=0.021..18.442 rows=3 loops=1)
  Filter: (user_id = '11111111-1111-1111-1111-111111111111'::uuid)
  Rows Removed by Filter: 149997
Execution Time: 18.501 ms
```

What to look at, in priority order:

1. **`Seq Scan` vs `Index Scan`/`Index Only Scan`** on a large table for a
   selective predicate is the single biggest signal — a sequential scan
   means Postgres is reading every row and discarding most of them (note
   `Rows Removed by Filter: 149997` above).
2. **`cost=X..Y`** is the planner's own *estimate*, in arbitrary units, not
   real time — useful for comparing plan alternatives, not for absolute
   timing.
3. **`actual time=X..Y`** (only present with `ANALYZE`, which actually runs
   the query) is real elapsed time in milliseconds — this is what you
   actually care about when diagnosing a slow query.
4. **`rows=N` (estimated) vs `actual ... rows=M`** — a large gap between
   estimated and actual row counts means the planner's statistics are
   stale (`ANALYZE table_name` refreshes them) and it may be choosing a
   bad plan based on wrong assumptions.

A sequential scan is not automatically bad — for a small table, or a
query that legitimately needs most of the table's rows, Postgres often
correctly *prefers* a sequential scan over an index scan, because random
I/O per indexed row lookup can cost more than one linear pass. The signal
to act on is a sequential scan on a **large** table for a **selective**
predicate (few matching rows out of many) that keeps showing up in slow
query logs.

## Key takeaways

- B-tree indexes turn `O(n)` scans into `O(log n)` lookups for equality
  and range predicates, at the cost of extra work on every write.
- Don't index every column — weigh the read benefit against the write
  cost, especially on high-throughput tables.
- Composite indexes only serve queries that filter on a **prefix** of
  their columns, left to right; order columns by what your actual query
  patterns need.
- In `EXPLAIN ANALYZE`, look for `Seq Scan` on large tables with selective
  filters, and compare estimated vs. actual row counts to catch stale
  statistics.
- A sequential scan isn't inherently wrong — it's often correct for small
  tables or unselective queries; judge it against table size and
  selectivity, not by presence alone.
""",
        ),
        LessonModule(
            title="Transactions and ACID in practice",
            content=r"""
## The four guarantees, concretely

**Atomicity** — a transaction's writes either all commit or all roll back;
there is no partial-application state visible to other transactions.

```sql
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 'a';
UPDATE accounts SET balance = balance + 100 WHERE id = 'b';
COMMIT;
```

If the process crashes between the two `UPDATE`s, Postgres guarantees that
on recovery, *neither* update is visible — not "the first one stuck." This
is what makes a multi-step operation like a fund transfer safe to express
as ordinary sequential statements instead of needing manual compensation
logic for every failure point.

**Consistency** — the database moves from one valid state to another,
where "valid" is defined by your constraints (foreign keys, `CHECK`
constraints, `UNIQUE` constraints, triggers). Consistency is really a
consequence of atomicity plus your own schema constraints, not an
independent mechanism — Postgres doesn't know your business rules, only
the constraints you've declared.

**Isolation** — concurrent transactions don't see each other's uncommitted
intermediate state. How *much* isolation is configurable (next module) —
this is the guarantee with the most nuance and the most room for subtle
bugs.

**Durability** — once a transaction commits, it survives a crash. Postgres
achieves this via write-ahead logging (WAL): changes are flushed to a
durable log before the commit is acknowledged to the client, so a crash
immediately after commit can still replay the WAL on restart and recover
the change.

## The most common real-world mistake: long transactions holding locks

```python
# WRONG — holds a row lock for as long as the external HTTP call takes,
# which could be milliseconds or could be many seconds under load or a
# flaky network.
def redeem_reward(db: Session, user_id: UUID, reward_id: UUID) -> None:
    with db.begin():
        user = db.query(User).filter(User.id == user_id).with_for_update().one()
        user.points -= 100
        db.flush()
        send_fulfillment_request(reward_id)  # external HTTP call, INSIDE the transaction
        db.commit()
```

`with_for_update()` takes a row lock on `user`'s row that is held for the
*entire* transaction — including the external HTTP call. Every other
transaction that needs to touch that same user row (another request from
the same user, a background job updating their XP) blocks until this one
finishes or times out. If the fulfillment service is slow or hangs, you've
turned an external dependency's latency directly into your own database's
lock contention — a classic way for a slow third-party call to cascade
into a full outage of unrelated functionality.

```python
# BETTER — do the external call outside the transaction; keep the DB
# transaction narrowly scoped to just the DB writes it actually needs.
def redeem_reward(db: Session, user_id: UUID, reward_id: UUID) -> None:
    with db.begin():
        user = db.query(User).filter(User.id == user_id).with_for_update().one()
        if user.points < 100:
            raise InsufficientPointsError()
        user.points -= 100
        db.commit()

    # If this fails, points have already been deducted — that gap needs an
    # explicit compensation path (a retry queue, a reconciliation job, or
    # an outbox — see the event-driven-architecture competency), but at
    # least it no longer holds a DB lock while it's happening.
    send_fulfillment_request(reward_id)
```

The general rule: **a database transaction should span only the
statements that need atomicity with each other, and nothing that involves
unbounded external latency** — network calls, `sleep()`s, waiting on a
queue, or anything else outside the database's own control.

## A second common mistake: transactions left open by application logic

```python
# WRONG — if get_user_preferences() raises or the caller forgets to
# close/commit, this transaction (and its locks, and its snapshot) stays
# open for the life of the request or worse, the life of the connection
# if it's pooled and reused without a rollback.
def handle_request(db: Session) -> None:
    db.begin()
    user = get_user(db, user_id)
    prefs = get_user_preferences(db, user_id)  # if this raises, db.begin() is never closed
    render(user, prefs)
    db.commit()
```

Use a context manager (`with db.begin():`) or a framework-level
per-request session lifecycle (as this project's FastAPI dependency
injection does via `Depends(get_db)`) so a transaction is *always* closed
— committed or rolled back — even on an exception, never left dangling.
An open transaction holds back Postgres's autovacuum from cleaning up dead
row versions the transaction might still need to see, which over time
bloats tables and indexes across the *entire* database, not just the
table the stuck transaction touched.

## Key takeaways

- Atomicity guarantees all-or-nothing; consistency is atomicity plus your
  own declared constraints; isolation controls what concurrent
  transactions can see of each other; durability survives a crash via
  write-ahead logging.
- Keep transactions narrowly scoped to statements that actually need
  atomicity together — never hold a transaction open across an external
  network call or other unbounded-latency operation.
- Always close transactions deterministically (context managers, a
  framework-managed session lifecycle) so an exception can't leave one
  open indefinitely.
- A long-held or leaked-open transaction doesn't just block other
  transactions on the same rows — it can stall autovacuum and cause
  table/index bloat database-wide.
""",
        ),
        LessonModule(
            title="Isolation levels and the lost-update race condition",
            content=r"""
## Why isolation levels exist

Full serial execution of every transaction — one at a time, no
overlap — would trivially avoid every concurrency bug, but it would also
make the database useless under any real load. Isolation levels are the
tradeoff dial between correctness guarantees and concurrency: stricter
levels prevent more anomalies but allow less overlap (and can force more
transactions to abort and retry).

Postgres supports four SQL-standard levels, though it implements `READ
UNCOMMITTED` identically to `READ COMMITTED` (Postgres never does dirty
reads regardless of what you ask for). The two that matter in practice:

- **READ COMMITTED** (Postgres's default) — each *statement* within a
  transaction sees a fresh snapshot of committed data as of when that
  statement started. Two `SELECT`s in the same transaction can see
  different data if another transaction committed in between.
- **REPEATABLE READ** — the entire transaction sees one snapshot, taken
  at the transaction's start. Every `SELECT` within it sees the same data,
  no matter what else commits concurrently.
- **SERIALIZABLE** — behaves as if transactions ran one at a time in some
  serial order, even though they actually run concurrently; Postgres
  detects when true serial execution couldn't have produced the observed
  result and aborts one of the conflicting transactions with a
  serialization error for the application to retry.

## The lost-update race, concretely, under READ COMMITTED

Consider two concurrent requests both incrementing a user's XP after
completing a challenge:

```sql
-- Transaction A                          -- Transaction B
BEGIN;                                    BEGIN;
SELECT xp FROM users WHERE id = 'u1';     SELECT xp FROM users WHERE id = 'u1';
-- reads xp = 100                         -- reads xp = 100 (A hasn't committed yet)

UPDATE users SET xp = 100 + 10            UPDATE users SET xp = 100 + 15
  WHERE id = 'u1';                          WHERE id = 'u1';
COMMIT;                                   -- blocks here (row lock held by A)...
-- xp is now 110                          -- ...then proceeds once A commits
                                           COMMIT;
                                           -- xp is now 115 — A's +10 is LOST
```

Both transactions read `xp = 100` before either wrote anything. Each
computed its new value from that stale read, and the second `COMMIT`
silently overwrites the first transaction's result — the +10 XP from
Transaction A vanishes with no error, no conflict, no warning. This is the
**lost update** anomaly, and `READ COMMITTED` explicitly permits it: each
individual statement is consistent with *some* committed snapshot, but the
transaction as a whole made a decision based on data that was stale by the
time it wrote.

This is exactly the scenario this platform seeds as a challenge — it's a
core "senior engineer" interview topic because it looks fine in code
review (`SELECT`, compute, `UPDATE` — nothing looks wrong) and only
manifests under real concurrent load, which is precisely the kind of bug
that's expensive to diagnose in production and cheap to prevent at design
time.

## Fix 1: SELECT FOR UPDATE — pessimistic locking

```sql
-- Transaction A                          -- Transaction B
BEGIN;                                    BEGIN;
SELECT xp FROM users WHERE id = 'u1'      SELECT xp FROM users WHERE id = 'u1'
  FOR UPDATE;                               FOR UPDATE;
-- reads xp = 100, takes a row lock       -- BLOCKS here waiting for A's lock

UPDATE users SET xp = 100 + 10            -- (still blocked)
  WHERE id = 'u1';
COMMIT;  -- releases the lock             -- unblocks, re-reads xp = 110 (fresh!)
                                           UPDATE users SET xp = 110 + 15
                                             WHERE id = 'u1';
                                           COMMIT;
                                           -- xp is now 125 — correct, nothing lost
```

`FOR UPDATE` takes an exclusive row lock at `SELECT` time, forcing
Transaction B to wait until A commits and releases it — at which point B's
`SELECT ... FOR UPDATE` re-executes against the now-current row and sees
110, not the stale 100. This serializes access to that specific row
without affecting any other row in the table, which is why it's the usual
fix for hot single-row counters: cheap, precise, and it only blocks
transactions actually contending for the *same* row.

Equivalently in application code:

```python
def award_xp(db: Session, user_id: UUID, amount: int) -> None:
    with db.begin():
        user = db.query(User).filter(User.id == user_id).with_for_update().one()
        user.xp += amount
        db.commit()
```

## Fix 2: SERIALIZABLE — optimistic, detect-and-retry

```sql
-- Both transactions:
BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT xp FROM users WHERE id = 'u1';   -- both read xp = 100
UPDATE users SET xp = xp + 10 ...;      -- (or +15 for B)
COMMIT;
-- Whichever commits SECOND gets:
-- ERROR: could not serialize access due to concurrent update
```

Under `SERIALIZABLE`, Postgres doesn't block at read time — both
transactions proceed freely — but it tracks read/write dependencies and,
at commit time, detects that no serial (one-at-a-time) ordering of these
two transactions could have produced this result. It aborts one with a
serialization failure, and the application is expected to retry it:

```python
def award_xp_serializable(db: Session, user_id: UUID, amount: int) -> None:
    for attempt in range(3):
        try:
            with db.begin():
                db.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
                user = db.query(User).filter(User.id == user_id).one()
                user.xp += amount
                db.commit()
            return
        except SerializationFailure:
            if attempt == 2:
                raise
            continue  # retry with a fresh transaction and a fresh read
```

## Which fix, when

`SELECT FOR UPDATE` is the more common choice for hot, frequently
contended single rows (counters, balances) — it's cheaper under high
contention because it queues waiters instead of letting them all proceed
and then aborting most of them. `SERIALIZABLE` is a better fit when the
conflicting operation touches multiple rows/tables in a pattern too
complex to express as "lock this one row first," or when contention is
low enough that optimistic retry rarely actually fires. Both are strictly
better than leaving the default `READ COMMITTED` in place for an
operation with a genuine read-modify-write dependency — the fix isn't
optional at that point, it's a correctness bug waiting for enough
concurrent load to trigger it.

## Key takeaways

- `READ COMMITTED` (Postgres's default) allows the lost-update anomaly:
  two transactions can each read the same stale value, compute
  independently, and the second commit silently discards the first's
  result.
- `SELECT ... FOR UPDATE` fixes it pessimistically: it locks the row at
  read time, forcing concurrent readers to wait and re-read the fresh
  value before writing.
- `SERIALIZABLE` fixes it optimistically: transactions proceed
  concurrently, but Postgres detects a would-be anomaly at commit time and
  aborts one transaction with a serialization error for the app to retry.
- Any read-modify-write sequence on shared state (counters, balances, XP,
  inventory) needs one of these two fixes under concurrent load — this
  isn't a theoretical concern, it reproduces reliably with two overlapping
  transactions.
""",
        ),
    ],
    "event-driven-architecture": [
        LessonModule(
            title="Message queues, pub/sub, and delivery guarantees",
            content=r"""
## Two shapes of asynchronous messaging

**Point-to-point (queue)**: a message is delivered to exactly one
consumer among a pool of competing consumers — the classic work-queue
pattern (e.g. Amazon SQS, or RabbitMQ with a single queue and multiple
workers). Good for distributing a stream of independent jobs across
workers.

**Publish/subscribe (topic)**: a message is delivered to *every*
subscriber interested in that topic — each subscriber gets its own copy
(e.g. Kafka topics with multiple consumer groups, RabbitMQ exchanges
fanning out to multiple queues, SNS fanning out to multiple SQS queues).
Good for broadcasting an event ("user signed up") to several independent
systems (send a welcome email, update analytics, provision a workspace)
that shouldn't have to coordinate with each other.

Real systems usually combine both: a pub/sub layer fans an event out to
one queue per interested subsystem, and within each subsystem a pool of
workers competes to process that subsystem's queue.

## Delivery guarantees: three options, one of which is mostly fiction

**At-most-once**: a message is delivered zero or one times — if anything
goes wrong (network failure, consumer crash) between "sent" and
"processed," it's simply lost. Nobody deliberately designs for this; it's
what you get from "fire and forget" (e.g. a `UDP`-like send with no
acknowledgment, or acking a message *before* processing it and then
crashing).

**At-least-once**: a message is delivered one or more times — the broker
keeps redelivering until it receives an explicit acknowledgment, so a
crash between "delivered" and "acked" causes a redelivery. This is what
essentially every production message broker (SQS, RabbitMQ, Kafka with
manual offset commits) actually guarantees, and it's the only one of the
three that's achievable without also constraining what the consumer does.

**Exactly-once**: each message is processed *effectively* once, with no
duplicates and no losses. Here's the part worth being precise about:
**true exactly-once delivery, at the transport/network level, is not
achievable in a distributed system with unreliable networks** — this is a
direct consequence of the fact that a sender can never distinguish "my
acknowledgment was lost" from "the message was never received," so it
must always choose between risking a duplicate (retry) or risking a loss
(don't retry). What some systems (Kafka's idempotent producer + transactional
consumer, for instance) actually deliver is **at-least-once delivery
combined with deduplication or idempotency**, which *looks* like
exactly-once from the outside. The guarantee lives at the processing
layer, not the transport layer.

```
                    ┌─────────────────────────────────────────┐
                    │  "Exactly-once" as marketed              │
                    │  = at-least-once delivery (transport)     │
                    │  + idempotent processing (application)    │
                    └─────────────────────────────────────────┘
```

This reframing matters practically: it tells you where to put the
engineering effort. You cannot make the network perfectly reliable — but
you *can* make your consumer idempotent, and that's the tractable half of
the problem. The next module covers exactly that pattern.

## What "at-least-once" means for your consumer code, concretely

If your broker guarantees at-least-once delivery, every consumer **will**
occasionally see the same message twice — not as a rare edge case, but as
an expected, routine occurrence (consumer crashes after processing but
before acking; network blip causes a redelivered message; a broker-side
timeout redelivers a message that was actually still being processed). A
consumer that isn't written to tolerate this will eventually double-charge
a card, double-send an email, or double-award XP in production. The fix
isn't trying to make delivery "more exactly-once" — it's designing the
consumer so that processing the same message twice is safe.

## Key takeaways

- Point-to-point queues distribute messages across competing consumers;
  pub/sub topics broadcast each message to every subscriber. Most real
  systems combine both.
- At-most-once (silently drop on failure), at-least-once (redeliver until
  acked, possibly duplicating), and exactly-once are the three delivery
  models — only the first two are achievable at the transport level.
- "Exactly-once" as marketed by real systems is almost always
  **at-least-once delivery plus idempotent or deduplicated processing** —
  the guarantee is enforced at the application layer, not the network.
- Because duplicate delivery under at-least-once is routine, not rare,
  consumers must be written to handle redelivery safely as a normal case
  — see the idempotent-consumer pattern in the next module.
""",
        ),
        LessonModule(
            title="Designing an idempotent consumer, and the outbox pattern",
            content=r"""
## The problem, concretely: "charge card" processed twice

Say a `charge.requested` event triggers a payment consumer:

```python
# WRONG — not idempotent. If this message is redelivered (consumer
# crashed after charging but before acking, or the broker times out an
# in-flight message and redelivers it), the customer is charged twice.
def handle_charge_requested(event: ChargeRequestedEvent) -> None:
    payment_gateway.charge(
        customer_id=event.customer_id,
        amount=event.amount,
    )
```

At-least-once delivery guarantees this handler *will* run more than once
for some fraction of messages over time. The fix is making the handler
safe to run twice — an **idempotent consumer**: processing the same
logical operation more than once produces the same end state as
processing it once, with no duplicate side effects.

## Pattern: a deduplication table keyed by message ID

Every inbound event needs a stable, unique identifier — either one the
producer assigns (a UUID generated once, at creation time, that survives
retries) or a natural key derived from the operation itself (e.g.
`f"{order_id}:charge"` — the same order should never be charged twice
regardless of how many times the event is redelivered).

```sql
CREATE TABLE processed_messages (
    message_id UUID PRIMARY KEY,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

```python
def handle_charge_requested(db: Session, event: ChargeRequestedEvent) -> None:
    with db.begin():
        # INSERT with a PK conflict is the idempotency check itself —
        # atomic, and race-safe under concurrent redelivery of the same
        # message (two workers processing the same redelivered message
        # at once can't both win this insert).
        result = db.execute(
            text(
                "INSERT INTO processed_messages (message_id) "
                "VALUES (:id) ON CONFLICT (message_id) DO NOTHING"
            ),
            {"id": str(event.message_id)},
        )
        if result.rowcount == 0:
            # already processed — this is a duplicate delivery, not an error
            return

        payment_gateway.charge(customer_id=event.customer_id, amount=event.amount)
        db.commit()
```

Two details that make this actually correct, not just apparently correct:

1. **The `INSERT ... ON CONFLICT DO NOTHING` must happen inside the same
   transaction as the side effect it's guarding**, or at least be checked
   *before* an irreversible external call. If you mark the message as
   processed *after* calling `payment_gateway.charge()`, a crash between
   the charge and the marking reopens the exact race you're trying to
   close — the message gets redelivered, sees no dedup record, and
   charges again.
2. **The dedup check must be atomic against concurrent workers**, not just
   sequential redeliveries. Two worker processes picking up the same
   redelivered message at nearly the same time must not both pass the
   check — a unique constraint with `ON CONFLICT` handles this correctly
   because the database enforces it; an application-level "check if it
   exists, then insert" (two separate statements) has a race window
   between the check and the insert.

For an external call like `payment_gateway.charge()` that can't itself be
rolled back by a DB transaction abort, pass an **idempotency key** to the
gateway if it supports one (Stripe, for example, accepts an
`Idempotency-Key` header) — that pushes the same guarantee one layer
further out, so even a retry of the *charge call itself* (not just the
message) is deduplicated by the payment provider.

## The other half of the problem: reliably publishing events

Idempotent consumption solves duplicate processing. There's a symmetric
problem on the *producing* side: how do you guarantee an event is
published if and only if the database transaction that triggered it
actually committed?

```python
# WRONG — classic dual-write problem. If the process crashes (or the
# broker call fails) between the commit and the publish, the DB says the
# order was placed but no downstream system ever hears about it. If the
# broker call happens BEFORE commit and the transaction then rolls back,
# downstream systems hear about an order that doesn't exist.
def place_order(db: Session, order: Order) -> None:
    with db.begin():
        db.add(order)
        db.commit()
    message_broker.publish("order.placed", order.to_event())  # not atomic with the commit above
```

## Pattern: the transactional outbox

Write the event to an `outbox` table **in the same database transaction**
as the business data it describes — so the event's existence is atomic
with the change that produced it, using nothing more exotic than the
regular ACID guarantees already covered in the Postgres fundamentals
competency. A separate relay process then reads unpublished outbox rows
and publishes them to the real message broker, retrying until it
succeeds.

```sql
CREATE TABLE outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ
);
```

```python
def place_order(db: Session, order: Order) -> None:
    with db.begin():
        db.add(order)
        db.flush()  # order.id is now populated
        db.add(
            OutboxEvent(
                topic="order.placed",
                payload=order.to_event_payload(),
            )
        )
        db.commit()  # order row and outbox row commit together, or not at all


def relay_outbox_events(db: Session, broker: MessageBroker) -> None:
    # Runs continuously (polling loop, or driven off Postgres logical
    # replication / a CDC tool like Debezium for lower latency).
    unpublished = (
        db.query(OutboxEvent).filter(OutboxEvent.published_at.is_(None)).limit(100).all()
    )
    for event in unpublished:
        broker.publish(event.topic, event.payload)  # idempotent producer send
        event.published_at = datetime.now(UTC)
        db.commit()
```

If the relay crashes after publishing but before recording
`published_at`, the event gets published again on the next pass — which
is exactly the at-least-once delivery this whole module assumes
downstream consumers are already built to tolerate. The outbox pattern
doesn't eliminate duplicates; it eliminates *lost* events, and pushes the
duplicate-handling responsibility to the one place (the consumer) that's
already required to handle it.

## Key takeaways

- At-least-once delivery makes duplicate message processing routine, not
  exceptional — consumers must be written to be idempotent, not "mostly
  reliable."
- A dedup table keyed by a stable message ID (or a natural idempotency
  key derived from the operation), checked atomically via `INSERT ...
  ON CONFLICT` inside the same transaction as the side effect, is the
  standard pattern.
- Mark-as-processed must happen atomically with (or strictly before) the
  irreversible side effect it guards — marking it after an external call
  reopens the race the pattern exists to close.
- The transactional outbox pattern solves the symmetric producer-side
  problem: writing the event to an outbox table in the same DB
  transaction as the business change guarantees the event is never lost
  relative to that change, at the cost of a separate relay process and
  possible duplicate publishes — which idempotent consumers already
  handle.
""",
        ),
    ],
}
