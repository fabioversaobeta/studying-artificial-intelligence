"""Lesson content for the Distributed Systems subject.

Module count per competency tracks real topic complexity — each of these
four competencies gets two modules: one establishing the core theory
precisely, one applying it to real systems and edge cases. See
app.seeds.lessons.types.LessonModule.
"""

from app.seeds.lessons.types import LessonModule

LESSONS: dict[str, list[LessonModule]] = {
    "cap-theorem": [
        LessonModule(
            title="The theorem, precisely",
            content=r"""
## Why "pick 2 of 3" is a misleading summary

CAP theorem is usually taught as "you can only have two of Consistency,
Availability, and Partition tolerance." That framing is technically true
but practically useless, because it implies partition tolerance is
optional — something you could trade away like the other two. It isn't.
In any real distributed system, the network *will* drop, delay, or
reorder messages between nodes eventually. A system that isn't partition
tolerant isn't a distributed system with a different tradeoff — it's a
single-node system that falls over the first time a cable gets unplugged.
So the real choice CAP forces on you is: **when a partition happens, do
you sacrifice consistency or availability?** CP or AP. That's it. There is
no third option where you keep both, because the theorem (formalized by
Gilbert and Lynch in 2002, building on Eric Brewer's conjecture) proves
you literally cannot.

## What each term actually means — precisely

**Consistency** here does *not* mean ACID consistency (constraints holding).
It means something close to **linearizability**: every read receives the
result of the most recent write, and all nodes see operations in the same
order, as if there were only a single copy of the data. If node A commits
a write and a client immediately reads from node B, that client must see
A's write — not stale data, not "eventually" the right value, *right now*.

**Availability** means every request to a non-failing node receives a
response — not necessarily the *correct* or *latest* value, just *some*
response, and it must not be an error or a timeout. A system that returns
stale data quickly is "available" in CAP's sense; a system that refuses to
answer until it's sure the data is fresh is not.

**Partition tolerance** means the system continues to operate despite an
arbitrary number of messages being dropped or delayed between nodes. Since
partitions are a fact of networked life (a switch fails, a cross-region
link degrades, a GC pause makes a node unreachable for 30 seconds), every
system that spans more than one node has to decide, in advance, what
happens when a partition occurs — you don't get to opt out by "being
careful."

## The actual decision: CP vs AP during a partition

Picture two nodes, A and B, replicating the same key, and the network
between them just split. A client sends a write to A. Another client sends
a read to B. Because A and B can't talk to each other right now, the
system has exactly two choices:

- **Choose consistency (CP):** B refuses to answer the read (or forwards
  it to A, or blocks) until the partition heals and it can guarantee the
  answer reflects A's write. The system sacrifices availability on B's
  side — some requests get errors or timeouts — in exchange for every
  answered request being correct.
- **Choose availability (AP):** B answers immediately with whatever data
  it has locally, possibly stale (it doesn't know about A's write yet).
  The system sacrifices consistency — a client can read data that doesn't
  reflect the latest write — in exchange for never refusing a request.

Neither choice is "wrong" — it's a business decision encoded in
infrastructure. A bank ledger usually wants CP: better to reject a
transaction than let two partitioned replicas both approve overdrafts
against the same balance. A product catalog page usually wants AP: better
to show a slightly stale price than a 500 error, because staleness is
recoverable and a blank page loses the sale outright.

## Outside of a partition, CAP says nothing

This is the detail people most often get wrong: CAP is a theorem about
behavior *during a network partition*, full stop. When the network is
healthy, there's no theoretical reason a system can't be both consistent
and available — and most systems are, most of the time, because
partitions are rare relative to total uptime. CAP doesn't force you to
choose a permanent identity; it forces you to choose a *policy for the bad
day*.

## Key takeaways

- Partition tolerance isn't optional in a real distributed system — the
  real choice CAP forces is CP vs AP *when a partition occurs*, not
  "pick any 2 of 3."
- Consistency in CAP means linearizability (reads reflect the latest
  write, as if there were one copy) — stronger than ACID's "C".
  Availability means every non-failing node answers every request, with
  no guarantee the answer is fresh.
- CP systems refuse or delay requests during a partition to protect
  correctness; AP systems answer with possibly-stale data to protect
  responsiveness.
- CAP only constrains behavior *during* a partition — outside of one, a
  well-built system can be both consistent and available.
""",
        ),
        LessonModule(
            title="Applying CAP — classifying real systems",
            content=r"""
## Working through concrete systems

The theorem is easy to state and easy to misapply, because most real
systems are not purely CP or purely AP everywhere — they make the choice
per operation, or per configuration knob. Still, most systems have a clear
default lean. Walking through examples makes the abstract choice concrete.

### A payments database (e.g. a bank's ledger, or a Spanner-backed system)

**CP.** When a partition splits the cluster, the side that can't verify
it holds a majority (or can't reach the leader) must refuse writes rather
than risk two partitions both crediting/debiting the same account
inconsistently. A rejected transaction is annoying; a double-spent balance
is a regulatory incident. Systems like Google Spanner, or a Postgres
primary with synchronous replication to a standby, explicitly choose to
block or fail writes rather than let the minority side accept them.

### DNS

**AP.** DNS is designed to keep answering even when large parts of the
network are unreachable — a resolver with a cached or stale record will
happily return it rather than refuse to resolve a hostname. Stale DNS
data (an old IP, a since-migrated record) is a tolerable, temporary
inconvenience; DNS refusing to answer at all would break nearly
everything on the internet simultaneously. The whole design (TTL-based
caching, hierarchical delegation, no global lock) optimizes for "always
answer something."

### A chat application (message delivery, presence, typing indicators)

Mostly **AP**, with important CP-flavored exceptions. You want the app to
keep working — showing cached messages, letting you type a message that
queues locally — even if it's disconnected from the server, rather than
freezing the UI. Message *ordering* within a single conversation, though,
often gets a stronger consistency treatment (sequence numbers, per-thread
ordering) even if the system as a whole leans available. This is a good
example of a system choosing CAP behavior per-operation rather than
globally.

### A distributed cache (e.g. Redis Cluster, Memcached pool)

**AP**, almost always by design. The entire point of a cache is to trade
some staleness for speed and availability — if a cache node is
unreachable, you either serve a (possibly stale) value from another
replica or fall through to the source of truth; you never want the cache
layer itself to become a hard blocker on serving traffic. Caches that
tried to be CP would defeat their own purpose: a cache that's unavailable
whenever it can't guarantee freshness provides negative value over just
querying the database directly.

## PACELC: the nuance CAP leaves out

CAP only describes behavior *during* a partition (P). But even when the
network is perfectly healthy, there's still a tradeoff between latency and
consistency — and CAP has nothing to say about that, because it's silent
on the common case. **PACELC** (Abadi, 2010) extends the idea: **if
Partitioned, choose Availability or Consistency; Else (normally
operating), choose Latency or Consistency.**

Concretely: a system doing synchronous replication to a remote-region
replica gets strong consistency, but every write pays the round-trip
latency to that region, partition or not. A system doing asynchronous
replication gets low write latency, but a read immediately after a write
might hit a replica that hasn't caught up yet — a consistency gap that
exists on a perfectly healthy network, with zero partitions in sight. This
is why "PC/EC" systems (like a strongly-consistent, synchronously-
replicated DB) and "PA/EL" systems (like DynamoDB in its original
eventually-consistent mode) both exist and are both reasonable
engineering choices — the letter after E is often the more *frequently
felt* tradeoff, since partitions are rare but every single request pays
the latency/consistency cost.

## Key takeaways

- CP examples: payment ledgers, systems needing strict correctness over
  uptime during a partition. AP examples: DNS, distributed caches, most
  chat/social apps — availability and responsiveness matter more than a
  momentarily stale read.
- Real systems often mix policies per operation (a chat app can be AP for
  delivery and CP-ish for ordering within a thread) rather than choosing
  one label for the whole system.
- PACELC generalizes CAP: even with no partition, you still trade latency
  against consistency on every request, because synchronous
  strongly-consistent replication is slower than async replication by
  construction.
- When evaluating any real system's CAP posture, ask two separate
  questions: "what happens during a partition?" (CAP) and "what's the
  latency/consistency tradeoff during normal operation?" (PACELC).
""",
        ),
    ],
    "replication": [
        LessonModule(
            title="Leader-follower replication mechanics",
            content=r"""
## Why replicate at all

Replication exists for two largely independent reasons: **durability and
availability** (don't lose data or serving capacity if one machine dies)
and **read scalability** (spread read traffic across multiple copies).
Leader-follower (a.k.a. primary-replica, master-slave) replication is the
dominant pattern because it gives a simple answer to the hardest question
in replication — "who resolves conflicting writes?" — by having exactly
one node, the leader, accept all writes. Followers only ever apply writes
that came from the leader, in the order the leader applied them, so there
is never a genuine conflict to resolve.

## The mechanics

The leader appends every write to its own storage and to a **replication
log** (in Postgres, the WAL; in MySQL, the binlog). Followers connect to
the leader, stream that log, and apply each entry to their own copy of
the data in the same order. A follower is, conceptually, replaying the
leader's history with some delay.

## Synchronous vs asynchronous replication

This is the single most consequential configuration knob in a replicated
system, because it's a direct trade of **write latency vs durability
guarantees**.

**Synchronous replication:** the leader waits for at least one follower
to confirm it has received (and often applied) the write before telling
the client the write succeeded. This guarantees that a confirmed write
survives the leader crashing immediately afterward — the follower already
has it. The cost is that every write's latency includes a round trip to
the follower, and if that follower is slow or unreachable, writes stall
or fail entirely (the leader can't safely say "done" without the
follower's ack).

**Asynchronous replication:** the leader confirms the write to the client
immediately, then sends it to followers in the background. Write latency
is just local disk (or local commit), regardless of follower health. The
cost: if the leader crashes before the follower receives the write, that
write is gone — the client was told it succeeded, and it's now
unrecoverable. This is the central tension of the failover discussion in
the next module.

Most production systems land on a middle ground: **one synchronous
follower plus N asynchronous ones** (Postgres calls this
`synchronous_standby_names`). You get a durability guarantee (at least one
up-to-date copy exists) without paying the full latency cost of waiting
for every replica.

## Replication lag

Because most followers apply the log asynchronously, they are, at any
given instant, some amount of time *behind* the leader — replication lag.
Under normal load this might be milliseconds; under load spikes,
long-running transactions, or network hiccups it can grow to seconds or
minutes. Lag isn't a bug to be eliminated — it's an inherent property of
async replication — but it produces concrete, user-visible correctness
problems if you're not careful about which queries go to which replica.

## Read-your-writes

**The problem:** a user submits a comment (write goes to the leader),
then the page reloads and fetches the comment list from a follower. If
that follower hasn't caught up yet, the user's own comment is missing —
even though *they* just wrote it a second ago. This is jarring
specifically because it violates something users intuitively expect: you
should always be able to see your own actions.

**Common fixes:** route reads for a user's own recently-written data to
the leader for some time window after they write (e.g. "read from leader
for 1 second after any write from this user"); track a log position or
timestamp with the write and require the follower serving the read to
have caught up past it; or simply always route a given user's reads to
the same replica they last wrote through, tracked via a sticky session.

## Monotonic reads

**The problem:** a user refreshes a page twice in a row. The first
request happens to land on a follower that's fully caught up; the second
lands on a *different* follower that's lagging further behind. The user
sees data, refreshes, and sees *older* data than before — time appears to
move backwards. This is possible any time reads are load-balanced across
multiple followers with independent, differing lag.

**Common fix:** ensure a given user's reads are consistently routed to
the *same* replica (e.g. hash the user/session ID to pick a replica) so
that, even if that replica is behind the leader, it is at least
monotonically catching up rather than jumping between arbitrary points in
history.

## Key takeaways

- Leader-follower replication resolves the write-conflict problem by
  construction: only the leader accepts writes, so there's only ever one
  order of truth to replay.
- Synchronous replication trades write latency for a durability guarantee
  (a confirmed write survives leader failure); asynchronous replication
  trades that guarantee for lower, follower-independent write latency.
  Most systems mix both: one sync follower, N async ones.
- Replication lag is inherent to async replication, not a defect — but it
  causes real, user-visible bugs: read-your-writes violations (your own
  write appears missing) and monotonic-read violations (data appears to
  go backwards on refresh).
- Both problems are usually fixed at the routing layer — pinning a user's
  reads to the leader briefly after a write, or pinning them to a single
  consistent replica — not by eliminating lag itself, which is generally
  not eliminable without paying full synchronous-replication cost.
""",
        ),
        LessonModule(
            title="Failover",
            content=r"""
## What failover is solving

If the leader in a leader-follower setup dies, the system needs a new
leader, fast, or every write stops. **Failover** is the process of
detecting the leader is gone, promoting a follower to take its place, and
getting clients to send writes to the new leader instead. Each step has
sharp edges.

## Detection: heartbeats and the false-positive problem

Nodes typically detect leader failure via **heartbeats** — the leader (or
a separate coordination service) periodically signals "I'm alive," and if
that signal is missing for longer than some timeout, the leader is
presumed dead. The core difficulty is that a network hiccup and an actual
crash look identical from a follower's point of view: both present as
"no heartbeat received." Set the timeout too short and you get false
positives — failing over away from a leader that was merely slow (a GC
pause, a brief network blip), which is disruptive and sometimes
dangerous. Set it too long and a real outage causes an unnecessarily long
write-unavailability window. There's no timeout that's simply "correct" —
it's a tuned tradeoff between failover speed and false-positive rate.

## Split-brain

The dangerous failure mode: a network partition separates the old leader
from the rest of the cluster, but the old leader is still running and
still *thinks* it's the leader (it just can't reach anyone). Meanwhile,
the majority side of the cluster, unable to reach the old leader, promotes
a follower to be the new leader. Now there are **two leaders simultaneously
accepting writes** — split-brain — and their data sets diverge with no
principled way to reconcile them later; if the same key was written on
both sides, one write is simply lost or silently overwritten upon
reconciliation.

The standard defense is requiring a promotion to be approved by a
**majority (quorum)** of the cluster's nodes, not just any single node
deciding unilaterally. A minority-side old leader, unable to reach a
majority, should recognize it no longer holds quorum and step down
(demote itself, refuse writes) rather than keep acting as leader. This is
precisely the problem consensus algorithms like Raft (see the
`consensus-algorithms` competency) are built to solve rigorously —
ad hoc heartbeat-based failover without a quorum requirement is exactly
where split-brain bugs live.

## Promotion and client redirection

Once a new leader is chosen, two more things must happen before the
system is actually healthy again:

1. **The new leader must be caught up (or made canonically correct).** If
   multiple followers are candidates, the one with the most complete
   replication log is usually chosen, and any other followers that had
   applied writes the new leader never saw must reconcile — typically by
   discarding their divergent tail and re-syncing from the new leader.
2. **Clients (and other followers) must discover the new leader.** This
   usually happens through one of: a proxy/router layer that clients
   always talk to (so the redirect is invisible to them), a DNS or virtual
   IP that gets repointed at the new leader, or a coordination service
   (ZooKeeper, etcd, Consul) that holds the current leader's identity and
   that clients/followers watch for changes. Until this propagates, some
   clients may still be sending writes to the old leader's address and
   getting errors or timeouts.

## What can go wrong: lost writes from promoting a lagging async replica

This is the sharpest edge case, and it's a direct consequence of the
sync-vs-async tradeoff from the previous module. If the dead leader was
using **asynchronous** replication, its followers may each be missing some
of its most recent writes — and different followers may be missing
*different* writes, depending on exactly how far each had caught up. If
the follower chosen for promotion wasn't the most up-to-date one (or even
if it was, it can still be behind the leader's actual last commit), those
writes are gone: the leader told clients they succeeded, but no surviving
node has them. This is a real, accepted risk of async replication — it's
not a bug in the failover process, it's the failover process correctly
doing its job on top of a fundamentally lossy replication strategy. The
mitigation is the sync-follower configuration from the previous module: if
at least one follower is synchronously up to date, promoting *that*
follower specifically (not an arbitrary one) avoids the loss.

## Key takeaways

- Failover requires: detecting leader failure (heartbeats, inherently a
  tuned tradeoff between speed and false positives), promoting a replica,
  and getting clients to find the new leader (proxy, DNS, or a
  coordination service).
- Split-brain — two nodes both believing they're leader after a partition
  — is the most dangerous failure mode; the standard defense is requiring
  a quorum/majority to authorize a promotion, and requiring a minority-side
  old leader to self-demote.
- Promoting a follower that was behind on asynchronous replication loses
  whatever writes it hadn't received yet — writes the client was already
  told succeeded. This is why systems that can't tolerate any write loss
  use at least one synchronous follower as the promotion candidate.
- Ad hoc failover logic without a formal quorum requirement is exactly the
  gap that consensus algorithms (Raft, Paxos) are designed to close.
""",
        ),
    ],
    "partitioning-sharding": [
        LessonModule(
            title="Sharding strategies",
            content=r"""
## Why shard

Replication solves durability and read scaling — every replica holds the
*full* dataset. Sharding (partitioning) solves a different problem: the
dataset, or the write throughput it needs, no longer fits on one machine
at all. Sharding splits the data itself across nodes, so each node holds
only a slice, and the system as a whole can hold (and write) far more
than any single node could alone. The central design decision is the
**shard key** — the field used to decide which shard a given row lives on
— and the strategy for mapping keys to shards.

## Hash-based sharding

Compute `hash(shard_key) % num_shards` (or, better, map the hash into a
fixed set of buckets that are then assigned to nodes — see consistent
hashing below) and route the record to that shard.

**Strength:** distributes data (and therefore load) close to uniformly
across shards, because a good hash function scatters keys evenly
regardless of the input distribution. There's no such thing as a "hot"
range under normal hash sharding — keys that are logically adjacent (e.g.
consecutive user IDs) land on essentially random, unrelated shards.

**Weakness:** you lose the ability to do efficient **range scans**. "Give
me all orders placed between March 1 and March 15" requires touching
every shard, because a hash function deliberately destroys any ordering
relationship between keys — there's no way to know in advance which
shards contain records in that date range.

## Range-based sharding

Assign contiguous ranges of the shard key to each shard — shard 1 holds
keys A–H, shard 2 holds I–P, and so on (this is how early Bigtable/HBase-
style systems and many time-series databases partition).

**Strength:** range queries are efficient — "give me everything from March
1–15" can go directly to the one or two shards that own that range,
without fanning out to every node.

**Weakness:** **hot shards**. If the shard key correlates with request
volume or write recency — which it very often does — one range absorbs
disproportionate traffic. The textbook case: sharding a time-series table
by timestamp range means *all* current writes land on the single shard
that owns "now," while every other shard, holding only historical data,
sits comparatively idle. The system has N shards worth of capacity but is
bottlenecked on one.

## Directory-based sharding

Maintain an explicit lookup table (a directory service) mapping each
shard key — or each range of keys — to the physical shard that holds it,
rather than computing the mapping algorithmically from a hash or range
function.

**Strength:** maximum flexibility. You can rebalance by moving individual
keys or arbitrary groups of keys between shards and simply updating the
directory — no formula constrains what can live where. This makes it
easy to isolate a single unusually large or hot tenant onto its own
dedicated shard, something neither pure hash nor pure range sharding does
cleanly.

**Weakness:** the directory itself becomes a critical dependency — every
request needs a lookup against it before it can even find the right
shard, adding latency and a new single point of failure/bottleneck unless
the directory is itself made highly available and heavily cached. It's
also more operational machinery to build and keep correct.

## Re-sharding cost — the problem that cuts across all three

Whatever the strategy, at some point you add or remove shards, and data
has to move. With naive `hash(key) % N` sharding, changing N from 4 to 5
changes the target shard for the *overwhelming majority* of keys
simultaneously — nearly the entire dataset has to be reshuffled at once,
which is operationally brutal at any real scale (the system is often
under-provisioned exactly because it's approaching this threshold, so
this is the worst possible moment to be moving most of the data around).

Range sharding re-shards more gracefully in principle (split one range
into two), but still requires careful, monitored data migration and
temporary dual-routing during the move. Directory-based sharding
re-shards most gracefully of all — move a subset of directory entries — at
the cost of the directory infrastructure described above.

## Key takeaways

- Hash sharding: near-uniform load distribution, but range scans require
  fanning out to every shard because ordering is deliberately destroyed.
- Range sharding: efficient range scans, but prone to hot shards whenever
  the key correlates with recency or popularity (the classic case:
  sharding by timestamp concentrates all current writes on one shard).
- Directory-based sharding: maximum rebalancing flexibility and the
  ability to isolate hot keys/tenants, at the cost of an extra
  lookup hop and a directory service that must itself be highly available.
- Naive modulo-based hash sharding re-shards catastrophically (`% N` to
  `% (N+1)` moves almost everything) — this is exactly the problem
  consistent hashing exists to solve, covered in the next module.
""",
        ),
        LessonModule(
            title="Choosing a shard key in practice",
            content=r"""
## Worked example: a multi-tenant SaaS product

Say you're building a project-management SaaS — many companies
("tenants"), each with users, projects, tasks, and comments. The natural
shard key candidates are `tenant_id`, `user_id`, or some derived
per-record ID. This is a genuinely common, realistic design decision, and
walking through it surfaces most of the tradeoffs that show up in
practice.

**Sharding by `tenant_id`:** every row belonging to a given company lands
on the same shard. This is usually the right default for multi-tenant
systems, for a specific reason: almost every query a tenant's application
issues is already scoped to that tenant ("show me *this company's*
projects," "list *this company's* tasks") — so `tenant_id`-sharding means
the overwhelming majority of queries can be routed to, and satisfied
entirely within, a single shard. The main risk is skew: a handful of
enterprise customers can be orders of magnitude larger (more users, more
data, more query volume) than the median tenant, producing hot shards
that mirror the range-sharding hot-shard problem from the previous
module — mitigated by giving oversized tenants their own dedicated
shard (which is exactly the flexibility directory-based sharding is good
at).

## What breaks once you shard

**Cross-shard joins.** A query that needs to join data living on
different shards — e.g. "find all comments by users at companies using
plan X," if plan data and comment data land on different shards — can no
longer be expressed as a single SQL join executed by the database engine.
It has to be done in application code: query one shard, take the results,
query the other shard(s) with those results as a filter, and join in
memory. This is slower, more code, and loses the database's query
planner/optimizer entirely.

**Multi-row/multi-shard transactions.** ACID transactions are a
single-node (or, at best, a Paxos/Raft-coordinated multi-node)
guarantee. A transaction that needs to atomically update rows on two
different shards either requires a **distributed transaction protocol**
(two-phase commit — meaningfully slower and more failure-prone than a
local transaction) or has to be redesigned to avoid needing atomicity
across shards at all (e.g. via eventual consistency plus a
compensating-action pattern, or by choosing a shard key that keeps
related rows that need to be transactionally consistent together on one
shard in the first place — which is the strongest argument for
`tenant_id`-based sharding above: keeping a tenant's data on one shard
means nearly all of that tenant's transactions stay single-shard).

**Secondary indexes.** An index on a non-shard-key column (e.g. "find the
task with this specific external ticket ID," regardless of tenant) can no
longer be a simple local index, because the matching row could be on any
shard. The two standard fixes are a **local secondary index** per shard
(fast to write, but a lookup requires fanning out to query every shard)
or a **global secondary index** maintained as its own separately-sharded
structure keyed by the indexed column (fast, targeted lookups, but the
index itself now needs its own replication/consistency story and lags
behind writes to the primary data, similar to the replication-lag
problem).

## Re-sharding without the "move everything at once" problem: consistent hashing

**Consistent hashing** solves the re-sharding catastrophe from the
previous module. Instead of `hash(key) % N`, map both shards and keys onto
points on a fixed, large hash ring (e.g. 0 to 2^32−1). A key belongs to
the first shard whose position on the ring is at or after the key's hash
position, walking clockwise. Adding a new shard means picking a position
for it on the ring and moving only the keys that fall between it and the
next shard counter-clockwise — a small, bounded fraction of the total
keyspace (roughly `1/N` of the data, not nearly all of it). This is the
technique behind DynamoDB's, Cassandra's, and many CDNs' partitioning
layer specifically because it makes elastic scaling (adding/removing
nodes) an incremental, low-blast-radius operation instead of a full
dataset migration. A common refinement is **virtual nodes** — each
physical shard owns many small positions scattered around the ring rather
than one — which smooths out load distribution further and makes adding
or removing a single physical shard redistribute load evenly across all
the *remaining* shards rather than dumping it all on one neighbor.

## Key takeaways

- In multi-tenant systems, sharding by tenant ID is usually the right
  default because it keeps the vast majority of real queries and
  transactions confined to a single shard — the strongest practical
  argument for a shard key isn't "spreads data evenly," it's "matches how
  data is actually queried and transacted together."
- Sharding breaks cross-shard joins (must be done in application code) and
  multi-row transactions across shards (need 2PC or a redesign to avoid
  needing cross-shard atomicity) and complicates secondary indexes (local
  index + fan-out, or a separately-maintained global index).
- Consistent hashing fixes the catastrophic re-sharding problem of naive
  modulo hashing: adding or removing a shard moves roughly `1/N` of the
  keys, not nearly all of them.
- Virtual nodes (each physical shard owning many ring positions) smooth
  out load distribution and spread rebalancing load across all remaining
  shards when one is added or removed.
""",
        ),
    ],
    "consensus-algorithms": [
        LessonModule(
            title="Why consensus is hard, and what Raft guarantees",
            content=r"""
## The problem consensus actually solves

Consensus is the problem of getting a set of nodes, some of which may
crash or become unreachable, to agree on a single value — and, more
usefully in practice, to agree on a single, totally-ordered *sequence* of
values (a replicated log), such that every node that applies the log ends
up in the same state. This sounds almost trivial to state and is
notoriously hard to get right, because a correct consensus protocol has
to keep working correctly through crashes, message loss, message
reordering, message duplication, and network partitions, without ever
letting two nodes disagree about a decision that's supposed to be final.
Early attempts either weren't actually correct under all these failure
modes, or were correct but described so abstractly (Paxos, in its
original 1998 paper, is famous for this) that implementers routinely got
subtly wrong. Raft (Ongaro and Ousterhout, 2014) was explicitly designed
as "Paxos, but understandable" — same guarantees, decomposed into
separable, explainable sub-problems.

## What "solving consensus" buys you

If you have a working consensus protocol, you can build a **replicated
state machine**: every node applies the same sequence of commands in the
same order, so every node ends up in the same state, and the system keeps
working (keeps making progress) as long as a *majority* of nodes are
up and can talk to each other — even though any specific node, including
whichever one is currently "in charge," can crash at any time without the
system losing data or availability. This is a fundamentally stronger
guarantee than ordinary leader-follower replication (covered in the
`replication` competency) provides on its own — plain async leader-
follower replication has no principled answer to "what if the leader
dies mid-write and multiple followers disagree about what happened," and
that gap is precisely where split-brain bugs come from. Consensus
protocols are how you close that gap rigorously instead of papering over
it with heuristics.

## Raft, conceptually: three sub-problems

Raft decomposes consensus into three pieces that are individually simple:
**leader election**, **log replication**, and **safety**.

### Leader election

At any time, every node in a Raft cluster is in one of three states:
*follower*, *candidate*, or *leader*. Time is divided into **terms** —
monotonically increasing integers, each term having at most one leader.
A follower that hasn't heard from a leader within a randomized election
timeout assumes the leader is gone, increments its term, becomes a
candidate, and requests votes from every other node. A node grants its
vote to at most one candidate per term, on a first-come basis (and only
if the candidate's log is at least as up to date as its own — this detail
matters for safety, below). A candidate that receives votes from a
**majority** of the cluster becomes leader for that term and starts
sending periodic heartbeats to suppress new elections.

The randomized timeout is a small but important design detail: if every
follower waited exactly the same duration, they'd all become candidates
simultaneously and split the vote every single time, potentially
repeatedly. Randomizing the timeout window makes one node almost always
notice first and win the election before others even start.

### Log replication

Once elected, the leader is the only node that accepts new commands from
clients. It appends each command to its own log, then sends it to every
follower in parallel (this looks like the leader-follower log-shipping
from the `replication` competency, but with a critical addition: the
leader only tells the client the command succeeded — "commits" it — after
a **majority** of nodes, including itself, have durably stored it in
their logs). That majority requirement is what makes the guarantee real:
even if the leader crashes immediately after committing, at least one
node in any future majority necessarily has that entry, because any two
majorities of the same cluster must overlap by at least one node.

### Safety

The election rule mentioned above — a candidate can only win a vote from
a node whose log is *at least as up to date* as the candidate's own —
guarantees that whoever wins an election already has every command that
was ever committed by a previous leader. This is what prevents a stale,
behind node from getting elected and silently "forgetting" committed
data — a new leader is safety-constructed, by the voting rule itself, to
never be missing anything the cluster has already agreed on.

## Key takeaways

- Consensus solves the general problem of getting nodes to agree on an
  ordered sequence of values despite crashes and network failures — it
  underlies replicated state machines that stay correct and available as
  long as a majority of nodes are healthy.
- Raft splits the problem into leader election (terms, randomized
  timeouts, majority votes), log replication (leader appends, only
  commits after a majority durably stores an entry), and safety (a
  candidate can only win if its log is at least as up to date as a
  majority's, guaranteeing no committed data is ever lost by a new
  leader).
- The majority-overlap property — any two majorities of the same cluster
  share at least one node — is the mathematical fact that makes "commit
  after a majority acknowledges" a real durability guarantee, not just a
  heuristic.
- Ordinary async leader-follower replication has no principled defense
  against split-brain; consensus protocols exist specifically to make
  that guarantee rigorous rather than best-effort.
""",
        ),
        LessonModule(
            title="Raft edge cases and where consensus shows up in practice",
            content=r"""
## Split votes

If more than one follower's election timeout expires at nearly the same
moment, multiple candidates can request votes in the same term
simultaneously, and the cluster's votes can split among them so that no
single candidate reaches a majority. Raft's answer isn't to prevent this
outright — it accepts that split votes will occasionally happen — but to
recover from it quickly: if no candidate wins before timeouts expire
again, every candidate restarts its own randomized timeout and tries
again in a new (higher) term. Because timeouts are randomized per node,
a split vote resolving on the very next round is overwhelmingly likely —
in practice this shows up as a barely-perceptible extra delay, not a
stall.

## Network partitions

Suppose a 5-node cluster splits into a 3-node group and a 2-node group.
The 3-node side can still elect a leader (it has a majority) and continues
accepting and committing writes normally. The 2-node side cannot elect a
leader — it can't reach a majority — so it cannot commit new writes; at
most, an old leader stranded in that minority keeps thinking it's in
charge but can no longer get any new entry acknowledged by a majority, so
nothing it does can actually commit. When the partition heals, that
stale leader discovers a higher term number from the majority side,
recognizes it's no longer current, and steps down to follower, discarding
any uncommitted entries it had accumulated in isolation. This is Raft's
version of the split-brain defense described in the `replication`
competency's failover module — but here it's a designed-in, proven
protocol invariant, not an operational heuristic layered on top.

## Why consensus is expensive — and why you don't reach for it by default

Every write that needs to be durably committed under Raft requires a
network round trip to a majority of nodes *before* the client gets an
acknowledgment — inherently more latency than a single-node write, and
meaningfully more than async leader-follower replication (which
acknowledges immediately, at the cost of the durability gap covered in
the `replication` competency). A 5-node Raft cluster also means every
write is durably stored on at least 3 nodes, using more storage and
network bandwidth than a system with a single source of truth. And the
operational complexity is real: cluster membership changes, log
compaction/snapshotting so the log doesn't grow forever, and tuning
election timeouts for your actual network's latency characteristics are
all nontrivial to run correctly. The rule of thumb: reach for a
consensus-backed system only when you specifically need strong
consistency and safe automatic failover *across multiple nodes* — not as
a default replication strategy for data that could tolerate eventual
consistency or a simpler primary/standby setup with manual failover.

## Where consensus shows up in real infrastructure

You rarely implement Raft or Paxos yourself — you consume a system that
already has, using it as a building block for a narrower problem:

- **etcd** (Raft-based) is the coordination store behind Kubernetes — it's
  how the cluster agrees on a single, consistent view of desired and
  actual state across every control-plane node, and it's why `etcd` being
  unhealthy takes the whole cluster's control plane down with it.
- **ZooKeeper** (uses its own protocol, ZAB, which is Paxos-like) plays
  the equivalent role for older distributed systems — Kafka historically
  used it to elect a controller broker and track partition leadership
  before Kafka replaced it with its own Raft-based (KRaft) implementation.
- **Distributed locks.** "Only one process should run this cron job/hold
  this resource at a time across N machines" is a consensus-shaped
  problem — a distributed lock built on a consensus store (etcd, ZooKeeper,
  or Consul) can guarantee at most one holder even during network
  partitions and node crashes, which a naive "write a row to a shared
  database and check for it" approach cannot, because that naive approach
  has no principled answer to a partition splitting the checker from the
  writer.
- **Leader election for your own services.** If you're building a system
  where exactly one instance should be "active" at a time (e.g. a
  singleton job scheduler, an active/passive failover pair), the correct
  building block is a consensus-backed leader-election primitive (most
  commonly implemented on top of etcd or ZooKeeper) rather than hand-
  rolling heartbeat-and-timeout logic — that hand-rolled logic is exactly
  where the split-brain and split-vote edge cases above tend to
  resurface, un-solved, in a bespoke and less-tested form.

## Key takeaways

- Split votes are expected and self-correcting via randomized re-election
  timeouts; network partitions leave only the majority side able to
  commit writes, and a stranded minority leader safely steps down once it
  observes a higher term after the partition heals.
- Consensus is expensive by design — every commit needs a majority round
  trip — so it's a deliberate choice for problems that specifically need
  strong cross-node consistency and safe automatic failover, not a
  default replication strategy.
- In practice, you consume consensus through etcd, ZooKeeper (or ZAB/
  KRaft), not by implementing Raft yourself.
- Distributed locks and leader election for your own services are
  consensus-shaped problems — building them on a consensus-backed
  primitive avoids reintroducing split-brain and split-vote bugs that a
  hand-rolled heartbeat/timeout scheme will eventually hit.
""",
        ),
    ],
}
