"""Lesson content for the Interview Preparation subject.

Module count per competency tracks real topic complexity — coding-interview-
patterns and system-design-interviews and behavioral-interviews each get
enough modules to cover their distinct sub-skills, while technical-
communication is narrow enough for one focused module. See
app.seeds.lessons.types.LessonModule.
"""

from app.seeds.lessons.types import LessonModule

LESSONS: dict[str, list[LessonModule]] = {
    "coding-interview-patterns": [
        LessonModule(
            title="Two Pointers and Sliding Window",
            content=r"""
## The pattern

Two pointers is an index-manipulation technique: instead of nested loops
(O(n²)), you walk one or two indices across a sequence in a single pass,
moving them based on a condition instead of independently. Sliding window
is the specific case where the two pointers mark the boundaries of a
contiguous subrange, and you grow/shrink that range as you scan.

Both patterns exist because the brute-force instinct for "find a pair" or
"find a subarray with property X" is to check every pair or every
subarray — O(n²) or worse. Two pointers exploits structure (sortedness,
or a monotonic relationship between window size and the property you're
checking) to collapse that to O(n).

## When it applies

- **Two pointers (opposite ends)**: the input is sorted, and you're
  looking for a pair/triple satisfying a sum or difference condition.
  Example: "two sum" on a *sorted* array, "three sum", "container with
  most water."
- **Two pointers (same direction / fast-slow)**: linked list cycle
  detection, removing duplicates in place, partitioning.
- **Sliding window**: the problem is about a *contiguous* substring or
  subarray, and the property you're tracking (sum, count of distinct
  characters, longest run without a violation) changes predictably as
  you add/remove one element at a time.

The tell in the problem statement: words like "subarray," "substring,"
"contiguous," or a sorted-array constraint plus a pair/sum requirement.

## Worked example: longest substring without repeating characters

Given a string, find the length of the longest substring with no
repeated characters.

Brute force: check every substring, O(n³) (O(n²) substrings, O(n) to
check each for duplicates). Sliding window gets this to O(n).

```python
def length_of_longest_substring(s: str) -> int:
    last_seen: dict[str, int] = {}  # char -> most recent index
    window_start = 0
    longest = 0

    for window_end, char in enumerate(s):
        # If char is in the current window, jump window_start past its
        # last occurrence. max() guards against jumping backwards when
        # the stored index is stale (outside the current window).
        if char in last_seen and last_seen[char] >= window_start:
            window_start = last_seen[char] + 1

        last_seen[char] = window_end
        longest = max(longest, window_end - window_start + 1)

    return longest


# "abcabcbb" -> 3 ("abc")
# "bbbbb"    -> 1 ("b")
# "pwwkew"   -> 3 ("wke")
```

Walk through `"abcabcbb"`: the window grows to `"abc"` (length 3), then
hits the second `a` at index 3 — `last_seen["a"] = 0 >= window_start (0)`,
so `window_start` jumps to 1. The window is now `"bca"`, still length 3.
It never needs to shrink one character at a time; it jumps directly past
the duplicate.

## Complexity analysis

- **Time**: O(n) — `window_end` visits each character once; `window_start`
  only ever moves forward, so across the whole run it also advances at
  most n times. Two pointers, each monotonic, each bounded by n, gives
  O(n) total even though it looks like nested iteration.
- **Space**: O(min(n, alphabet size)) for `last_seen` — bounded by the
  character set (e.g. O(1) for ASCII), not by input length.

This is the general shape of the complexity argument for two
pointers/sliding window: each pointer moves monotonically and is bounded
by n, so even though there are "two loops," the total work is linear, not
quadratic. State that argument explicitly in an interview — "both
pointers only move forward, so total pointer movement is bounded by 2n" —
because it's the part that actually proves the O(n) claim rather than
just asserting it.

## Key takeaways

- Reach for two pointers when the input is sorted and you need a
  pair/sum condition; reach for sliding window when the problem is about
  a contiguous subarray/substring with a property that changes
  incrementally as the window moves.
- The complexity win comes from monotonic pointer movement — each pointer
  advances at most n times total, turning an apparent O(n²) scan into
  O(n). Say this out loud in an interview; don't just claim O(n).
- Track window state incrementally (a running sum, a count, a hash map of
  last-seen indices) instead of recomputing it from scratch on every
  window change — recomputing is what silently reintroduces the O(n²)
  you were trying to avoid.
- Common variants: fixed-size window (window size is given), variable-size
  window (grow until invalid, then shrink), and window with a frequency
  map (anagram/permutation-in-string problems).
""",
        ),
        LessonModule(
            title="Hash Maps for O(1) Lookup Tricks",
            content=r"""
## The core trick: "have I seen this before?"

A huge fraction of array/string interview problems reduce to one
question asked repeatedly: *have I already seen the value I need to pair
with the current element?* A hash map (Python `dict`/`set`) answers that
in O(1) average time, which is what turns an O(n²) nested-loop scan into
a single O(n) pass. This is the single highest-leverage trick in the
entire interview canon — recognize it and a large class of "medium"
problems becomes trivial.

## Worked example: two-sum (unsorted)

Given an array and a target, return the indices of two numbers that sum
to the target. Unlike the sorted two-pointer version, this array is in
arbitrary order.

Brute force: for each element, scan the rest of the array for its
complement — O(n²).

```python
def two_sum(nums: list[int], target: int) -> tuple[int, int]:
    seen: dict[int, int] = {}  # value -> index

    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return (seen[complement], i)
        seen[num] = i

    raise ValueError("no two sum solution")


# nums=[2, 7, 11, 15], target=9 -> (0, 1)  because 2 + 7 == 9
```

The insight: instead of asking "for this number, does its complement
exist anywhere in the array" (which requires scanning), you ask "have I
already recorded this number's complement while walking forward?" — and
a hash map lets you check membership in O(1) instead of O(n). One pass,
O(n) time, O(n) space.

## The general trade: space for time

This is the pattern underneath the trick, stated explicitly because
interviewers want to hear you articulate it, not just apply it: **you are
paying O(n) extra memory to avoid O(n) extra time per lookup.** Brute
force costs no extra space but re-scans on every element; the hash map
approach remembers what it's already seen so it never re-scans. When an
interviewer asks "can you do better than O(n²)?", the answer is almost
always "trade space for time with a hash map" unless the array is sorted
(then two pointers gets you O(n) with O(1) space instead — prefer that
when sortedness is available, since it avoids the extra memory).

## Frequency counting

The second major hash-map pattern: counting occurrences to answer
questions about distribution — anagrams, majority elements, first unique
character, grouping items by a derived key.

```python
from collections import Counter

def is_anagram(s: str, t: str) -> bool:
    return Counter(s) == Counter(t)


def first_unique_char(s: str) -> int:
    counts = Counter(s)
    for i, char in enumerate(s):
        if counts[char] == 1:
            return i
    return -1
```

`Counter` is a `dict` subclass — reach for it whenever the problem is
about *how many times* something occurs rather than *whether* it occurs.
Comparing two `Counter`s for equality (as in `is_anagram`) is itself an
O(n) operation that replaces what would otherwise be a sort-and-compare
(O(n log n)).

## When hash maps are the wrong tool

Worth naming so it doesn't sound like a hammer for every nail: if the
array is already sorted, two pointers gets the same time complexity with
O(1) space — no reason to pay for a hash map. If you need order
(nearest neighbor, range queries), a hash map's O(1) lookup doesn't help
because it doesn't preserve or expose ordering — a sorted structure
(array, balanced BST, sorted container) is the right tool there instead.

## Key takeaways

- The "have I seen this before" pattern turns an O(n²) nested scan into a
  single O(n) pass by trading O(n) space for O(1) average lookup time —
  state this trade-off explicitly in an interview.
- Two-sum on an unsorted array is the canonical example: build the seen
  set/map incrementally while scanning, check for the complement before
  inserting the current element.
- `Counter` (or a plain `dict` used as a tally) is the tool for frequency
  questions: anagrams, majority element, grouping, first-unique-element.
- Don't reach for a hash map when the array is sorted (two pointers is
  strictly cheaper) or when you need ordering/range queries (hash maps
  don't preserve order).
""",
        ),
        LessonModule(
            title="Trees and Graphs: BFS vs DFS",
            content=r"""
## Graphs are trees plus cycles

Conceptually, a tree is just a graph with no cycles and (usually) a
single root — every tree-traversal algorithm you already know (preorder,
inorder, postorder, level-order) is a graph-traversal algorithm with an
extra guarantee that you'll never revisit a node. The moment a graph
problem clicks in an interview, it's usually because you realize "this is
the tree traversal I know, plus a `visited` set to handle cycles." That
single addition — tracking visited nodes — is the entire conceptual delta
between tree algorithms and graph algorithms. Get comfortable with tree
BFS/DFS first; graphs are not a new topic, they're a two-line patch to
the same one.

## DFS: recursive vs iterative

Depth-first search goes as deep as possible along one branch before
backtracking. It's naturally recursive because the call stack *is* the
traversal stack.

```python
def dfs_recursive(node: TreeNode | None, visited: set[int]) -> None:
    if node is None or node.id in visited:
        return
    visited.add(node.id)
    process(node)
    for child in node.children:
        dfs_recursive(child, visited)
```

The iterative version makes the implicit call stack explicit, which
matters in an interview because recursion has a real limit (Python's
default recursion limit is 1000; a skewed tree/graph with 10,000 nodes
will blow it):

```python
def dfs_iterative(start: TreeNode) -> None:
    stack = [start]
    visited: set[int] = set()

    while stack:
        node = stack.pop()
        if node.id in visited:
            continue
        visited.add(node.id)
        process(node)
        for child in node.children:
            if child.id not in visited:
                stack.append(child)
```

Note `stack.pop()` (LIFO, from the end) — that's what makes it
depth-first. Swap it for BFS.

## BFS: level by level, using a queue

Breadth-first search explores all neighbors at the current depth before
moving deeper. It requires a queue (FIFO), not a stack:

```python
from collections import deque

def bfs(start: TreeNode) -> None:
    queue = deque([start])
    visited: set[int] = {start.id}

    while queue:
        node = queue.popleft()  # FIFO — this is what makes it breadth-first
        process(node)
        for child in node.children:
            if child.id not in visited:
                visited.add(child.id)
                queue.append(child)
```

The one-character difference between BFS and DFS-with-a-list — `pop()`
vs `popleft()` — is worth internalizing precisely because it's easy to
get backwards under pressure; say the word "queue" and "FIFO" out loud
while writing it to avoid transposing them.

## When each is the right choice

- **BFS**: shortest path in an unweighted graph (level-order distance
  from the start *is* the shortest path, because BFS finds nodes in
  strictly increasing distance order), "minimum number of steps"
  problems, finding all nodes within k hops, level-order tree traversal.
- **DFS**: exploring all paths (not just the shortest), detecting cycles,
  topological sort, connected components, backtracking problems
  (permutations, combinations, "can this be partitioned" questions),
  anything where you need to fully explore one branch before deciding
  whether to commit to it.

The single fastest way to pick correctly under pressure: if the question
contains "shortest" or "minimum steps/hops," default to BFS. If it
contains "all paths," "can you reach," or looks like a
backtracking/enumeration problem, default to DFS.

## Handling cycles — the graph-specific addition

Trees never need a `visited` set for correctness (you can't revisit a
node by walking down from the root). Graphs always do, unless the
problem explicitly guarantees acyclicity (e.g. a DAG for topological
sort). Forgetting `visited` on a graph problem is the single most common
interview bug — it turns a correct-looking DFS/BFS into an infinite loop
the moment the input graph has a cycle. State explicitly, before coding,
whether the input is a tree or a general graph, and add the `visited`
set as soon as it's the latter.

## Key takeaways

- A graph is a tree with the "no cycles" guarantee removed — the
  traversal logic is identical, the only addition is a `visited` set.
- DFS uses a stack (or recursion, which is a stack); BFS uses a queue.
  `pop()` (LIFO) vs `popleft()` (FIFO) is the entire mechanical
  difference.
- BFS finds shortest paths in unweighted graphs because it visits nodes
  in non-decreasing distance order; reach for it whenever the problem
  says "shortest" or "minimum steps."
- DFS is for exploring all paths, backtracking, cycle detection, and
  topological sort; reach for it whenever the problem says "all paths"
  or "can you reach."
- Always name upfront whether you're on a tree or a general graph — that
  decides whether you need a `visited` set, and skipping it on a cyclic
  graph is the most common bug in this whole category.
""",
        ),
    ],
    "system-design-interviews": [
        LessonModule(
            title="A Structure That Works in 45 Minutes",
            content=r"""
## Why structure matters more than knowledge here

System design interviews are graded on process, not on reciting the
"correct" architecture for a well-known system. There is rarely one
correct answer — there is a well-reasoned one and a scattershot one.
Candidates with strong technical knowledge fail these interviews
constantly by jumping straight to a diagram of Kafka and Redis before
anyone has agreed on what the system needs to do. The structure below
exists to prevent that failure mode, and interviewers are explicitly
watching for whether you follow it without being told to.

## Step 1: clarify requirements (5-10 minutes)

Two categories, and skipping either is a tell that you design by
instinct rather than by requirement:

- **Functional requirements**: what the system actually does, from the
  user's point of view. For "design a URL shortener": can users pick a
  custom alias? Do shortened URLs expire? Is there click analytics?
- **Non-functional requirements**: the qualities the system must have —
  and this is where scale lives. Explicitly ask: *how many users? how
  many requests per second? read-heavy or write-heavy? what's the
  acceptable latency? what's the consistency requirement (can reads be
  stale)?* Don't guess these — asking is itself part of what's graded,
  because a senior engineer knows requirements come from the
  conversation, not from assumption.

A strong opening sounds like: "Before I design anything, let me pin down
scope. Functionally, do we need custom short codes, or just
auto-generated ones? Do links expire? Non-functionally, what's the
expected scale — are we talking thousands or hundreds of millions of
URLs, and is this read-heavy (redirects) or write-heavy (shortening
requests)?"

## Step 2: back-of-envelope estimation (5-10 minutes)

Convert the requirements into numbers that will drive every design
decision that follows — this step is what separates "I know some
technologies" from "I can reason about capacity."

Worked example, continuing the URL shortener, assuming the interviewer
says: 100M new URLs created per month, 100:1 read-to-write ratio.

```
Writes (URL creations):
  100,000,000 / month
  ≈ 100,000,000 / (30 * 24 * 3600) seconds
  ≈ 39 writes/sec average

Reads (redirects), at 100:1 read:write ratio:
  ≈ 39 * 100 = 3,900 reads/sec average

Peak (assume 2-3x average for peak traffic):
  ≈ 100-120 writes/sec peak
  ≈ 8,000-12,000 reads/sec peak

Storage, assuming each record is ~500 bytes (URL + short code +
metadata) and we retain 5 years of writes:
  100M/month * 12 * 5 years = 6,000,000,000 records
  6,000,000,000 * 500 bytes ≈ 3 TB over 5 years

Bandwidth (read path), assuming a 500-byte redirect response:
  3,900 reads/sec * 500 bytes ≈ ~2 MB/sec average
```

These numbers directly justify design decisions later: 3,900 reads/sec
means a single well-indexed database read replica probably isn't enough
without caching; 3 TB over 5 years is small enough that storage cost
isn't a driving constraint, but it does rule out keeping everything in
memory on one machine. State the numbers, then say what they imply — the
implication is the part that's actually being graded, not the
arithmetic.

## Step 3: high-level design (15-20 minutes)

Now — and only now — draw boxes and arrows: client, load balancer, API
servers, cache, database, maybe a queue for async work. The discipline
here is to **justify every box** as you draw it, tying it back to a
requirement or a number from step 2, rather than listing technologies
because they're familiar:

- "Reads dominate 100:1, so I'll put a cache (Redis) in front of the
  database for the redirect path — that's the 3,900 reads/sec, and a
  cache absorbs the vast majority of that without hitting the DB."
- "For the ID generation, given we need uniqueness across multiple
  write servers without a central bottleneck, I'd use something like a
  counter service with pre-allocated ranges, or a base62 encoding of a
  distributed ID (e.g. Snowflake-style) rather than random generation
  with collision retries at this write volume."

Each sentence pattern is the same: *requirement/number -> component ->
why*. An interviewer following along should never have to ask "why did
you add that?" because you already said why before they had to ask.

## Key takeaways

- The structure is requirements (functional + non-functional/scale) ->
  estimation (QPS, storage, bandwidth) -> high-level design — in that
  order, every time, regardless of which system is being designed.
- Explicitly ask about scale; don't assume it. The number changes the
  design (a cache is optional at 10 reads/sec and mandatory at 10,000).
- Show the arithmetic for estimation out loud — the interviewer is
  grading the reasoning process, not just the final number.
- Justify every component in the high-level design by tying it back to a
  specific requirement or number — an unjustified box is a red flag,
  not a point scored.
""",
        ),
        LessonModule(
            title="Deep Dives and What Interviewers Are Actually Evaluating",
            content=r"""
## What's actually being graded

A system design interview is not graded on whether you reproduced the
"real" architecture of the system you were asked to design (few
candidates have seen the real one, and interviewers know that). It's
graded on: did you gather requirements before designing, can you
estimate capacity, can you produce a coherent high-level design, and —
this module's focus — can you go deep on a hard part and reason about
trade-offs the way someone who has actually operated systems in
production does. That last part is where seniority shows up most
clearly, and it's the part candidates with strong breadth but shallow
depth tend to fumble.

## Picking 1-2 components to go deep on

After the high-level design, a good interviewer will ask "which part do
you want to go deeper on?" or will steer you toward one themselves. The
mistake is trying to add depth everywhere in the time remaining —
spreading 15 minutes across five components gives you five shallow
paragraphs, none of which demonstrate real expertise. Pick the one or
two components where the interesting trade-offs actually live for *this*
system, and go deep enough to hit a genuine decision point.

For the URL shortener: the interesting depth is usually the ID-generation
strategy (how do you generate unique short codes across multiple
write-servers without a single point of contention?) or the caching
strategy (what's the eviction policy, what happens on a cache miss under
load, how do you handle a hot key if one URL goes viral?). The load
balancer configuration is almost never where the interesting depth is —
don't spend five minutes there because it feels like a safe, well-known
topic.

## Trade-off articulation

The single highest-signal sentence pattern in a system design interview
is: **"I chose X over Y because Z, and the cost of that choice is W."**
Every real engineering decision has a cost; naming it is what separates
someone who has shipped systems from someone reciting a tutorial.

Example, on the ID-generation deep dive:

> "I'd generate short codes with a counter-based approach — a central
> counter that hands out ranges of IDs to each write server, which then
> encodes them in base62. I chose this over random generation with
> collision checks because at our write volume, random generation means
> an increasing collision-retry rate as the keyspace fills up, and I'd
> rather pay a small amount of coordination complexity upfront than an
> unpredictable, worsening retry cost later. The cost of my approach is
> that the counter service is a new component I now need to keep highly
> available — if I get that wrong, it becomes a single point of failure
> for all writes, so I'd make it a small, replicated service with
> pre-allocated ranges to reduce how often it's even contacted."

Notice the shape: choice, reason, and — critically — the cost of the
choice, stated without being prompted. That last clause is what most
candidates omit, and it's usually the difference between a "meets bar"
and "exceeds bar" evaluation.

## Common failure modes

- **Jumping to a specific technology before establishing requirements.**
  Saying "I'll use Kafka" in the first two minutes, before anyone has
  discussed throughput, ordering needs, or consumer patterns, reads as
  pattern-matching rather than reasoning — even if Kafka turns out to be
  the right call. Earn the technology choice with a requirement first.
- **Not asking clarifying questions.** Silence in the first five minutes,
  followed by a fully-formed design, signals that the candidate designs
  from assumption rather than from stated needs — which is exactly the
  instinct that causes real over-engineering and mis-scoped systems on
  the job.
- **Over-engineering for scale that wasn't asked for.** Introducing
  sharding, multi-region active-active replication, and a message queue
  for a system the interviewer scoped at "10,000 users" is not
  impressive — it reads as an inability to right-size a solution to its
  actual requirements, which is a real and costly failure mode in
  production, not just an interview one.
- **Silence during the estimation step.** Doing the arithmetic in your
  head and only stating the conclusion denies the interviewer the
  reasoning they're there to evaluate — narrate the numbers as you
  produce them.

## Key takeaways

- Depth beats breadth in the deep-dive phase: pick one or two components
  where the real trade-offs live, and go deep enough to hit an actual
  decision point rather than skimming five components shallowly.
- Use the pattern "I chose X over Y because Z, and it costs W" — stating
  the cost unprompted is the strongest single signal of engineering
  maturity in this interview format.
- The most common failure modes are all versions of skipping the
  reasoning step: naming a technology before requirements exist, not
  asking clarifying questions, and over-engineering for unrequested
  scale.
- The interviewer is evaluating process (how you get to a design) far
  more than the specific final architecture — a well-reasoned "wrong"
  answer outperforms an unexplained "right" one.
""",
        ),
    ],
    "behavioral-interviews": [
        LessonModule(
            title="STAR Done Well",
            content=r"""
## The structure

STAR is a shape for a behavioral answer, not a script to recite
mechanically — interviewers who've heard a thousand robotic STAR answers
can tell the difference between someone following the shape naturally
and someone reading it off an internal checklist.

- **Situation**: the context, in 1-2 sentences. Enough to orient the
  listener — team size, what the project was, what was at stake — and
  no more. This is the part candidates most often over-invest in.
- **Task**: what specifically needed to happen, and often, what your
  specific responsibility was within it.
- **Action**: what *you* did — the decisions you made, the trade-offs you
  weighed, the specific steps you took. This is the longest part of a
  good answer, and it's the part most answers get wrong (see below).
- **Result**: the outcome, ideally with a concrete measure (time saved,
  incidents prevented, a metric that moved, a team practice that
  changed) and, when relevant, what you learned or would do differently.

## The most common failure mode: a vague, team-focused Action

The single most frequent way a STAR answer fails is that the Action
section describes what "we" did instead of what "I" did. An interviewer
asking a behavioral question is trying to evaluate *your* judgment,
*your* specific contribution, and *your* decision-making — not the
team's. An answer like "we realized the deployment was failing, so we
rolled it back and investigated" gives the interviewer nothing to
evaluate about the candidate specifically; it could have been said by
anyone on that team, including someone who did nothing.

Compare:

**Weak (team-focused, vague):**
> "Our service started throwing errors in production. We looked into it
> as a team, found the issue, and fixed it. After that we added better
> monitoring so it wouldn't happen again."

**Strong (specific, first-person Action):**
> "I was the first to notice the error rate spike on our dashboard — I
> paged myself in, and while others joined, I made the call to roll
> back the deploy rather than try to hotfix forward, because we didn't
> yet know the root cause and I didn't want to risk making it worse
> under time pressure. I then bisected the last three commits locally
> against a replay of the failing requests and found a null-handling
> bug in a refactored validation path. I wrote the fix, added a
> regression test for the specific null case, and afterward proposed —
> and built — an alerting rule on that specific error signature so
> we'd catch it in staging next time."

The strong version names specific decisions ("I made the call to roll
back rather than hotfix forward, because..."), specific technical
actions (bisecting commits, writing the regression test), and a
specific artifact of the result (the alerting rule). Every sentence
answers "what did *you*, specifically, do or decide" — even the parts
that involved a team ("others joined") are framed around your action
within that team, not the team's collective action.

## A useful test while preparing a story

For every sentence in your Action section, ask: *could a bystander who
was on the team but did nothing have said this same sentence about
themselves?* If yes, it's too vague — it's describing what happened to
the team, not what you did. Rewrite it to name the specific decision,
trade-off, or step that was yours.

## Result: be concrete, and don't skip the reflection

A result stated as "and it worked out well" is nearly as weak as a vague
Action. Prefer a number or a concrete change when you have one ("reduced
deploy-related incidents from roughly one a month to zero over the
following quarter"), and when the result includes a mistake or a
suboptimal outcome, say what you learned or would do differently —
interviewers often rate self-aware, honest results (including partial
failures) higher than a suspiciously perfect one.

## Key takeaways

- STAR is a shape, not a script — Situation and Task should be brief;
  Action should be the longest section and should be almost entirely
  about you, not "we."
- The dominant failure mode is a vague, team-attributed Action —
  interviewers can't evaluate judgment they can't see, and "we decided"
  hides exactly what they're trying to assess.
- Test each Action sentence with: "could someone who did nothing have
  said this about themselves?" If yes, make it more specific.
- End with a concrete Result — a number or an observable change — and
  don't be afraid to include what you learned, even from an imperfect
  outcome.
""",
        ),
        LessonModule(
            title="Building a Story Bank",
            content=r"""
## Why prepare stories instead of answers

Behavioral interviewers draw from a fairly small set of recurring themes
because those themes map to traits companies actually screen for:
handling conflict, operating under ambiguity or failure, taking
initiative without formal authority. Preparing five to eight real stories
that map cleanly onto these themes — rather than trying to improvise a
fresh answer to each specific question in the room — is what lets you
answer confidently under pressure, and it's a far more efficient use of
prep time than trying to anticipate exact question wording.

## The common themes, and what each is really probing for

- **Conflict with a teammate.** Not "tell me about a disagreement" as a
  trivia question — it's probing whether you can disagree productively,
  without either steamrolling people or avoiding necessary friction.
  Pick a story where the conflict was substantive (a technical
  direction, a scope trade-off) and where you can describe the specific
  steps you took to resolve it, not just that it "got resolved."
- **A production incident.** Probing judgment under pressure and
  ownership. The strongest incident stories show a clear decision
  process (rollback vs. forward-fix, how you triaged, who you looped in
  and when) and end with a systemic fix, not just a one-off patch —
  interviewers are listening for whether you improve the system, not
  just extinguish the fire.
- **A time you disagreed with a decision** (from a manager or the team).
  Probing whether you can voice dissent professionally and whether you
  can commit to a decision once made, even if you disagreed with it —
  this is the "disagree and commit" trait almost every company screens
  for in some form. A story that ends with you either escalating
  destructively or silently resenting the decision both read poorly;
  the strong version shows you making your case once, clearly, and then
  either changing the outcome or committing fully once the decision was
  made.
- **A failure and what you learned.** Probing self-awareness and growth.
  Pick a real failure — not a humblebrag disguised as one ("my flaw is
  I work too hard") — and be specific about the mechanism of the
  failure and the concrete change you made afterward (a new habit, a
  new check, a changed default) as a result.
- **Mentoring or leading without formal authority.** Probing whether you
  can influence and develop others when you're not anyone's manager —
  increasingly the actual day-to-day of a senior IC. A strong story
  names a specific person or situation, what you specifically did to
  help them grow or to align a group, and an observable outcome.

## Mapping your real experience to themes

Before an interview loop, list your last few years of real work and, for
each notable event, tag which theme(s) it could serve — many single
stories can flex across two or three themes with a different emphasis in
the Action/Result framing. A production incident story, told with
emphasis on how you convinced a skeptical teammate to try your fix, also
covers "conflict." The goal isn't memorizing a script per theme; it's
having 5-8 real events available so that whatever the interviewer's
specific question, you have a genuine, specific story to reach for
instead of improvising from scratch.

## Keeping answers tight: 2-3 minutes, not a narrative

The single most common pacing mistake is over-explaining the Situation —
spending ninety seconds on org-chart context and project history before
getting to anything the interviewer can actually evaluate. A useful
discipline while practicing: time yourself, and aim for Situation+Task
combined to take well under 30 seconds, leaving the bulk of 2-3 minutes
for Action and Result. If you notice yourself narrating background for
more than a few sentences, that's the signal to compress it — the
interviewer needs just enough context to understand why your actions
mattered, not a full project history.

A good practice loop: record yourself (or say it out loud) answering
each of your 5-8 story-bank stories, time it, and cut it down until it
consistently lands in the 2-3 minute range without losing the specific,
first-person Action content from the previous module — length should
come out of trimming Situation, never out of trimming Action.

## Key takeaways

- Prepare 5-8 real stories mapped to the recurring themes (conflict,
  incident, disagreement with a decision, failure/learning,
  mentoring/leading without authority) instead of improvising fresh
  answers to each question.
- Each theme is probing a specific trait — know what's actually being
  evaluated so you pick the story (and the emphasis within it) that
  demonstrates that trait, not just a story that's topically related.
- A single strong story often serves two or three themes depending on
  which part of it you emphasize.
- Keep answers to 2-3 minutes by compressing Situation/Task aggressively
  — practice with a timer, and cut length from context-setting, never
  from the specific Action detail.
""",
        ),
    ],
    "technical-communication": [
        LessonModule(
            title="Structuring a Technical Explanation Under Pressure",
            content=r"""
## Lead with the conclusion, not the derivation

The single highest-leverage habit for explaining anything technical
under interview pressure — or in a design review, an incident channel,
or a status update — is inverting the natural order in which you
*arrived* at the answer. Engineers naturally narrate chronologically:
here's what I considered, here's what I tried, here's what I ruled out,
and finally, here's what I chose. That order is how discovery happened,
but it is close to the worst possible order for *communicating* the
result, because it makes the listener hold a growing pile of ungrounded
context while waiting for the payoff.

Lead with the conclusion instead — the inverted pyramid used in
journalism: most important fact first, supporting detail after, in
decreasing order of importance. State the recommendation or the answer
in the first sentence, then justify it.

**Chronological (weak) ordering:**
> "So I looked at using a relational database first, but then I
> considered that we have a lot of write throughput, so I also looked at
> a couple of NoSQL options, and there's tradeoffs there around
> consistency, and eventually, given all that, I think we should go with
> Postgres with read replicas."

**Inverted-pyramid (strong) ordering:**
> "I'd recommend Postgres with read replicas. The two things driving that:
> our access patterns are relational — we join across orders and
> customers constantly — and our write throughput is well within what a
> single primary can handle, so we don't need to pay NoSQL's consistency
> trade-offs to get scale we don't yet need."

Same content, same conclusion — but the second version tells the
listener the answer in the first five seconds, so every sentence after
that lands as *support for a known conclusion* instead of *suspense
before an unknown one*. Under interview pressure, this ordering also
protects you: if you run out of time partway through, the listener
already has the important part.

## Name trade-offs explicitly instead of implying them

A frequent gap in otherwise-strong technical explanations: the trade-off
is real and was clearly considered, but it's never stated — it's only
implied by which option got chosen. Implying a trade-off asks the
listener to reconstruct your reasoning from the outcome; naming it
hands them the reasoning directly, and it's also simply more honest
about the fact that the chosen option isn't free.

**Implied (weaker):**
> "We went with eventual consistency for the read replicas."

**Explicit (stronger):**
> "We chose eventual consistency for the read replicas — the trade-off is
> that a client can briefly read stale data right after a write, but it
> buys us horizontal read scaling without the coordination cost of
> synchronous replication. Given our data (mostly read-heavy content
> that tolerates a few hundred milliseconds of staleness), that trade
> was worth making."

The explicit version does three things in three sentences: names the
choice, names the cost, and names why the cost was acceptable *for this
specific context*. That last clause matters — it signals the trade-off
was evaluated against the actual requirements, not applied as a
one-size-fits-all default.

## A concrete drill: record and review

The skill above is a communication habit, not a knowledge gap, which
means it's trained by rehearsal, not by reading about it. A drill that
works:

1. Pick a system you've actually built or worked on deeply.
2. Set a 2-minute timer and record yourself (phone voice memo is
   enough) explaining what it does and one non-obvious design decision
   in it, as if to a smart engineer who's never seen it.
3. Listen back and check for three specific things:
   - **Filler words and hedging** ("um," "so basically," "kind of,"
     "I guess") — count them. A high count under a 2-minute constraint
     usually means you hadn't actually decided on the structure before
     starting to talk; that's fixable by pausing 3 seconds before
     answering to mentally line up conclusion -> reasoning -> trade-off.
   - **Unclear jumps in logic** — a sentence that only makes sense if
     the listener already knows something you haven't said yet. These
     are usually invisible to the speaker (you know the missing context)
     and obvious to a fresh listener — which is why recording and
     replaying it catches them when just "thinking through the answer"
     silently does not.
   - **Whether the conclusion survives without the detail** — could
     someone who stopped listening after your first sentence still
     state your recommendation correctly? If not, you buried the lede
     and need to reorder.

Repeat with a different system every few days. The 2-minute constraint
is doing real work here: it forces the inverted-pyramid habit, because
there's no time budget left for a chronological narrative once you've
front-loaded the conclusion — the constraint makes the skill
unavoidable rather than optional.

## Key takeaways

- Lead with the conclusion or recommendation, then the reasoning — this
  is the inverted pyramid, and it protects you if you run out of time
  and gives the listener a frame for everything that follows.
- Name trade-offs explicitly ("I chose X, the cost is Y, that was
  acceptable because Z") instead of letting the listener infer them from
  which option you picked.
- Drill this with a 2-minute recorded explanation of a real system,
  reviewed for filler words, unstated logical jumps, and whether the
  conclusion is recoverable from just the first sentence.
- This is a rehearsed habit, not a knowledge gap — the fix is repeated,
  reviewed practice under a real time constraint, not reading more about
  communication.
""",
        ),
    ],
}
