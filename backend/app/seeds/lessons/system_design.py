"""Lesson content for the System Design subject.

Covers four competencies that show up constantly in senior/staff-level
system design interviews and in real backend work: API design, caching,
load balancing, and database scaling. Module count tracks real topic
complexity, not a fixed count — see app.seeds.lessons.types.LessonModule.
"""

from app.seeds.lessons.types import LessonModule

LESSONS: dict[str, list[LessonModule]] = {
    "api-design": [
        LessonModule(
            title="REST semantics, pagination, and versioning",
            content=r"""
## Resources, not actions

REST APIs model **nouns** (resources) manipulated by a small, fixed set of
verbs (HTTP methods). The most common design mistake is smuggling verbs
into the URL because it feels more "obvious":

```
BAD:
POST /createUser
POST /getUserOrders
POST /cancelOrder/42

GOOD:
POST   /users
GET    /users/42/orders
DELETE /orders/42          # or POST /orders/42/cancellation if cancel
                            # is not a true delete (see below)
```

The verb lives in the HTTP method, not the path. `/cancelOrder/42` is a
tell that the API is being designed as a set of remote procedure calls
wearing an HTTP costume, not as resources.

Not every operation is a clean CRUD mapping onto a resource, though.
"Cancel an order" is not the same as "delete an order" — you usually want
to keep the record and change its state. Two accepted patterns:

```
PATCH /orders/42          { "status": "cancelled" }
POST  /orders/42/cancellations       # model the action as a sub-resource
```

Both are more honest than `POST /cancelOrder/42` because they keep the
resource model intact instead of leaking a procedure name into the URL.

## HTTP verbs and status codes, used correctly

| Verb | Meaning | Idempotent? | Safe (no side effects)? |
|---|---|---|---|
| GET | read | yes | yes |
| PUT | full replace | yes | no |
| PATCH | partial update | no (in general) | no |
| POST | create / non-idempotent action | no | no |
| DELETE | remove | yes | no |

"Idempotent" means: calling it N times has the same effect as calling it
once. `PUT /users/42 {name: "Ana"}` sent three times in a row leaves the
same end state as sending it once — that's why `PUT` is safe to blindly
retry on a network timeout. `POST /users` sent three times creates three
users — retries are dangerous unless you add an idempotency key (next
module).

Status codes are part of the contract, not decoration. Common misuse:

```
BAD:  return 200 OK with {"error": "user not found"} in the body
GOOD: return 404 Not Found with a structured error body
```

A caller (or a load balancer, or a monitoring dashboard) that only looks
at the status code learns nothing useful from the first version — every
response looks identical whether it succeeded or failed. Key codes to use
precisely:

- `200` — success with a body (GET, successful PATCH/PUT).
- `201 Created` — successful POST that created a resource; include a
  `Location` header pointing at it.
- `204 No Content` — success with nothing to return (DELETE).
- `400` — malformed request (client sent garbage the server can't parse).
- `401` — not authenticated (who are you?).
- `403` — authenticated but not authorized (I know who you are, you can't
  do this).
- `404` — resource doesn't exist.
- `409 Conflict` — request conflicts with current state (e.g. optimistic
  concurrency version mismatch, duplicate unique key).
- `422 Unprocessable Entity` — well-formed request, semantically invalid
  (e.g. `end_date` before `start_date`).
- `429 Too Many Requests` — rate limited.
- `500` — unhandled server error. `503` — server is temporarily
  unavailable (overloaded, in maintenance) — distinct from 500 because a
  503 tells the caller "retry later," a 500 doesn't promise that.

## Pagination: cursor vs offset

**Offset pagination** (`GET /orders?limit=20&offset=40`) is simple and
lets you jump to page N directly, but has two real problems at scale:

1. **Performance.** `OFFSET 100000` still makes the database walk and
   discard the first 100,000 rows before returning the next page — cost
   grows linearly with how deep you page.
2. **Consistency under concurrent writes.** If a row is inserted before
   the offset window while you're paging, every subsequent page shifts by
   one — you can see a duplicate or skip a row entirely between page
   fetches.

**Cursor pagination** (`GET /orders?limit=20&after=eyJpZCI6NDJ9`) encodes
"where I left off" — typically the last-seen sort key(s), often
base64-encoded — instead of a numeric position:

```
GET /orders?limit=20
-> { "items": [...], "next_cursor": "eyJpZCI6NjJ9" }

GET /orders?limit=20&after=eyJpZCI6NjJ9
-> { "items": [...], "next_cursor": "eyJpZCI6ODJ9" }
```

The query becomes `WHERE id > 62 ORDER BY id LIMIT 20` — a direct index
seek regardless of how deep you are, and it's stable under concurrent
inserts because it's anchored to a value, not a position. The tradeoff:
you lose "jump to page 7" — cursors are inherently sequential, forward
(or backward) only. For most infinite-scroll / API-consumer pagination
this tradeoff is worth it; for an admin UI with page numbers, offset
pagination on a bounded, rarely-huge table is often fine.

## Versioning strategies

Two mainstream approaches:

```
URL versioning:      GET /v1/users/42
Header versioning:    GET /users/42
                       Accept: application/vnd.myapi.v1+json
```

**URL versioning** is explicit, cacheable by URL, trivially visible in
logs and browser address bars, and easy for clients to understand — this
is why it dominates in practice (Stripe, GitHub, most public APIs use
some flavor of it). Downside: it implies the entire API moves in lockstep
versions, even when only one endpoint changed.

**Header versioning** keeps URLs stable (nice for REST purists — the URL
identifies the *resource*, not a version of an API), and allows per-
request negotiation. Downside: invisible in browser address bars and
harder to test with a plain link; most engineers reach for `curl -H` far
less readily than editing a URL.

In practice, most teams do best with URL versioning at a coarse
`v1`/`v2` level and avoid breaking changes as long as possible via
additive changes (new optional fields, new endpoints) — a new major
version is a last resort because every version is a parallel API surface
you maintain.

## Key takeaways

- Model resources (nouns) in the URL; let the HTTP method carry the verb.
- Status codes are part of the contract — a caller should be able to
  branch on the status code alone without parsing the body.
- Offset pagination is simple but degrades in performance and can skip or
  duplicate rows under concurrent writes; cursor pagination anchors to a
  value, staying fast and stable but forward/backward-only.
- URL versioning (`/v1/...`) wins on visibility and simplicity; header
  versioning keeps URLs "pure" at the cost of discoverability. Prefer
  additive, backward-compatible changes over bumping versions at all.
""",
        ),
        LessonModule(
            title="Idempotency and error contracts",
            content=r"""
## Why idempotency matters for retries

Networks fail in the worst possible way: **you don't know if the request
you sent actually reached the server and was processed.** A client that
calls `POST /payments {"amount": 100}`, the request succeeds on the
server, and then the response is lost to a network blip, cannot tell that
apart from the request never having arrived at all. The client's only
safe options are "give up" (bad — money should have moved) or "retry"
(dangerous — money might move *twice*).

This is not a hypothetical edge case; it's the default behavior of every
TCP connection, every load balancer, every mobile client on a flaky
connection. Any POST endpoint that has a real-world side effect
(charging a card, sending an email, placing an order, incrementing an
inventory count) needs a story for "what happens when the client retries
because it wasn't sure the first attempt worked."

## Idempotency keys (the payments-industry pattern)

The client generates a unique key (typically a UUID) per *logical*
operation — not per HTTP request — and sends it on every attempt of that
operation:

```
POST /payments
Idempotency-Key: 7f3e9b2a-6c41-4e2d-9c88-1a2b3c4d5e6f
{ "amount": 10000, "currency": "USD", "customer_id": "cus_42" }
```

Server-side handling:

```python
def create_payment(idempotency_key: str, body: PaymentRequest) -> Payment:
    existing = idempotency_store.get(idempotency_key)
    if existing is not None:
        if existing.request_hash != hash(body):
            raise ConflictError(
                "Idempotency-Key reused with a different request body"
            )
        return existing.response  # replay the original result, unchanged

    # Reserve the key BEFORE doing the side effect, inside the same
    # transaction/lock that performs it, to close the race between two
    # concurrent retries both passing the "not found" check above.
    payment = charge_card(body)
    idempotency_store.save(idempotency_key, request_hash=hash(body), response=payment)
    return payment
```

Three details that matter in a real implementation:

1. **The key must be reserved atomically with the side effect**, not
   checked-then-acted in two separate steps — otherwise two retries
   arriving at nearly the same time both pass the "no existing key" check
   and both charge the card. This is typically a unique constraint on
   `idempotency_key` in the same table/transaction as the payment write,
   or a short-lived lock held for the duration of the operation.
2. **Keys expire.** Storing them forever is unbounded growth; 24 hours is
   a common window, matching how long a client is expected to retry
   before giving up and asking a human.
3. **Same key + different body = reject, don't silently reuse.** If a
   client sends the same `Idempotency-Key` with a different `amount`,
   that's a client bug, not something to paper over — return `409/422`.

Note the asymmetry with plain HTTP idempotency (the earlier module's
table): `PUT`/`DELETE` are *naturally* idempotent because of what they
mean semantically. `POST /payments` is not naturally idempotent — placing
an order twice is a different outcome from placing it once — so it needs
an *explicit* mechanism (the key) to make retries safe. Idempotency keys
are how you get POST's flexibility with PUT's retry safety.

## Consistent error response shapes

An API that returns a different error JSON shape per endpoint (or per
exception type, if you just serialize whatever the framework threw)
forces every client to write bespoke error-parsing logic per call site.
A single, predictable envelope pays for itself the first time a client
needs to show a useful message to a user or branch on error type:

```
BAD (inconsistent across endpoints):
  { "error": "Not found" }
  { "message": "Validation failed", "fields": [...] }
  { "detail": "insufficient_funds" }

GOOD (one shape, always):
{
  "error": {
    "code": "insufficient_funds",
    "message": "Card has insufficient funds for this charge.",
    "details": [
      { "field": "amount", "issue": "exceeds available balance" }
    ],
    "request_id": "req_9f8e7d6c"
  }
}
```

Why each field earns its place:

- **`code`** — a stable, machine-readable string the client can `switch`
  on. Unlike the HTTP status code (coarse: "409 conflict") this can be
  specific ("insufficient_funds" vs "duplicate_charge" — both might be
  409s). Never change an existing code's meaning; adding new codes is
  backward compatible, repurposing one is not.
- **`message`** — human-readable, safe to show directly or log; not
  meant to be parsed.
- **`details`** — structured, per-field validation errors for forms.
- **`request_id`** — ties the error back to a specific server-side log
  line/trace; the single most useful field when a user reports "it broke"
  and you need to find out what actually happened without guessing.

The same envelope should wrap *every* error, from a 400 validation
failure to a 500 the framework generated for an unhandled exception —
which usually means a global exception handler/middleware that catches
everything and reshapes it, rather than trusting every endpoint to
individually format errors correctly.

## Key takeaways

- Networks can fail after the server has already processed a request but
  before the client sees the response — the client can't distinguish
  "never arrived" from "succeeded, response lost," so blind retries of
  non-idempotent operations are unsafe without extra machinery.
- Idempotency keys make a POST safe to retry: reserve the key atomically
  with the side effect, replay the stored response for a repeat key, and
  reject a repeated key with a different body.
- A single, consistent error envelope (stable `code`, human `message`,
  structured `details`, `request_id`) across every endpoint is what makes
  client-side error handling and support debugging tractable — enforce it
  centrally (one exception handler), not endpoint by endpoint.
""",
        ),
    ],
    "caching-strategies": [
        LessonModule(
            title="Caching patterns: cache-aside, write-through, write-behind",
            content=r"""
## Why cache at all

A cache trades **staleness risk** for **latency and load reduction**. It
only makes sense when reads vastly outnumber writes for the data in
question, and when serving slightly-stale data is acceptable for at least
a short window. Caching write-heavy, must-be-fresh data (an inventory
counter you decrement on every sale, right before checkout) is a common
source of subtle correctness bugs — know what you're trading before you
add a cache, not after production incidents teach you.

## Cache-aside (lazy loading)

The application code owns the cache explicitly: check cache, on miss read
the source of truth and populate the cache, then serve.

```python
def get_user(user_id: UUID) -> User:
    cached = cache.get(f"user:{user_id}")
    if cached is not None:
        return cached

    user = db.query(User).get(user_id)     # cache miss -> hit the DB
    cache.set(f"user:{user_id}", user, ttl=300)
    return user

def update_user(user_id: UUID, changes: dict) -> User:
    user = db.update(User, user_id, changes)
    cache.delete(f"user:{user_id}")         # invalidate, don't update
    return user
```

This is the most common pattern (what most people mean by "we added
Redis in front of Postgres") because it's simple and the cache only ever
holds what's actually been requested — no wasted memory on cold data.

Tradeoffs:
- **First request after a miss/expiry is slow** (has to hit the DB) —
  the "thundering herd on cold cache" problem, covered in the next
  module.
- **On write, invalidate rather than update the cache directly.**
  Deleting is simpler and safer than trying to write the new value into
  the cache from the write path — writing the cache directly risks races
  where a concurrent read repopulates a stale value right after your
  delete (this is exactly what the next module's locking techniques
  address), or where the write path's view of "the new value" doesn't
  match what a read would compute (e.g. cached data is a joined/derived
  view).
- The cache and the database **can disagree** during the gap between a
  DB write and the corresponding cache invalidation — a brief inconsistency
  window, not eventual-never.

## Write-through

The application writes to the cache and the cache synchronously writes
through to the database as part of the same request — the cache sits
*in front of* the database on the write path, not just the read path.

```
App -> Cache.set(key, value)  -> Cache writes to DB synchronously -> ack
```

The cache is always consistent with the database immediately after a
write (no invalidation gap), and reads are always fast because the cache
is always populated for anything that's ever been written. The cost:
every write now pays cache-write latency *and* DB-write latency, in
series, so writes get slower — you've optimized reads by taxing writes.
Also, on a cold cache (fresh instance, eviction), a plain write-through
cache doesn't automatically populate itself for existing rows the way
cache-aside does on a miss — it needs cache-aside-style backfill on read,
or a warm-up job, or both.

## Write-behind (write-back)

Like write-through, but the write to the durable store is deferred and
batched asynchronously instead of happening in the request path:

```
App -> Cache.set(key, value)  -> ack immediately
                               -> (async, batched) flush to DB later
```

Writes are very fast (the client only waits on the cache write, not the
DB), and batching many updates to the same key into one DB write reduces
DB load — genuinely useful for something like a view counter or a
leaderboard score updated thousands of times a second, where only the
latest value matters and you don't want every increment to be a DB
round-trip.

The serious cost: a **durability gap**. If the cache node dies before the
deferred write flushes, that data is gone — never made it to the source
of truth. Write-behind is appropriate for data where losing the last few
seconds of updates is tolerable (analytics counters, non-critical
denormalized aggregates) and inappropriate for anything where "the
customer paid us $500 and we lost the record" is a possible outcome —
that data needs a durable write in the request path, full stop.

## Choosing between them

| Pattern | Read latency | Write latency | Consistency risk | Good for |
|---|---|---|---|---|
| Cache-aside | fast (warm) | normal (DB only) | brief staleness | general-purpose default |
| Write-through | fast, always warm | slow (cache+DB) | none | read-heavy, correctness-sensitive |
| Write-behind | fast, always warm | very fast | loss on crash | high-write-volume, loss-tolerant |

Most systems default to cache-aside because it's the simplest to reason
about and fails safe (worst case: extra DB load, not data loss). Reach
for write-through/write-behind only when you've identified a specific
access pattern (very read-heavy with correctness needs, or very
write-heavy with loss tolerance) that cache-aside doesn't serve well.

## Key takeaways

- Cache-aside: app checks cache, falls back to DB on miss, invalidates
  (not updates) on write. Simple, safe-by-default, the right starting
  point for most caches.
- Write-through: cache and DB stay synchronously consistent, at the cost
  of slower writes (two writes in series).
- Write-behind: fastest writes via async batched flush to the DB, at the
  cost of a real durability gap if the cache dies before flushing — only
  acceptable for loss-tolerant data.
- Caching only pays off when reads dominate writes and some staleness is
  tolerable; caching hot, correctness-critical, write-heavy data is a
  common source of production incidents.
""",
        ),
        LessonModule(
            title="Invalidation, TTLs, and the two hard problems",
            content=r"""
## "There are only two hard things in Computer Science: cache
invalidation and naming things."

Phil Karlton's line (often quoted with "...and off-by-one errors" tacked
on as a joke) is funny because it's true: caching itself is easy — the
hard part is knowing *when a cached value has stopped being true* and
getting rid of it before someone acts on stale data.

## Strategy 1: TTL (time-to-live) — the default, bounded staleness

Every cached entry expires automatically after a fixed duration, whether
or not the underlying data changed:

```python
cache.set(f"product:{id}", product, ttl=60)   # 60 seconds
```

This is the simplest strategy: you never have to explicitly track every
place a value could change, because staleness self-heals within one TTL
window. The entire design question collapses to picking the TTL:

- **Too short** — you lose most of the caching benefit; the cache is
  perpetually cold and you're back to hammering the source of truth.
- **Too long** — users (or downstream systems) can act on data that's
  been wrong for minutes. A price that changed 4 minutes ago but is
  cached with a 5-minute TTL is a price someone might pay incorrectly.

Pick the TTL based on **how bad it is to be wrong for that long**, not on
a round number that feels convenient. A user's display name being 60
seconds stale is harmless; an account balance being 60 seconds stale
during a fraud check is not.

## Strategy 2: explicit invalidation — precise, but you have to catch every path

Instead of (or in addition to) a TTL, actively delete/update the cache
entry the moment the underlying data changes:

```python
def update_product_price(product_id: UUID, new_price: Decimal) -> None:
    db.update(Product, product_id, {"price": new_price})
    cache.delete(f"product:{product_id}")
```

This gives you correctness the instant the write happens instead of
waiting out a TTL — but only for writes that go through code paths you
remembered to instrument. The classic way this breaks:

- A bulk admin script updates prices directly via SQL, bypassing the
  application's `update_product_price` function — the cache never
  learns about it and now silently serves a wrong price until TTL
  expiry (which is exactly why relying on explicit invalidation *alone*,
  with no TTL as a backstop, is fragile — always keep a TTL as a safety
  net even when you also invalidate explicitly).
- A value is derived from multiple source rows (e.g. a cached "order
  summary" built from the order plus its line items plus a discount
  code) — you have to invalidate it from *every* write path that
  touches any of those tables, and it's easy to miss one.

## Strategy 3: versioned keys — sidestep invalidation entirely

Instead of deleting a stale key, change *which key* you read/write, so
old entries are simply never looked at again (and naturally age out via
TTL or LRU eviction, with no explicit delete needed):

```python
def cache_key_for_product(product_id: UUID) -> str:
    version = cache.get(f"product:{product_id}:version") or 1
    return f"product:{product_id}:v{version}"

def update_product_price(product_id: UUID, new_price: Decimal) -> None:
    db.update(Product, product_id, {"price": new_price})
    cache.incr(f"product:{product_id}:version")  # old v-key is now orphaned
```

This is especially useful for **bulk/global invalidation** — e.g. bump a
single `schema:version` key to invalidate an entire class of cached
responses at once (a config change, a deployed template change) without
enumerating every individual key that's affected. The cost is one extra
cache read to resolve the current version before every cache access, and
old versions sitting around until they naturally expire/evict (usually a
non-issue since they're small and TTL'd anyway).

## Putting it together: layered defense

Production systems rarely pick just one of these — they layer them:

1. **TTL as the backstop** on every cached entry, sized to "how bad is it
   to be wrong for this long" — this bounds the *worst case* staleness
   even if every other mechanism fails.
2. **Explicit invalidation** on the known, common write paths, for
   correctness the instant a write happens rather than waiting out the
   TTL.
3. **Versioned keys** for anything invalidated in bulk (config, schema,
   anything with many dependents) rather than trying to enumerate every
   affected cache key by hand.

## Key takeaways

- TTL bounds worst-case staleness with zero bookkeeping — always keep one
  as a backstop, sized to how costly it is to be wrong for that duration.
- Explicit invalidation is precise but only as good as your coverage of
  every write path — bulk updates and multi-table derived values are
  where it silently breaks.
- Versioned keys turn "delete this stale value" into "stop pointing at
  it," which is the cleanest way to invalidate many related keys at once.
- Real systems combine all three rather than picking one strategy
  exclusively.
""",
        ),
        LessonModule(
            title="Cache stampede (thundering herd) and mitigations",
            content=r"""
## The failure mode

A cache stampede happens when a **popular** key expires (or the cache
node restarts cold) and a **large burst of concurrent requests** all miss
the cache at the same moment, all fall through to the source of truth
simultaneously, and collectively overwhelm it:

```
t=0    "homepage:featured_products" TTL expires
t=0ms  1,200 requests/sec are hitting this endpoint
t=0ms  all 1,200 concurrent requests see a cache miss
t=1ms  all ~1,200 requests independently query the database
       for the same data, at the same instant
```

The database, which was comfortably serving 1,200 *cached* reads/sec,
suddenly gets 1,200 *identical, uncached* queries in the same instant.
For an expensive query (a join, an aggregation), this can be enough to
saturate connections or CPU and cause a cascading outage — the exact
outage the cache existed to prevent. This is especially dangerous for hot
keys (a trending product, a viral post, a widely-shared dashboard) where
"large burst of concurrent requests for one key" is the normal case, not
an edge case.

## Mitigation 1: locking / request coalescing

Only let **one** request recompute the value on a miss; every other
concurrent request either waits for that result or serves a slightly
stale value in the meantime:

```python
def get_featured_products() -> list[Product]:
    cached = cache.get("homepage:featured_products")
    if cached is not None:
        return cached

    lock_acquired = cache.set(
        "homepage:featured_products:lock", "1", ttl=5, nx=True  # nx = only if absent
    )
    if lock_acquired:
        try:
            fresh = compute_featured_products()  # the expensive query
            cache.set("homepage:featured_products", fresh, ttl=60)
            return fresh
        finally:
            cache.delete("homepage:featured_products:lock")
    else:
        # someone else is already recomputing it — briefly wait and
        # retry the cache read, or serve stale data if you have it
        time.sleep(0.05)
        return get_featured_products()
```

`nx=True` (SET-if-not-exists) is the key primitive: only the first
request to reach it wins the lock; every concurrent request behind it
sees the lock already held and backs off instead of also querying the
database. This collapses N concurrent misses into 1 actual DB query.

## Mitigation 2: jittered TTLs

If many keys were populated at the same moment (e.g. a cache warm-up job
that fills 10,000 keys in a tight loop, all with `ttl=300`), they all
expire at the same moment too — turning a single stampede into a
recurring scheduled event every 5 minutes. Adding random jitter spreads
the expirations out:

```python
import random

def set_with_jitter(key: str, value: object, base_ttl: int) -> None:
    jitter = random.uniform(-0.1, 0.1) * base_ttl   # +/- 10%
    cache.set(key, value, ttl=base_ttl + jitter)
```

Cheap to implement, and it converts a synchronized thundering herd into a
smoothed-out trickle of individual misses over time — no coordination
between requests required, unlike locking.

## Mitigation 3: probabilistic early expiration (early recomputation)

Instead of waiting for a hard expiry and then stampeding, have requests
*probabilistically* decide to recompute the value slightly *before* it
expires — with probability that increases as the entry approaches its
actual TTL. A common formula (from the "XFetch" approach):

```
recompute_now = (now - delta * beta * log(random())) >= expiry_time
```

where `delta` is how long the value took to compute last time, and
`beta` tunes aggressiveness. In practice: most requests just serve the
cached value normally; a small and increasing fraction of requests, as
expiry nears, decide "I'll be the one to recompute early" — while
everyone else keeps serving the still-valid cached value. By the time the
entry actually expires, it's already been refreshed by one of these early
requests, so no one ever sees a genuine miss on a hot key. This is more
sophisticated than simple locking and is what large-scale CDN/cache
layers (e.g. Varnish-style "grace mode," some Facebook/Google cache
designs) use for their hottest keys.

## Which one to reach for

- **Locking** — simplest to reason about, works well for a small number
  of very hot keys, adds a small amount of wait time to requests that
  land behind the lock.
- **Jittered TTLs** — near-zero cost, always worth doing for any bulk-
  populated cache; doesn't fully prevent stampedes on a single very hot
  key, just desynchronizes bulk expiry.
- **Probabilistic early expiration** — best for extremely hot keys at
  scale, where you want zero requests to ever see a real miss, at the
  cost of implementation complexity and doing recomputation work
  slightly more often than strictly necessary.

## Key takeaways

- A cache stampede occurs when a popular key's expiry causes many
  concurrent requests to simultaneously miss and hit the source of truth
  at once — the exact overload the cache existed to prevent.
- Locking (SET-if-not-exists) coalesces concurrent misses into one
  actual recompute; other requests wait briefly or serve stale data.
- Jittered TTLs prevent bulk-populated keys from all expiring in
  lockstep — cheap insurance, always worth adding.
- Probabilistic early expiration refreshes hot keys just before they
  expire so genuine misses on the hottest keys become rare to nonexistent.
""",
        ),
    ],
    "load-balancing": [
        LessonModule(
            title="Load balancer algorithms and L4 vs L7",
            content=r"""
## What a load balancer actually does

A load balancer sits between clients and a pool of backend instances,
distributing incoming requests/connections across the pool so no single
instance gets overwhelmed, and so the system keeps serving traffic if one
instance goes down. Two design questions determine how it behaves: *which
layer of the network stack does it operate at*, and *which algorithm does
it use to pick a backend*.

## Layer 4 vs Layer 7

**L4 (transport layer)** load balancers operate on raw TCP/UDP
connections. They see IP addresses and ports, not HTTP — they don't parse
the request at all. A connection gets routed to a backend and then every
packet on that connection goes to the same backend for its lifetime.

- Very fast (no parsing overhead) and protocol-agnostic (works for any
  TCP traffic, not just HTTP).
- Cannot route based on anything inside the request — no routing by URL
  path, header, or cookie, because it never looks that far.
- Example: a plain TCP load balancer, or AWS Network Load Balancer.

**L7 (application layer)** load balancers terminate and parse the actual
HTTP request, so they can make routing decisions based on its content:

```
Route /api/v1/*      -> backend pool "api-v1"
Route /api/v2/*      -> backend pool "api-v2"
Route Host: admin.*  -> backend pool "admin"
Route /static/*      -> CDN origin pool
```

- Enables path-based routing, header/cookie-based routing (canary
  releases, A/B tests, sticky sessions), request-level retries, and
  request-level metrics (latency per route, error rate per route).
- Costs more CPU per request (TLS termination + HTTP parsing) and adds a
  small amount of latency versus a dumb L4 pass-through.
- Example: NGINX, Envoy, HAProxy in HTTP mode, AWS Application Load
  Balancer.

Most modern web architectures use L7 at the edge (need path/host-based
routing, TLS termination, canary deploys) and sometimes L4 for raw
internal TCP services (databases, gRPC-only internal meshes) where HTTP-
level features aren't needed and the extra speed matters.

## Algorithm: round robin

Requests are handed to backends in strict rotating order: 1, 2, 3, 1, 2,
3, ... Simple, and fair *by request count* — but not by request cost or
backend capacity. If backend 2 is handling a request that takes 10x as
long as the others (a slow report generation), round robin keeps sending
it new work at the same rate as the fast backends, and it falls behind.

**Weighted round robin** fixes the "backends have different capacity"
half of this (send instance A twice as much as instance B if A has twice
the CPU) but not the "request cost varies" half.

## Algorithm: least connections

Route each new request to whichever backend currently has the fewest
open/in-flight connections:

```
Backend A: 12 active connections
Backend B: 3 active connections   <- next request goes here
Backend C: 9 active connections
```

This self-corrects for uneven request cost — a backend stuck processing
slow requests naturally accumulates open connections and stops receiving
new ones until it catches up, without needing to know *why* it's slow.
Generally a better default than round robin for HTTP traffic with
variable request cost (most real APIs), at the cost of the load balancer
needing to track connection state per backend rather than just an
index.

## Algorithm: consistent hashing

Route based on a hash of some request attribute (client IP, session ID,
cache key) so that **the same input consistently lands on the same
backend** — critical whenever backends hold per-client state that isn't
shared (an in-memory cache, a sticky session, a WebSocket connection).

The naive approach — `hash(key) % num_backends` — has a fatal flaw:
adding or removing *one* backend changes `num_backends` and therefore
reshuffles almost every key's target backend, effectively invalidating
your entire cache/session state at once. Consistent hashing avoids this
by mapping both backends and keys onto a fixed hash ring (e.g. 0 to
2^32-1); a key is routed to the next backend clockwise from its position
on the ring:

```
Hash ring (simplified):
   0 -------- B ---------- A ---------- C -------- 2^32-1
   key_1 (hash=50) -> next backend clockwise -> A
   key_2 (hash=200) -> next backend clockwise -> C

Removing A: only keys that hashed to A's arc move (to C, the next
clockwise backend) — B and C's existing keys are undisturbed.
```

Removing or adding one backend only remaps the keys that were
specifically mapped to (or near) that backend — roughly `1/N` of all
keys — instead of remapping everything. This is what makes horizontal
scaling of stateful/cache-backed services tolerable: you don't lose your
entire cache hit rate every time you add an instance.

## When each matters

- **Round robin / weighted round robin** — stateless services, uniform
  request cost, simplicity is the priority.
- **Least connections** — stateless services with variable request cost
  (the common real-world case) — usually the better default over plain
  round robin.
- **Consistent hashing** — any time backends hold state tied to a key
  (client-affinity caching, sharded in-memory data, sticky sessions) and
  you need scaling events to disturb as little of that state as possible.

## Key takeaways

- L4 load balancers route raw connections fast but blind to HTTP
  content; L7 load balancers parse HTTP and can route by path/host/
  header at the cost of more per-request overhead — most edge
  architectures use L7 for that routing flexibility.
- Round robin is fair by request count only; least connections
  self-corrects for uneven request cost and is the better default for
  most real HTTP traffic.
- Consistent hashing keeps the same key mapped to the same backend and,
  critically, only remaps ~1/N of keys when a backend is added or
  removed — essential whenever backends hold per-key state.
""",
        ),
        LessonModule(
            title="Health checks, autoscaling, and the next bottleneck",
            content=r"""
## Health checks: don't route to a backend that can't serve

A load balancer needs to know which backends are actually able to handle
traffic *right now* — a process can be running (the OS sees it, TCP
connections succeed) while the application inside it is deadlocked,
out of DB connections, or stuck in an infinite GC pause. Two common
checks, used together:

- **Liveness check** — "is the process up at all?" Usually just a TCP
  connect or a trivial `GET /healthz` that returns 200 without touching
  any dependency. If this fails, the process is likely wedged and should
  be restarted (this is typically the orchestrator's — e.g. Kubernetes
  — job, not the load balancer's).
- **Readiness check** — "is this instance ready to serve *real* traffic
  right now?" Usually checks that its DB connection pool is healthy, that
  it's finished start-up initialization, and that it isn't in a
  deliberate drain state before shutdown. If this fails, the load
  balancer should stop routing new requests here *without* killing the
  process — it might recover in a few seconds (e.g. a transient DB
  blip), and restarting it would be destructive overkill for a temporary
  condition.

```
GET /healthz/live   -> 200 always, unless the process itself is broken
GET /healthz/ready  -> 200 only if: DB pool healthy AND not draining
                        AND startup complete
```

Conflating the two is a common bug: a `/health` endpoint that just
returns `200 OK` unconditionally tells the load balancer nothing useful
— it'll happily keep routing traffic to an instance whose database
connection pool is exhausted, because the process itself is technically
"up."

**Graceful shutdown** is the readiness check's other job: before a
deployment kills an instance, it should first fail its readiness check
(so the load balancer stops sending new requests) while still finishing
in-flight requests, and only then actually terminate. Skipping this
causes visible request failures on every single deploy.

## Autoscaling triggers

Autoscaling adds/removes backend instances based on a metric crossing a
threshold. Picking the right metric matters more than picking the right
threshold number:

- **CPU utilization** — the classic default, easy to reason about, but
  misleading for I/O-bound services (a service mostly waiting on a slow
  downstream API or a DB query shows *low* CPU while still being
  saturated on concurrent request slots).
- **Request queue depth / in-flight requests** — closer to "are we
  actually falling behind," works well regardless of whether the
  bottleneck is CPU or I/O.
- **p99 latency** — scale out when tail latency crosses a threshold;
  directly reflects user-facing pain, but is a lagging indicator (by the
  time p99 degrades, users already felt it) and can be noisy.
- **Custom business metrics** — e.g. queue length in a message broker for
  a worker pool, which is a much more direct signal than CPU for
  queue-consumer workloads.

Autoscaling also needs a **cooldown/stabilization window** — without one,
a brief spike triggers a scale-out, the new instances come up and the
average utilization drops, triggering an immediate scale-in, which
removes the very capacity that was about to be needed again ("flapping").
Real autoscalers wait for a metric to be sustained over a window (e.g.
"CPU > 70% for 3 consecutive minutes") before acting, and scale in more
conservatively/slowly than they scale out.

## What actually becomes the bottleneck first

Horizontal scaling of application servers is the easy part — stateless
compute is close to infinitely scalable if the LB and orchestration
support it. What breaks first, in rough order of how often it bites in
practice:

1. **The database.** Adding 10x more application instances means 10x
   more potential concurrent connections and queries hitting one
   (initially) database. The DB is very often the true bottleneck behind
   an apparent "we need more app servers" symptom — see the
   database-scaling competency for read replicas, connection pooling,
   and sharding.
2. **Stateful in-process data.** A service holding session data,
   WebSocket connections, or an in-memory cache *in the process itself*
   doesn't scale cleanly — a new instance starts with none of that
   state. This forces either **sticky sessions** (the load balancer
   consistently routes a given client to the same instance — see the
   previous module's consistent hashing) or moving that state out to a
   shared external store (Redis-backed sessions, an external cache) so
   any instance can serve any client. Sticky sessions are a stopgap:
   they reintroduce a single point of failure per client (if that one
   instance dies, that client's state is gone) and unbalance load if
   some sticky clients are far more active than others.
3. **Shared downstream dependencies** — a third-party API with its own
   rate limit doesn't scale just because you added more of your own
   instances; you've just moved the bottleneck one hop over and possibly
   made it worse (more concurrent callers hitting the same external
   limit).
4. **The load balancer itself**, at extreme scale — usually the last
   thing to become the bottleneck in practice, but a single LB node has
   a connection/throughput ceiling too, which is why LBs themselves are
   often deployed in redundant, sometimes horizontally scaled, pairs/
   pools behind DNS or anycast.

The practical implication: "just add more instances behind the load
balancer" is necessary but rarely sufficient on its own — it shifts load
onto whatever the new instances all share (almost always the database),
and that shared resource is where the real scaling work usually has to
happen next.

## Key takeaways

- Separate liveness ("is the process alive, restart if not") from
  readiness ("can this instance take traffic right now, stop routing if
  not") — a health check that only checks the former lets the LB keep
  sending traffic to instances that can't actually serve it.
- Graceful shutdown means failing readiness first, draining in-flight
  requests, then terminating — skipping this causes failed requests on
  every deploy.
- Pick autoscaling triggers that reflect the real bottleneck (queue
  depth/latency for I/O-bound services, not just CPU), and use a
  stabilization window to avoid flapping.
- Stateless application servers scale horizontally fairly easily; the
  database, in-process state (sessions/caches), and shared external
  dependencies are what actually hit a ceiling first — scaling app
  servers alone just moves the bottleneck downstream.
""",
        ),
    ],
    "database-scaling": [
        LessonModule(
            title="Read replicas and replication lag",
            content=r"""
## The basic idea

A **primary** (or "leader"/"master") database handles all writes. One or
more **read replicas** ("followers") receive a continuous stream of
changes from the primary (via its write-ahead log, in Postgres terms) and
apply them to keep their own copy up to date. Read traffic — which in
most applications vastly outnumbers write traffic — gets spread across
the replicas, freeing the primary to focus on writes and leaving
headroom before it becomes the bottleneck.

```
                 writes
Clients -------------------> Primary
   |                            |  (replication stream)
   |          reads             v
   +----------------------> Replica 1
   |
   +----------------------> Replica 2
```

This is usually the *first* scaling lever reached for once a single
database instance can't keep up, because it requires no application data
model changes (unlike sharding) — just routing logic for "which
connection do I use for this query."

## Replication lag is not optional — it's physics

Replication is asynchronous in most common setups (Postgres streaming
replication in its default async mode, MySQL async replication): the
primary commits a write and returns success to the client *before*
confirming every replica has applied it. The replica catches up
shortly after — usually milliseconds, but under load, network hiccups,
or a replica running a long query, that lag can stretch to seconds or
more. This isn't a bug to be fixed; it's an inherent property of
asynchronous replication, and any system using it needs to account for
the lag rather than assume it doesn't exist.

## The read-your-writes problem, concretely

```
t=0ms    User submits a profile update: POST /profile {"bio": "..."}
         -> write goes to Primary, commits, returns 200 OK
t=5ms    Client immediately does GET /profile to show the updated page
         -> read is routed to Replica 2, which hasn't applied the
            write yet (lag = 5-50ms is common under load)
t=5ms    Replica 2 returns the user's OLD bio
```

From the user's point of view, they just saved a change and it appears
to have not saved — genuinely confusing and a very common real-world bug
report ("I updated my profile and it reverted!"). It didn't revert; a
subsequent read simply landed on a replica that hadn't caught up yet.

## Mitigations

**1. Route the immediate post-write read to the primary.** The simplest
fix: after a write, force the next read for that same resource (or for
that user, for some short window) to hit the primary instead of a
replica — often via a short-lived flag/cookie or by routing all reads
for a logged-in mutation-performing session to the primary for a few
seconds.

```python
def update_profile(user_id: UUID, changes: dict) -> None:
    db.primary.update(User, user_id, changes)
    session_cache.set(f"read_from_primary:{user_id}", True, ttl=5)

def get_profile(user_id: UUID) -> User:
    use_primary = session_cache.get(f"read_from_primary:{user_id}")
    conn = db.primary if use_primary else db.pick_replica()
    return conn.query(User).get(user_id)
```

**2. Track replication position and wait for it.** More precise: after a
write, note the primary's log position (e.g. Postgres's LSN); when a read
comes in, check whether the target replica has caught up to at least that
position, and either wait briefly or fall back to the primary if not.
More correct than a blanket "route to primary for N seconds" but more
complex to implement.

**3. Accept the staleness for reads that don't need read-your-writes.**
Not every read is "did my own write just take effect." A user viewing
someone *else's* public profile, a dashboard showing aggregate stats, a
product listing page — these can tolerate a few hundred milliseconds of
staleness with zero user-visible harm, and should be routed to replicas
without any special-casing. The mitigation only needs to apply to the
specific "user reads back what they themselves just wrote" pattern.

## What replicas are (and aren't) good for

Good for: spreading read load, providing read availability if the
primary is temporarily down (with a promotion process), running
expensive analytical/reporting queries off a replica so they don't
compete with production traffic on the primary.

Not a substitute for: write scaling (every replica still funnels through
the same primary for writes — replicas don't help write throughput at
all), and not a substitute for backups (replication propagates mistakes
just as faithfully as good writes — a bad `DELETE` without a `WHERE`
clause replicates to every follower in milliseconds; only a
point-in-time backup protects against that).

## Key takeaways

- Read replicas scale read throughput without changing the data model —
  usually the first lever pulled after a single DB instance is
  saturated — but do nothing for write throughput.
- Replication lag is inherent to asynchronous replication, not a defect;
  design for it rather than assuming replicas are always current.
- The read-your-writes problem (user's own write appears to have not
  happened) is the most common user-visible symptom of lag — fix it by
  routing the immediate post-write read to the primary, or by tracking
  and waiting for replication position, applied only where read-your-
  writes actually matters.
- Replicas are not a backup strategy — they replicate mistakes as
  faithfully as valid writes.
""",
        ),
        LessonModule(
            title="Connection pooling and pool exhaustion",
            content=r"""
## Why you can't just open a connection per request

Opening a new database connection is expensive relative to the queries
it will run: TCP handshake, TLS negotiation (if applicable), database
authentication, and on Postgres specifically, the backend forks an
entire new OS process per connection — measured in single-digit to
tens of milliseconds, versus sub-millisecond for a simple indexed query.
Under real traffic, opening (and tearing down) a fresh connection for
every request wastes more time and CPU on connection setup than on the
actual query work, and can outright overwhelm the database's connection
handling before it does any useful work.

Databases also have a **hard cap** on concurrent connections (Postgres
defaults to 100; each one, especially in Postgres's process-per-
connection model, costs real memory — often cited around 5-10MB of
overhead per idle connection). This cap is not really about the load —
it's a fixed ceiling regardless of how powerful the underlying hardware
is, meaning you cannot simply "add more app instances" your way past it
without hitting a wall.

## Connection pooling: reuse instead of reopen

A connection pool keeps a set of already-established connections open
and hands them out to application code on demand, returning them to the
pool when the request finishes instead of closing them:

```python
# Application code borrows and returns a connection; the pool owns the
# lifecycle of the underlying TCP/auth handshake.
with connection_pool.acquire() as conn:
    conn.execute("SELECT * FROM users WHERE id = %s", (user_id,))
# connection returned to the pool here, ready for the next borrower
```

Most ORMs/drivers include an in-process pool (SQLAlchemy's default
`QueuePool`, for instance) sized per application instance — e.g. "each of
our 20 app server processes keeps a pool of 10 connections open." The
problem: `20 instances * 10 connections = 200`, comfortably over
Postgres's default 100-connection cap, *before counting analytics jobs,
migrations, or a human connected via psql*. This is exactly the scenario
that autoscaling makes worse — each new app instance that spins up to
handle load brings its own pool, and connection count grows with
instance count even though the database's connection ceiling didn't move.

## External pooling: PgBouncer-style

PgBouncer (and similar tools — RDS Proxy, pgpool) sits as a separate
process between the application fleet and the database, holding a
*small*, fixed pool of real database connections and multiplexing many
more client connections onto them:

```
20 app instances x 10 in-process connections each = 200 client-side
"connections" ... but they connect to PgBouncer, not Postgres directly

PgBouncer -> maintains, say, 20 real connections to Postgres

Postgres sees: 20 connections, regardless of how much the app fleet scales
```

The key mechanism is **transaction-mode pooling**: a real Postgres
connection is only checked out from PgBouncer's pool for the duration of
a single transaction, then immediately returned to the pool for another
client's transaction to use — instead of being held for an entire
client session. This is what lets a small number of real backend
connections serve a much larger number of concurrent application
requests, as long as no single transaction holds the connection open
for long.

The tradeoff: transaction-mode pooling breaks session-level features
that assume a connection is "yours" for its whole lifetime — session-
level temporary tables, `SET` statements meant to persist across
queries, and multi-statement session state referring back to a
`PREPARE`d statement from earlier in the session. Applications behind
transaction-mode PgBouncer need to avoid relying on session state
outliving a single transaction.

## Pool exhaustion: the failure mode

When every connection in a pool is checked out and none are free, the
next request has to wait — and if it waits past its own timeout, it
fails, even though the database itself might be perfectly healthy and
underloaded. This is a distinct failure mode from "the database is slow"
— pool exhaustion is "the *pool* is the bottleneck," visible as request
timeouts or connection-acquisition errors while the DB's own CPU/IO
metrics look fine.

Common causes:

- **A slow query holding a connection far longer than normal** — every
  other request queues up behind the pool waiting for a connection that
  won't free up until that one slow query finishes.
- **A connection leak** — application code that acquires a connection
  (e.g. opens a transaction) and, due to a bug (a missing `finally`/
  context-manager, an unhandled exception path), never returns it to the
  pool. The pool's available connections monotonically shrink until
  none are left.
- **Pool sized too small for actual concurrency** — under-provisioned
  relative to real traffic, so the pool is fully checked out even under
  entirely normal load.
- **Pool sized too large relative to the database's real capacity** — the
  inverse mistake: a generously sized pool per instance, multiplied
  across many instances, exceeds what the database can actually handle
  concurrently, and the database itself falls over under the connection
  count even though each individual pool looks "fine" from the app's
  side.

## Key takeaways

- Opening a raw connection per request is expensive and doesn't scale —
  connection pooling amortizes that setup cost by reusing established
  connections.
- Databases have a hard, fixed connection ceiling (not a function of
  hardware alone) — naive per-instance pooling multiplies out across a
  scaled fleet and can exceed that ceiling even when each pool looks
  reasonably sized in isolation.
- External poolers like PgBouncer solve this by holding a small number
  of real DB connections and multiplexing many client connections onto
  them, typically per-transaction — at the cost of losing session-level
  state guarantees.
- Pool exhaustion is a distinct failure mode from DB overload: it shows
  up as timeouts/connection-acquisition errors while the database's own
  metrics look healthy, and is usually caused by slow queries, leaked
  connections, or a pool sized wrong for real concurrency.
""",
        ),
        LessonModule(
            title="Sharding and denormalization",
            content=r"""
## When replicas and indexing stop being enough

Read replicas (module 1) scale read throughput; connection pooling
(module 2) makes many concurrent clients viable. Neither helps when the
problem is **write throughput** or **data volume** exceeding what a
single primary instance can hold or process — every write still funnels
through one primary, and a single machine has a ceiling on disk size,
memory for caching the working set, and write IOPS. When indexing is
already optimal and read replicas are already in place, and the primary
is still the bottleneck on writes or the dataset no longer fits
comfortably on one machine, the remaining lever is **sharding**:
splitting the dataset itself across multiple independent database
instances, each holding a subset of the rows.

```
Single primary (pre-shard):
  orders table: 400M rows, 1 instance, all writes serialize through it

Sharded (post-shard), 4 shards by customer_id:
  Shard 1: customers 0-25M      Shard 2: customers 25-50M
  Shard 3: customers 50-75M     Shard 4: customers 75-100M
  -> each shard independently handles ~100M rows and its own write load
```

## Picking a shard key

The shard key determines which shard a given row lives on (commonly via
`hash(shard_key) % num_shards`, or a range/directory-based mapping). This
is the single most consequential decision in a sharded design, and
mistakes here are expensive to reverse — resharding a live system is a
significant migration, not a config change. What makes a good shard key:

- **High cardinality and even distribution** — enough distinct values,
  spread evenly, so no single shard becomes a hotspot. Sharding by
  `country` fails this if 80% of your users are in one country — that
  shard carries 80% of the load while the others sit idle.
- **Matches your dominant query pattern** — pick the key that most
  queries already filter by, so most queries can be routed to a single
  shard. An e-commerce platform sharding orders by `customer_id` keeps
  "show this customer's order history" (a very common query) entirely
  within one shard; sharding by `order_id` instead would make that same
  query fan out across every shard.
- **Stable over the row's lifetime** — a shard key that can change after
  creation (e.g. sharding a user by their current subscription tier,
  which changes) forces moving the row between shards on that change,
  which is exactly the expensive migration operation you want to avoid
  needing routinely.

## What breaks: cross-shard joins and transactions

The entire reason a single database was easy to work with is that it
gave you joins and transactions across your whole dataset for free.
Sharding takes that away for anything that spans shards:

**Cross-shard joins** — a join between `orders` (sharded by
`customer_id`) and `products` (not naturally tied to any customer) can't
be expressed as a single SQL query if `products` isn't co-located on the
same shard as the relevant `orders` rows. The common answer is
**denormalization**: duplicate the specific product fields the query
needs (name, price at time of order) directly onto the `orders` row
at write time, so the read never needs to join across shards at all:

```sql
-- Normalized (requires a join, breaks across shards):
SELECT o.id, o.quantity, p.name, p.price
FROM orders o JOIN products p ON o.product_id = p.id
WHERE o.customer_id = 42;

-- Denormalized (self-contained within one shard, no join needed):
SELECT id, quantity, product_name, product_price_at_purchase
FROM orders
WHERE customer_id = 42;
```

This is also usually *correct* business behavior independent of
sharding — an order's total should reflect the product's price *at the
time of purchase*, not today's live price, which a live join would
incorrectly return if the price changed since. Denormalization here
fixes a correctness issue and a scaling issue at once — not always the
case, but a useful reminder that "normalize everything, join at read
time" is a default, not a law, and the right amount of denormalization
is a real design decision even before sharding enters the picture.

**Cross-shard transactions** — a transaction that must atomically update
rows on two different shards (e.g. transferring a balance between two
users who happen to hash to different shards) can't rely on a single
database's ACID guarantees anymore. Options, in increasing order of
complexity: avoid the need entirely by shard key design (co-locate
data that transacts together), accept eventual consistency with a
compensating-action pattern (the "saga" pattern — do step 1, do step 2,
and if step 2 fails, run a compensating undo for step 1), or implement a
distributed transaction protocol (two-phase commit) — which is
operationally expensive and rarely the first choice for this reason.

## Denormalize before you shard, if you can

Because cross-shard joins are so costly to work around, it's worth
denormalizing (accepting controlled, intentional data duplication with an
explicit update path) for the specific access patterns that would
otherwise require a cross-shard join — *before* committing to a shard
key, since the denormalization choices influence which key actually
keeps your dominant queries single-shard. This is the general principle
behind "when indexing and replicas aren't enough": try denormalizing
the specific hot paths first (often solves the problem on a single
database, with much less operational complexity), and treat full
sharding as the answer only once write throughput or data volume itself
is the limit, not just query shape.

## Key takeaways

- Reach for sharding only after indexing and read replicas are already
  in place and the bottleneck is write throughput or raw data volume on
  a single primary — it solves a different problem than replicas do.
- The shard key choice is the most consequential and hardest-to-reverse
  decision: pick a high-cardinality, evenly distributed key that matches
  your dominant query pattern and doesn't change over a row's lifetime.
- Cross-shard joins and transactions lose the guarantees a single
  database gave you for free — mitigate joins via denormalization
  (duplicate the fields you need at write time) and mitigate
  transactions by co-locating data that transacts together, or accept
  eventual consistency via a saga/compensating-action pattern.
- Denormalizing the specific hot access patterns often resolves the
  underlying problem on a single database and should be tried before
  committing to a full sharding migration.
""",
        ),
    ],
}
