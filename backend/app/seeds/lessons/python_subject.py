"""Lesson content for the Python subject.

Written for a senior engineer who is fluent in other languages (PHP,
JS/Node) but newer to idiomatic Python. The emphasis throughout is on *why*
something is the Pythonic way to do a thing, not on explaining what a
variable or a loop is. See app.seeds.lessons.types.LessonModule.
"""

from app.seeds.lessons.types import LessonModule

LESSONS: dict[str, list[LessonModule]] = {
    "python-fundamentals": [
        LessonModule(
            title="The data model: iteration, comprehensions, truthiness",
            content=r"""
## Python's data model is a protocol, not a type hierarchy

Coming from PHP or JS, "iterable" probably means "implements some Iterable
interface" or "has a `[Symbol.iterator]`." Python's version is similar in
spirit but leans much harder on **duck typing via dunder methods**: an
object is iterable if it defines `__iter__` (or, as a fallback, `__getitem__`
starting at index 0). There's no marker interface to implement — the
presence of the right method *is* the contract. This is the same idea
behind `len(obj)` calling `obj.__len__()`, `obj[key]` calling
`obj.__getitem__(key)`, and `for x in obj` calling `obj.__iter__()`. The
built-in functions are thin syntax over dunder method lookups.

```python
class CountdownRange:
    def __init__(self, start: int) -> None:
        self.start = start

    def __iter__(self):
        n = self.start
        while n > 0:
            yield n
            n -= 1


for n in CountdownRange(3):
    print(n)  # 3, 2, 1
```

No base class, no `implements Iterable`. `for` just calls `__iter__()` and
keeps pulling from whatever it gets back until `StopIteration`. This
matters practically: when you see `for x in thing`, `*thing`, or
`list(thing)` working on some object in a library you didn't write, the
object almost certainly just implements `__iter__` — there's no interface
to go hunting for in a type hierarchy.

## Comprehensions: not syntax sugar, a different mental model

A `for` loop with `.append()` describes *how* to build a list, step by
step. A comprehension describes *what* the list contains — it reads closer
to set-builder notation than to imperative iteration:

```python
# Imperative: how to build it
squares = []
for n in range(10):
    if n % 2 == 0:
        squares.append(n ** 2)

# Declarative: what it is
squares = [n ** 2 for n in range(10) if n % 2 == 0]
```

Both do the same work, but the comprehension is a single expression — it
can be a default argument, a dict value, an argument to another function,
without a temporary variable. It's also measurably faster in CPython
because the loop runs in a specialized bytecode path instead of repeated
attribute lookups for `.append`.

Dict and set comprehensions follow the same shape:

```python
by_id = {user.id: user for user in users}
unique_domains = {email.split("@")[1] for email in emails}
```

## When a comprehension hurts readability

The idiom breaks down once you nest logic past a certain point. This is
"clever," not "readable":

```python
# Don't do this
result = [
    transform(x)
    for sublist in nested
    for x in sublist
    if predicate(x)
    if another_predicate(x)
]
```

Two `for` clauses and two `if` clauses in one expression forces the reader
to mentally re-linearize it into nested loops anyway — at that point a
plain loop with named intermediate variables communicates better than a
one-liner that "wins" on line count:

```python
result = []
for sublist in nested:
    for x in sublist:
        if predicate(x) and another_predicate(x):
            result.append(transform(x))
```

A useful rule of thumb: one `for` and at most one `if` is almost always a
readability win; two `for` clauses or nested comprehensions are almost
always a readability loss. Optimize for what a reviewer can parse in one
pass, not for expression-golfing.

## Generator expressions: comprehensions without materializing memory

Swap `[...]` for `(...)` and you get a generator expression — lazy,
one-item-at-a-time, doesn't build the whole list in memory:

```python
total = sum(order.amount for order in orders if order.status == "paid")
```

This never creates an intermediate list of amounts; `sum` pulls one value
at a time. For anything feeding into `sum`, `any`, `all`, `max`, or another
single-pass consumer, prefer the generator expression over building a list
first — it's the same comprehension syntax, just without materializing
data you're about to throw away.

## Truthiness and idiomatic conditionals

Python's truthiness rules are broader than "falsy is 0/null/undefined
in JS": empty containers (`[]`, `{}`, `()`, `set()`), empty strings, and
`0`/`0.0` are all falsy, and this is leaned on heavily in idiomatic code:

```python
# Idiomatic
if not items:
    raise ValueError("no items to process")

# Not idiomatic (and subtly different — len() is a fine ADT check, but
# most Python reviewers read this as a translated-from-another-language tell)
if len(items) == 0:
    raise ValueError("no items to process")
```

One place this genuinely trips people up: `None` checks. `if not value:` is
true for `None`, but *also* for `0`, `""`, and `[]` — if zero or an empty
string is a legitimate value you need to distinguish from "absent," you
need `if value is None:`, not `if not value:`. This is a real bug source
when a function's return type is `int | None` and `0` is valid.

```python
def get_discount(order: Order) -> int | None: ...

discount = get_discount(order)
if not discount:        # BUG: treats a real 0% discount same as "no discount"
    discount = default_discount

if discount is None:    # correct: only "absent" triggers the default
    discount = default_discount
```

## Key takeaways

- Iteration, indexing, and length are protocols driven by dunder methods
  (`__iter__`, `__getitem__`, `__len__`) — not an interface hierarchy to
  look up.
- Comprehensions describe *what* a collection contains, not the steps to
  build it; prefer them for a single `for` + at most one `if`.
- Past that complexity, a plain loop is more readable — don't chase
  one-liners at the cost of a reviewer being able to parse the expression.
- Generator expressions (`(...)` instead of `[...]`) avoid materializing a
  throwaway list when the consumer only needs to iterate once.
- `if not value:` and `if value is None:` are **not** the same check —
  falsy-but-present values (`0`, `""`, `[]`) will silently take the "empty"
  branch under `not value`.
""",
        ),
        LessonModule(
            title="Context managers and the with statement",
            content=r"""
## What problem `with` actually solves

In PHP or Node you're used to `try/finally` (or `using`-style patterns in
other languages) to guarantee cleanup — closing a file handle, releasing a
lock, rolling back a transaction — even if the code in between raises. The
`with` statement is Python's dedicated syntax for exactly that pattern,
and it's used pervasively: files, DB sessions, locks, temp directories,
timers, mocking patches.

```python
with open("data.csv") as f:
    rows = f.readlines()
# file is guaranteed closed here, even if readlines() raised
```

Without it, you'd write the `try/finally` by hand every time:

```python
f = open("data.csv")
try:
    rows = f.readlines()
finally:
    f.close()
```

Both are correct. The `with` version is idiomatic because it makes the
"this resource has a guaranteed cleanup boundary" fact visible in the
structure of the code, not buried in a `finally` block someone might forget
to write.

## What `__enter__` and `__exit__` actually do

`with EXPR as VAR:` desugars, roughly, to:

```python
mgr = EXPR
VAR = mgr.__enter__()
try:
    # block body
    ...
finally:
    mgr.__exit__(exc_type, exc_value, traceback)
```

`__enter__` runs at the top of the block and its return value is what gets
bound to `VAR` — for a file, `__enter__` returns `self`, which is why
`with open(...) as f:` gives you back the file object. `__exit__` always
runs, and receives exception info if the block raised (`None, None, None`
if it didn't). If `__exit__` returns a truthy value, the exception is
**suppressed** — this is intentional, but easy to do by accident if you
write `def __exit__(self, *args): return True` out of habit.

## Writing your own: class-based

```python
import time


class Timer:
    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.elapsed = time.perf_counter() - self._start
        return False  # don't suppress exceptions


with Timer() as t:
    do_expensive_work()
print(f"took {t.elapsed:.3f}s")
```

Note the explicit `return False` — being explicit about *not* swallowing
exceptions is worth the extra line, since the failure mode (a silently
swallowed exception) is much harder to debug than a slightly verbose
`__exit__`.

## Writing your own: `@contextmanager` (the idiomatic default)

For anything that's "run setup, yield control, run cleanup," a generator
function decorated with `@contextmanager` is almost always less
boilerplate than a full class:

```python
from contextlib import contextmanager
from collections.abc import Iterator


@contextmanager
def timer() -> Iterator[dict]:
    result: dict = {}
    start = time.perf_counter()
    try:
        yield result
    finally:
        result["elapsed"] = time.perf_counter() - start


with timer() as t:
    do_expensive_work()
print(f"took {t['elapsed']:.3f}s")
```

Everything before `yield` is `__enter__`; the yielded value is what `as`
binds to; everything after `yield`, inside `finally`, is `__exit__`. The
`try/finally` around the `yield` is what guarantees cleanup runs even if
the caller's block raises — omitting it is the single most common bug
in hand-written context managers.

## Why this matters for resource safety specifically

The unifying theme: any resource with an acquire/release lifecycle —
file handles, DB connections and transactions, threading locks, temp
files — should be modeled as a context manager, because it makes leaking
that resource a *structural* impossibility rather than a discipline
problem. This project's own `Session` usage in `backend/app/api/deps.py`
follows this pattern: a DB session is opened and guaranteed to close (and
roll back on error) via a `with`/generator-based dependency, not via
manual `session.close()` calls scattered through route handlers.

```python
# SQLAlchemy session — same pattern, real code from this kind of codebase
def get_db() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

## Multiple context managers at once

Python lets you combine managers in one `with` statement (parenthesized
form, Python 3.10+, mirrors multiple imports):

```python
with (
    open("in.csv") as src,
    open("out.csv", "w") as dst,
):
    dst.write(transform(src.read()))
```

Both are guaranteed to be cleaned up, exited in reverse order of entry,
even if `transform` raises.

## Key takeaways

- `with` is guaranteed-cleanup syntax — the block's setup/teardown pair is
  `__enter__`/`__exit__`, called even when the body raises.
- `__exit__` returning a truthy value suppresses the exception — a
  frequent bug when copy-pasted context manager boilerplate returns `True`
  without meaning to.
- `@contextmanager` (a generator + `yield` wrapped in `try/finally`) is
  the idiomatic default for simple cases; a full class is worth it mainly
  when you need multiple methods or state beyond one setup/teardown pair.
- Anything with an acquire/release lifecycle — files, DB sessions, locks —
  belongs in a context manager so leaking it is structurally prevented,
  not just a discipline convention.
""",
        ),
        LessonModule(
            title="Idiomatic control flow: EAFP, unpacking, match",
            content=r"""
## EAFP vs LBYL

"Look Before You Leap" (check preconditions, then act) is the default
instinct coming from most languages:

```python
# LBYL
if key in config:
    value = config[key]
else:
    value = default
```

Python's idiom is usually "Easier to Ask Forgiveness than Permission" —
attempt the operation, handle the exception if it fails:

```python
# EAFP
try:
    value = config[key]
except KeyError:
    value = default
```

This isn't just style. Two real reasons EAFP is preferred in Python:

1. **Race conditions.** Between an LBYL check and the subsequent action,
   state can change (a file existing check followed by an open, a
   dict-membership check followed by access in threaded code). EAFP
   collapses the check-then-act gap into one atomic-from-your-perspective
   operation.
2. **Cost model.** CPython exceptions are cheap when *not* raised — a
   `try` block with no exception has near-zero overhead. LBYL often means
   paying for the lookup twice (once to check, once to use); EAFP pays for
   it once, and only pays the (higher) exception cost on the actually-rare
   failure path.

That said, `dict.get(key, default)` beats both for the simple default-value
case — reach for the method that says what you mean before reaching for
`try/except` as a first resort:

```python
value = config.get(key, default)  # simplest correct version
```

EAFP earns its keep for the more complex cases — multiple ways an
operation can fail, or operations without a convenience method:

```python
try:
    user = User.objects.get(email=email)
except User.DoesNotExist:
    user = User.objects.create(email=email)
```

## Unpacking

Destructuring in JS (`const [a, b] = arr`) has a direct, more powerful
analogue in Python, used constantly in idiomatic code:

```python
first, second, *rest = [1, 2, 3, 4, 5]
# first=1, second=2, rest=[3, 4, 5]

*init, last = [1, 2, 3, 4, 5]
# init=[1, 2, 3, 4], last=5

a, (b, c) = 1, (2, 3)   # nested unpacking
```

The most common real-world use: swapping without a temp variable (tuple
packing/unpacking, not special-cased swap syntax — it's the same mechanism
as function returns), and unpacking function returns:

```python
a, b = b, a  # builds a tuple (b, a), then unpacks it into a, b

def min_max(values: list[int]) -> tuple[int, int]:
    return min(values), max(values)

lo, hi = min_max(values)
```

And unpacking in a `for` loop over pairs — extremely common with
`.items()`, `enumerate`, and `zip`:

```python
for key, value in mapping.items():
    ...

for index, value in enumerate(values):
    ...

for a, b in zip(list_a, list_b):
    ...
```

## `match` statements (3.10+): structural pattern matching, not a switch

`match` looks like a `switch`, but it's doing structural destructuring
against patterns, not just equality checks against a value — closer to
pattern matching in Rust/Elixir/Scala than to C-family `switch`:

```python
def handle(event: dict) -> str:
    match event:
        case {"type": "click", "x": x, "y": y}:
            return f"click at ({x}, {y})"
        case {"type": "keypress", "key": key}:
            return f"key: {key}"
        case {"type": type_} if type_.startswith("custom_"):
            return f"custom event: {type_}"
        case _:
            return "unknown event"
```

It also matches against class shapes, not just dicts — useful for
dispatching on a small closed set of domain types without an `isinstance`
chain:

```python
match shape:
    case Circle(radius=r):
        return 3.14159 * r ** 2
    case Rectangle(width=w, height=h):
        return w * h
    case _:
        raise ValueError(f"unknown shape: {shape}")
```

Reach for `match` when you're destructuring *and* branching on shape at
the same time — for a simple value-equality dispatch, a dict lookup or a
plain `if/elif` chain is often more direct.

## When NOT to be clever

All three of these idioms have a failure mode: using them because they're
available, not because they communicate intent better than the plain
alternative. A `try/except` wrapping ten lines to catch one possible
`KeyError` five lines down obscures which line can actually fail — narrow
the `try` block to just the risky call. A `match` with a single `case`
and a wildcard is just an `if` wearing a costume. Deeply nested unpacking
(`(a, (b, (c, d))) = nested`) is harder to read than three plain
assignment lines. Idiomatic doesn't mean "use the fanciest applicable
syntax" — it means "use the construct that makes the intent obvious to
the next reader," and sometimes that's the boring version.

## Key takeaways

- EAFP (try, then handle the exception) is preferred over LBYL (check,
  then act) in Python — it avoids check-then-act races and is often
  cheaper when the failure path is rare; `dict.get(k, default)` beats
  both for the simple default-value case.
- Unpacking (including starred `*rest`) is the idiomatic way to destructure
  tuples, function returns, and loop pairs — not just a swap-variables
  trick.
- `match` does structural pattern matching (dict shape, class shape,
  guards), not value-equality switching — use it when you're branching on
  *shape*, not just comparing a value.
- Every one of these idioms can be misused for "looking clever" instead of
  being clearer — the bar is always "does this read faster than the
  boring version," not "does this use a more advanced feature."
""",
        ),
    ],
    "type-hints": [
        LessonModule(
            title="Type hints: why they matter and the basics",
            content=r"""
## Python is dynamically typed; type hints don't change that

This is the first thing to get straight coming from a statically-typed
mindset (or even from TypeScript, which does change JS's runtime
behavior in some configurations): Python type hints are **not enforced at
runtime** by default. `def add(a: int, b: int) -> int:` will happily
accept and add two strings — the hints are pure metadata, checked by a
separate tool (`mypy`, `pyright`) that never runs when your program runs.
This surprises people expecting hints to behave like TypeScript's compiler
output or like PHP's (enforced) type declarations.

```python
def add(a: int, b: int) -> int:
    return a + b

add("hello", "world")  # runs fine, returns "helloworld" — no error at runtime
```

## So why bother, in a dynamic language?

Three concrete payoffs that matter even without runtime enforcement:

1. **Bugs caught before code runs.** `mypy`/`pyright` catch a real class
   of bugs — passing `None` where a value is required, calling a method
   that doesn't exist on a type, mismatched return types — during
   development, in CI, or in your editor, instead of in production at 2am.
2. **Executable documentation.** `def get_user(user_id: UUID) -> User |
   None:` tells you the contract without reading the function body or
   guessing from the name. Docstrings go stale; type hints that mypy
   checks against the actual code cannot silently drift from reality the
   same way.
3. **IDE support.** Autocomplete, "go to definition," and inline
   parameter hints all get dramatically better once the IDE can infer
   concrete types instead of guessing from usage.

## Basic syntax

```python
def greet(name: str, times: int = 1) -> str:
    return (name + " ") * times


age: int = 30
scores: list[int] = [90, 85, 77]
config: dict[str, str] = {"env": "production"}
```

Note `list[int]` and `dict[str, str]` — since Python 3.9 the built-in
collection types are generic directly (no need to import `List`/`Dict`
from `typing` anymore; that's legacy from 3.8 and earlier you'll still see
in older code).

## Optional values: `Optional[X]` vs `X | None`

`Optional[X]` is exactly `Union[X, None]` — a value that's either an `X`
or `None`. Modern Python (3.10+) lets you write this with the `|`
operator directly, which is now the idiomatic form:

```python
from typing import Optional

def find_user(user_id: UUID) -> Optional[User]: ...   # older style
def find_user(user_id: UUID) -> User | None: ...       # idiomatic, 3.10+
```

The `| None` form reads the same as the reasoning you'd use out loud
("a User, or None") and composes the same way unions do generally
(`int | str`, `str | bytes`), so it's preferred in new code targeting
3.10+. This project targets a modern Python version, so default to `|
None` unless you have a concrete reason (a library, an older runtime
target) to use `Optional`.

## Generics: `list[T]`, `dict[K, V]`, and your own generic functions

Beyond the built-ins, you write your own generic functions and classes
with `TypeVar` (pre-3.12) or the newer `type` parameter syntax (3.12+):

```python
from typing import TypeVar

T = TypeVar("T")

def first(items: list[T]) -> T:
    return items[0]

# Python 3.12+ syntax — no import needed
def first(items: list[T]) -> T:
    ...
```

The point of a `TypeVar` here isn't decoration — it's that `first`
returns *the same type it was given*: `first([1, 2, 3])` is known to
return `int`, `first(["a", "b"])` is known to return `str`, and mypy
enforces that relationship at every call site. Without the `TypeVar`,
you'd have to type the return as `Any` or `object`, losing all of that
information.

## A worked example: a typed repository function

```python
from collections.abc import Sequence
from uuid import UUID


def get_active_users(
    user_ids: Sequence[UUID],
    include_admins: bool = False,
) -> list[User]:
    query = select(User).where(User.id.in_(user_ids), User.is_active.is_(True))
    if not include_admins:
        query = query.where(User.role != "admin")
    return list(session.scalars(query))
```

Notice `Sequence[UUID]` rather than `list[UUID]` for the *parameter* —
accepting the most general type that supports what you actually do
(iterate, no mutation) is idiomatic; it lets callers pass a `list`, a
`tuple`, or any other sequence without your function caring. Prefer
concrete types (`list[User]`) for *return* values, since callers benefit
from knowing exactly what they get back. This asymmetry — liberal in what
you accept, precise in what you return — is a recurring theme in
well-typed Python APIs.

## Key takeaways

- Type hints are unenforced metadata at runtime by default — the payoff is
  static analysis (mypy/pyright), documentation, and IDE support, not
  runtime validation.
- Prefer `X | None` over `Optional[X]` in modern code — same meaning,
  reads more naturally, consistent with general union syntax.
- Built-in collections (`list`, `dict`, `set`) are generic directly since
  3.9 — no need to import from `typing` for these anymore.
- `TypeVar` (or 3.12+ `type` parameter syntax) lets a function's return
  type depend on its argument types — use it whenever "the output type
  matches the input type" is actually true.
- Accept broad types (`Sequence`, `Iterable`) as parameters; return
  concrete types (`list`, a specific class) — liberal in, precise out.
""",
        ),
        LessonModule(
            title="Protocol vs ABC, and using mypy effectively",
            content=r"""
## Two ways to say "this type must support X"

Python has two distinct mechanisms for describing a required interface,
and picking the wrong one for the situation is a common source of
over-engineered or overly-rigid code.

**`ABC` (nominal typing)** — a type satisfies the interface only if it
*explicitly* inherits from the abstract base class:

```python
from abc import ABC, abstractmethod


class Repository(ABC):
    @abstractmethod
    def get(self, id: UUID) -> object: ...

    @abstractmethod
    def save(self, entity: object) -> None: ...


class PostgresRepository(Repository):  # must inherit, must implement both
    def get(self, id: UUID) -> object: ...
    def save(self, entity: object) -> None: ...
```

Instantiating a subclass that hasn't implemented every `@abstractmethod`
raises `TypeError` *at runtime* — this is real enforcement, not just a
type-checker opinion, because `ABCMeta` hooks into instance creation.

**`Protocol` (structural typing)** — a type satisfies the interface simply
by *having the right shape*, with no inheritance relationship required:

```python
from typing import Protocol


class SupportsGet(Protocol):
    def get(self, id: UUID) -> object: ...


class PostgresRepository:  # no inheritance from SupportsGet at all
    def get(self, id: UUID) -> object: ...
    def save(self, entity: object) -> None: ...


def load(repo: SupportsGet, id: UUID) -> object:
    return repo.get(id)

load(PostgresRepository(), some_id)  # type-checks: PostgresRepository has .get()
```

This is "duck typing, but checked" — mypy verifies structural
compatibility at type-check time, but there's zero runtime cost or
coupling; `PostgresRepository` doesn't even need to know `SupportsGet`
exists. This is the closest Python gets to Go's interfaces, and it's a
distinctly different mental model from Java/PHP-style `implements`.

## When to use each

- **`Protocol`** when you're defining "what capability does my function
  need" and don't want to force every implementer (including ones from
  third-party libraries you don't control) into an inheritance
  relationship. This is the default choice for most application code —
  it's less coupling for the same guarantee.
- **`ABC`** when you want actual runtime enforcement (a subclass that
  forgets to implement a method should fail loudly at instantiation, not
  just get flagged by a type checker someone might be ignoring), or when
  you want to share concrete helper methods alongside the abstract
  contract (`ABC` can mix abstract and implemented methods; a `Protocol`
  is generally just the shape).

## A generic `Repository[T]`

Combining generics with a `Protocol` gives you one reusable, precisely
typed interface instead of hand-writing a `UserRepository`,
`OrderRepository`, etc., each restating the same shape:

```python
from typing import Protocol, TypeVar
from uuid import UUID

T = TypeVar("T")


class Repository(Protocol[T]):
    def get(self, id: UUID) -> T | None: ...
    def save(self, entity: T) -> None: ...
    def delete(self, id: UUID) -> None: ...


class SqlAlchemyUserRepository:  # satisfies Repository[User] structurally
    def get(self, id: UUID) -> User | None: ...
    def save(self, entity: User) -> None: ...
    def delete(self, id: UUID) -> None: ...


def deactivate(repo: Repository[User], user_id: UUID) -> None:
    user = repo.get(user_id)
    if user is not None:
        user.is_active = False
        repo.save(user)
```

`deactivate` works against *any* type that structurally satisfies
`Repository[User]` — a real SQL-backed one, an in-memory fake for tests, a
caching decorator wrapping another repository — without any of them
inheriting from anything.

## Using mypy effectively

**Turn on strict mode early, not after the codebase is large.** `mypy
--strict` (or the equivalent flags in `pyproject.toml`) catches missing
type hints, implicit `Any`, and unchecked `None` handling that the default
mode lets slide. Retrofitting strict mode onto an untyped codebase is far
more painful than starting with it.

```toml
[tool.mypy]
strict = true
```

**Common false positives and how to handle them, in order of preference:**

1. **Narrow the type properly first.** The most common "false positive" is
   actually mypy correctly flagging that a value really could be `None`:

   ```python
   def process(user: User | None) -> str:
       return user.name  # mypy error: user could be None
   ```

   The fix is a real narrowing check, not suppression:

   ```python
   def process(user: User | None) -> str:
       if user is None:
           raise ValueError("user is required")
       return user.name  # mypy now knows user is User here
   ```

2. **Use `cast()` when you know something mypy can't infer**, e.g. after
   validating with a library mypy doesn't understand:

   ```python
   from typing import cast

   raw = json.loads(payload)
   data = cast(dict[str, str], raw)  # you've validated the shape elsewhere
   ```

3. **`# type: ignore[error-code]` is the last resort, not the first.**
   Always include the specific error code (`# type: ignore[arg-type]`, not
   a bare `# type: ignore`) so the suppression doesn't silently swallow
   unrelated future errors on that line, and leave a comment explaining
   *why* it's genuinely unfixable (a third-party stub bug, a dynamic
   pattern mypy fundamentally can't model) rather than reaching for it the
   moment mypy first complains.

```python
result = some_untyped_legacy_lib.do_thing()  # type: ignore[no-untyped-call]
# legacy_lib has no type stubs upstream; tracked in docs/PENDING.md
```

Reaching for `# type: ignore` before trying to actually fix the type is
the single biggest way strict typing rots over time — six months of
`# type: ignore` scattered without codes or reasons is indistinguishable
from not having mypy at all.

## Key takeaways

- `Protocol` is structural (duck typing, checked statically, no
  inheritance needed); `ABC` is nominal (explicit inheritance, enforced at
  runtime via `ABCMeta`). Default to `Protocol` for application interfaces;
  reach for `ABC` when you need runtime enforcement or shared concrete
  behavior.
- A generic `Protocol[T]` (e.g. `Repository[T]`) gives you one reusable
  interface instead of restating the same shape per entity type.
- Run mypy in strict mode from the start of a project — retrofitting it
  onto an untyped codebase later is much more expensive.
- When mypy complains, narrow the type first, `cast()` second, and reach
  for a scoped `# type: ignore[code]` with a comment only as the last
  resort — never a bare `# type: ignore`.
""",
        ),
    ],
    "async-python": [
        LessonModule(
            title="What async actually buys you (and what it doesn't)",
            content=r"""
## The event loop model, in contrast to threads

Coming from Node, the mental model transfers almost directly: a single
thread runs an event loop that switches between tasks whenever one of them
hits an `await` on I/O, instead of blocking. Coming from PHP (traditionally
process-per-request, no shared event loop) or from Java-style threading,
it's a bigger mental shift: **asyncio concurrency happens on one OS
thread**. There's no preemption — a coroutine runs uninterrupted until it
hits an `await` and voluntarily yields control back to the loop. This is
fundamentally different from OS threads, which the scheduler can suspend
at any instruction.

That single fact explains most of asyncio's behavior:

- Two coroutines can never run their Python bytecode *simultaneously* —
  only one is ever executing at a time. "Concurrency," not "parallelism."
- A coroutine that never `await`s anything blocks the entire event loop —
  every other coroutine waits, because nothing preempts it.
- There's no need for locks around shared in-memory state the way there is
  with threads, *as long as* you don't `await` in the middle of a
  read-modify-write sequence (if you do, another coroutine can run in that
  gap and the classic race condition is back).

## Coroutines vs threads vs processes — three different problems solved

- **`asyncio` coroutines** — solve many concurrent I/O-bound waits
  (network, DB, file I/O). Cost model: one thread, cooperative switching,
  near-zero per-task overhead.
- **OS threads (`threading`)** — solve blocking I/O in libraries that
  aren't async-aware. Cost model: OS context-switch cost, real locking
  hazards, limited by the GIL for CPU-bound work.
- **Processes (`multiprocessing`)** — solve actual CPU-bound parallelism.
  Cost model: separate memory space, no GIL contention, but expensive
  startup and serialization cost to move data between processes.

## The common misconception: async does NOTHING for CPU-bound work

This is the mistake senior engineers coming from Node most often make,
because Node's story is subtly different (Node is also single-threaded,
but "CPU-bound work blocks everything" is *equally* true there — the
misconception is thinking Python's GIL makes async a general parallelism
tool, which it never was in either language).

```python
import asyncio


async def compute_primes(n: int) -> list[int]:
    primes = []
    for candidate in range(2, n):
        if all(candidate % p != 0 for p in primes):
            primes.append(candidate)
    return primes


async def main() -> None:
    # These do NOT run in parallel. compute_primes never awaits anything,
    # so once it starts, it runs to completion, blocking the entire event
    # loop — the second call doesn't even start until the first returns.
    results = await asyncio.gather(
        compute_primes(50_000),
        compute_primes(50_000),
    )
```

`asyncio.gather` schedules both coroutines, but since neither one ever
hits an `await` internally, the first one monopolizes the single thread
until it finishes — there is no interleaving, and total wall-clock time is
the same as running them sequentially (actually slightly worse, due to
scheduling overhead). Async gives the *event loop* opportunities to switch
tasks only at `await` points; a tight CPU loop with no `await` in it never
yields, so there's nothing for the loop to interleave.

For CPU-bound work, the fix is a process pool (side-steps the GIL by using
separate interpreters), not asyncio:

```python
from concurrent.futures import ProcessPoolExecutor
import asyncio


async def main() -> None:
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as pool:
        results = await asyncio.gather(
            loop.run_in_executor(pool, compute_primes_sync, 50_000),
            loop.run_in_executor(pool, compute_primes_sync, 50_000),
        )
```

## Where async genuinely helps: I/O-bound work

The payoff shows up when a coroutine spends most of its time *waiting*,
not computing — a network call, a database round-trip, reading a file off
disk. While one coroutine waits on the network, the event loop runs
another coroutine's code during that dead time:

```python
async def fetch_user(client: httpx.AsyncClient, user_id: UUID) -> User:
    response = await client.get(f"/users/{user_id}")  # yields control here
    return User(**response.json())


async def main() -> None:
    async with httpx.AsyncClient(base_url="https://api.example.com") as client:
        # All three requests are in flight concurrently — while one waits
        # on the network, the loop runs the others.
        users = await asyncio.gather(
            fetch_user(client, id1),
            fetch_user(client, id2),
            fetch_user(client, id3),
        )
```

Three sequential `await`-based HTTP calls with no concurrency would take
roughly `t1 + t2 + t3`; run concurrently via `gather`, they take roughly
`max(t1, t2, t3)` — the win is proportional to how much of the total time
is spent waiting on something external, not computing.

## Key takeaways

- Asyncio concurrency runs on a single thread with cooperative scheduling
  — a coroutine only yields control at an `await`; nothing preempts it.
- Threads and processes solve different problems: threads help with
  blocking I/O from non-async libraries; processes are the actual answer
  for CPU-bound parallelism (they sidestep the GIL).
- Async helps I/O-bound work (network, disk, DB) because the event loop
  can run other tasks while one waits. It does nothing for CPU-bound work
  — a tight loop with no `await` blocks the entire event loop, and
  `asyncio.gather` around two CPU-bound coroutines still runs them
  sequentially in wall-clock time.
- If a workload is genuinely CPU-bound, reach for `ProcessPoolExecutor`
  (optionally driven from async code via `run_in_executor`), not asyncio
  concurrency primitives.
""",
        ),
        LessonModule(
            title="Practical asyncio: gather, semaphores, partial failure",
            content=r"""
## `async`/`await` mechanics

`async def` defines a coroutine function — calling it doesn't run the
body, it returns a coroutine object that has to be driven by an event
loop (`await`ed, or scheduled as a `Task`):

```python
async def fetch_one(client: httpx.AsyncClient, url: str) -> httpx.Response:
    return await client.get(url)

coro = fetch_one(client, url)   # nothing has run yet
result = await coro             # now it actually executes
```

`await` does two things: it runs the awaited coroutine, and it's the point
at which *this* coroutine can be suspended and the event loop can go run
something else while waiting for the result.

## `asyncio.gather`: running many coroutines concurrently

```python
results = await asyncio.gather(
    fetch_one(client, url1),
    fetch_one(client, url2),
    fetch_one(client, url3),
)
```

By default, if *any* awaited coroutine raises, `gather` immediately
propagates that exception — the other still-running coroutines are not
automatically cancelled, but their results are discarded, which is often
not what you want for a batch job where a single bad URL shouldn't kill
the whole batch.

## Worked example: N URLs, bounded concurrency, partial failure tolerated

This combines the three practical concerns that come up in almost every
real asyncio use case: limiting how many requests run at once (you don't
want 10,000 concurrent connections just because you have 10,000 URLs),
and not letting one failure abort everything else.

```python
import asyncio
import httpx


async def fetch_with_limit(
    client: httpx.AsyncClient,
    url: str,
    semaphore: asyncio.Semaphore,
) -> tuple[str, httpx.Response | None, Exception | None]:
    async with semaphore:  # blocks here once `limit` tasks are already inside
        try:
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            return url, response, None
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            return url, None, exc


async def fetch_all(urls: list[str], limit: int = 10) -> list[tuple]:
    semaphore = asyncio.Semaphore(limit)
    async with httpx.AsyncClient() as client:
        tasks = [fetch_with_limit(client, url, semaphore) for url in urls]
        return await asyncio.gather(*tasks)  # exceptions are already caught
                                              # inside fetch_with_limit, so
                                              # gather never sees one raise


async def main() -> None:
    urls = [f"https://api.example.com/items/{i}" for i in range(500)]
    results = await fetch_all(urls, limit=10)

    succeeded = [(url, resp) for url, resp, err in results if err is None]
    failed = [(url, err) for url, resp, err in results if err is not None]
    print(f"{len(succeeded)} ok, {len(failed)} failed")
```

Two design choices worth calling out explicitly:

1. **`asyncio.Semaphore(limit)`** caps how many coroutines can be inside
   the `async with semaphore:` block simultaneously — the 11th task
   attempting to enter blocks (asynchronously, without tying up a thread)
   until one of the first 10 finishes and releases. This is what "bounding
   concurrency" means concretely: 500 URLs, but never more than 10
   in-flight HTTP requests at once.
2. **Catching exceptions *inside* `fetch_with_limit`, not around
   `gather`.** If you let an exception propagate out of a task passed to
   `gather`, by default `gather` raises the first exception it sees and
   the caller loses visibility into which of the other 499 requests
   succeeded. Catching per-task and returning the error as data
   (`(url, None, exc)`) instead of raising is what makes "handle
   individual failures without cancelling the rest" actually work — the
   alternative, `asyncio.gather(*tasks, return_exceptions=True)`, achieves
   something similar by stuffing exceptions into the results list instead
   of raising, but then every call site has to `isinstance`-check each
   result, which is usually less clear than handling it at the source.

## A common pitfall: forgetting `asyncio.gather` needs coroutines, not results

```python
# Wrong: this awaits sequentially, one at a time — no concurrency at all
results = [await fetch_one(client, url) for url in urls]

# Right: create all the coroutine objects first, then run them concurrently
results = await asyncio.gather(*(fetch_one(client, url) for url in urls))
```

The list-comprehension-with-`await` version looks similar but is a
completely different program: each `await` inside the loop body suspends
and resumes before moving to the next iteration, so requests happen one
after another, with zero overlap. Whether that's a bug or genuinely
intended (sometimes you *want* strict ordering) depends entirely on the
use case — but it's a mistake to write it by accident while intending
concurrency.

## Key takeaways

- A coroutine function returns a coroutine object when called; nothing
  runs until it's awaited or scheduled — this trips up anyone expecting
  call-time execution like a normal function.
- `asyncio.Semaphore(n)` is the standard way to bound concurrency —
  `async with semaphore:` around the work blocks the (n+1)th concurrent
  attempt without consuming a thread.
- To tolerate partial failure across many concurrent tasks, catch
  exceptions *inside* each task and return them as data, rather than
  letting them propagate into `gather` (or use
  `return_exceptions=True` and check each result explicitly).
- `[await f(x) for x in xs]` runs sequentially, not concurrently — build
  the coroutine objects first and hand them all to `gather` if you
  actually want overlap.
""",
        ),
        LessonModule(
            title="Case study: why this project's backend uses sync SQLAlchemy",
            content=r"""
## The temptation: "FastAPI supports async, so use async everywhere"

FastAPI is often introduced through async examples, and it's easy to
absorb "async is the modern/correct way to write a FastAPI app" as a
blanket rule. This project's own backend (`backend/app/`) deliberately
does the opposite for its database layer: routers that touch the database
are plain `def`, not `async def`, and SQLAlchemy is used in its
synchronous mode — see `docs/DECISIONS.md` for the full reasoning recorded
at the time. This module treats that choice as a worked case study in
*not* reaching for async by default.

## Why sync-over-async can be the right call here

Applying the previous module's lesson (async helps I/O-bound work, but
only when you're actually structured to exploit the concurrency): a
typical CRUD backend's request handler does one or two sequential DB
queries and returns — there's rarely a batch of independent I/O calls
within a single request that would benefit from `asyncio.gather`-style
concurrency the way the "fetch N URLs" example did. Without that internal
concurrency to exploit, async buys you *less* than it initially appears
to, while it costs you real things:

1. **A more complex mental model for the whole codebase.** Once part of a
   codebase is async, "what colour is this function" (sync vs async)
   becomes a decision every new function has to make, and mixing them
   incorrectly (calling a sync blocking DB driver from inside an `async
   def` route, for instance) silently blocks the *entire* event loop for
   every other in-flight request — a much worse failure mode than a
   blocked thread in a thread-pool model, because it stalls concurrent
   *unrelated* requests, not just the one making the call.
2. **The ecosystem cost.** Async database drivers, async ORMs, and async
   versions of every dependency are a smaller, less battle-tested subset
   of the Python ecosystem than their sync counterparts. Sync SQLAlchemy
   is the more mature, more heavily used path.
3. **FastAPI already solves the concurrency problem for sync code.** A
   plain `def` route handler in FastAPI is automatically run in a thread
   pool, not the main event loop — so a sync DB call in one request
   doesn't block other concurrent requests either. You get "requests don't
   block each other" without opting into async's added complexity, because
   FastAPI's threading already provides it at the request level.

## When async *would* be the right call instead

The case study cuts both ways — this isn't "async is bad," it's "match
the tool to the actual shape of the workload." Async earns its complexity
when:

- A single request needs to make **multiple independent I/O calls that
  can genuinely overlap** — e.g., fanning out to three downstream
  microservices and combining their responses, where `asyncio.gather`
  turns `t1 + t2 + t3` into `max(t1, t2, t3)`.
- The service needs to hold **very large numbers of concurrent
  long-lived connections** (websockets, SSE streams, long-polling) where a
  thread-per-connection model would exhaust OS thread limits.
- You're building **on top of a library that's async-only** (some modern
  HTTP clients, some message queue clients) — at that point you're paying
  the async complexity cost either way, so you might as well go async
  end-to-end instead of bridging sync and async awkwardly.

## The general principle

The decision isn't "async is modern, sync is legacy" — it's "does this
workload have exploitable I/O concurrency, and does the added complexity
pay for itself." A backend doing one DB round-trip per request, already
handled by a thread pool underneath, often doesn't clear that bar. A
service fanning out to five APIs per request, or juggering thousands of
open streaming connections, usually does. Treat "should this be async" as
an engineering trade-off to evaluate per component, the same way you'd
evaluate any other technology choice — not a default to reach for because
a framework happens to support it.

## Key takeaways

- Async's payoff requires *exploitable* concurrent I/O within a unit of
  work — a handler doing one sequential DB call doesn't have anything for
  `gather` to overlap, so async adds complexity without a matching win.
- FastAPI runs plain `def` route handlers in a thread pool automatically —
  sync code already gets "one slow request doesn't block others" without
  opting into async's mixed-sync/async hazards.
- Mixing a blocking (sync) call inside `async def` code is worse than the
  equivalent mistake in a thread-pool model: it stalls the entire event
  loop, affecting every concurrent request, not just the slow one.
- This project's own backend chose sync SQLAlchemy deliberately for these
  reasons (see docs/DECISIONS.md) — treat it as a real example of
  evaluating async as a trade-off per component, not a default.
""",
        ),
    ],
    "testing-with-pytest": [
        LessonModule(
            title="Fixtures and parametrization",
            content=r"""
## Why pytest fixtures beat `setUp`/`tearDown`

Coming from `unittest` (or JUnit/PHPUnit-style `setUp`/`tearDown`),
fixtures are pytest's answer to shared test setup — but they solve a
broader problem than "run this before every test in the class." A
`setUp` method is monolithic: every test in the class gets *all* of it,
whether it needs a database connection, an authenticated client, sample
data, or all three. Fixtures are composable and requested individually by
name, so each test declares exactly what it needs:

```python
import pytest


@pytest.fixture
def db_session():
    session = SessionLocal()
    yield session          # test runs here
    session.rollback()     # cleanup, always runs after the test
    session.close()


@pytest.fixture
def sample_user(db_session):          # fixtures can depend on other fixtures
    user = User(email="test@example.com")
    db_session.add(user)
    db_session.commit()
    return user


def test_deactivate_user(db_session, sample_user):
    deactivate(db_session, sample_user.id)
    db_session.refresh(sample_user)
    assert sample_user.is_active is False


def test_something_unrelated_to_users():
    # doesn't request db_session or sample_user — pays no cost for setup
    # it doesn't need, unlike a shared setUp() every test in the class runs
    assert normalize_slug("Hello World") == "hello-world"
```

The `yield` splits setup from teardown the same way a `@contextmanager`
does (this is not a coincidence — it's the same underlying pattern):
everything before `yield` runs before the test, everything after runs
after, guaranteed, even if the test fails or raises.

## Fixture scopes

By default a fixture runs fresh for *every test function that requests
it*. That's often wasteful for expensive setup (spinning up a DB
connection pool, seeding reference data) that doesn't need to be
per-test. `scope` controls the lifetime:

```python
@pytest.fixture(scope="function")   # default: new instance per test
def db_session(): ...

@pytest.fixture(scope="module")     # one instance, shared by all tests in this file
def api_client(): ...

@pytest.fixture(scope="session")    # one instance for the entire test run
def db_engine(): ...
```

The trade-off: a wider scope means less setup cost, but more risk of
cross-test state leakage if the fixture's resource is mutable and one
test's changes bleed into another. A common, effective pattern: a
`session`-scoped engine/connection-pool (expensive, safe to share because
it holds no per-test data) paired with a `function`-scoped transaction
that wraps each test and rolls back at the end (cheap, guarantees
isolation):

```python
@pytest.fixture(scope="session")
def engine():
    return create_engine(TEST_DATABASE_URL)


@pytest.fixture(scope="function")
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()   # undoes everything this test did
    connection.close()
```

## `@pytest.mark.parametrize`: one readable test, many cases

The naive way to cover several edge cases is copy-pasting the test body
with different literals — which makes it easy for the cases to drift out
of sync and hard to see, at a glance, which inputs are actually covered.
`parametrize` separates the test *logic* from the test *data*:

```python
@pytest.mark.parametrize(
    "raw_input, expected",
    [
        ("Hello World", "hello-world"),
        ("  leading spaces", "leading-spaces"),
        ("Already-Slugged", "already-slugged"),
        ("Multiple   Spaces", "multiple-spaces"),
        ("", ""),
        ("Café Münster", "cafe-munster"),  # accented characters
    ],
)
def test_normalize_slug(raw_input: str, expected: str) -> None:
    assert normalize_slug(raw_input) == expected
```

pytest runs this as six independent test cases (`test_normalize_slug[Hello
World-hello-world]`, etc.), each reported separately — one failing input
doesn't hide the pass/fail status of the other five, unlike a hand-rolled
loop over cases inside one test function, where a failure on case 2 stops
the function and you never learn whether cases 3–6 would have passed too.

Stacking two `parametrize` decorators multiplies the cases (a Cartesian
product) — useful for covering combinations without writing them out by
hand:

```python
@pytest.mark.parametrize("role", ["admin", "member", "guest"])
@pytest.mark.parametrize("is_active", [True, False])
def test_can_access_dashboard(role: str, is_active: bool) -> None:
    user = make_user(role=role, is_active=is_active)
    assert can_access_dashboard(user) == (is_active and role != "guest")
```

That's 3 × 2 = 6 generated test cases from four lines, each named and
reported individually.

## Key takeaways

- Fixtures are requested by name per-test, not inherited wholesale like
  `setUp` — each test pays only for the setup it actually declares.
- `yield` inside a fixture splits setup (before) from guaranteed teardown
  (after) — the same pattern as `@contextmanager`.
- Fixture `scope` trades setup cost against isolation risk — a common
  pattern is a session-scoped engine plus a function-scoped
  transaction-per-test that rolls back automatically.
- `@pytest.mark.parametrize` turns "one test, many near-duplicate copies"
  into "one test body, a table of cases" — each case is reported
  independently, so one failure doesn't hide the others.
""",
        ),
        LessonModule(
            title="Mocking done well and structuring a test suite",
            content=r"""
## `unittest.mock` basics

`Mock`/`MagicMock` objects auto-create attributes and methods on access,
recording every call so you can assert on it afterward:

```python
from unittest.mock import Mock

mock_client = Mock()
mock_client.get.return_value = {"status": "ok"}

result = mock_client.get("/health")

mock_client.get.assert_called_once_with("/health")
assert result == {"status": "ok"}
```

`patch` (as a decorator or context manager) temporarily replaces a real
object with a mock for the duration of a test:

```python
from unittest.mock import patch

def test_sends_welcome_email():
    with patch("app.services.user_service.send_email") as mock_send:
        create_user(email="new@example.com")
        mock_send.assert_called_once_with(
            to="new@example.com", template="welcome"
        )
```

The critical, frequently-misunderstood detail: `patch("app.services.
user_service.send_email")` patches the name `send_email` **as looked up in
the `user_service` module**, not wherever `send_email` was originally
defined. If `user_service.py` does `from app.email import send_email`,
you patch `app.services.user_service.send_email` (where it's *used*), not
`app.email.send_email` (where it's *defined*) — patching the wrong
location is the single most common reason "the mock isn't being called"
when debugging a failing mock-based test.

## pytest's `monkeypatch`: the more idiomatic option for simple substitution

For attribute/env-var/dict substitution that needs to be automatically
undone after the test, `monkeypatch` (a built-in pytest fixture) is
usually more idiomatic than reaching for `patch` directly — no context
manager or decorator nesting required, and cleanup is automatic:

```python
def test_uses_configured_api_url(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "https://staging.example.com")
    client = build_client()
    assert client.base_url == "https://staging.example.com"


def test_retry_uses_no_delay_in_tests(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda seconds: None)
    result = call_with_retry(flaky_operation)
    assert result == "success"
```

## What to mock vs what not to mock: "don't mock what you don't own"

This is the single most important judgment call in mocking, and the one
most often gotten wrong by over-mocking. The guideline: mock things **at
the boundary of your own code** — the interfaces you defined — not deep
inside a third-party library's internals.

```python
# Reasonable: mocking your own abstraction boundary
def test_place_order_charges_payment(mocker):
    fake_gateway = Mock(spec=PaymentGateway)   # PaymentGateway is YOUR interface
    fake_gateway.charge.return_value = ChargeResult(success=True)

    place_order(order, payment_gateway=fake_gateway)

    fake_gateway.charge.assert_called_once_with(order.total)


# Risky: mocking deep into a third-party library's internals
def test_place_order_charges_payment_bad(mocker):
    mocker.patch("stripe.PaymentIntent.create", return_value={"status": "succeeded"})
    # Now this test knows Stripe's SDK internals AND encodes an assumption
    # about the exact shape of Stripe's response — it'll break silently
    # when the SDK changes its return shape, and it never verifies your
    # code handles Stripe's *actual* behavior (rate limits, real error
    # shapes, etc.) — it only verifies your code handles whatever shape
    # you guessed at.
```

Mocking a third-party library you don't own encodes assumptions about
that library's internal behavior into your test suite — assumptions that
can silently drift from reality as the library evolves, giving you a
green test suite that no longer reflects what actually happens at
runtime. The fix is usually one level of your own abstraction: wrap the
third-party call in a small class/function you own (`PaymentGateway`),
mock *that* boundary in unit tests, and cover the real third-party
integration with a small number of separate, real (or sandbox-mode)
integration tests that aren't mocked at all.

## Structuring a test suite: arrange/act/assert

Most well-structured pytest tests fall into three visually separated
sections, even without comments labeling them — the shape alone should
communicate this:

```python
def test_applying_a_valid_coupon_reduces_order_total():
    # Arrange
    order = make_order(subtotal=Decimal("100.00"))
    coupon = make_coupon(code="SAVE10", percent_off=10)

    # Act
    apply_coupon(order, coupon)

    # Assert
    assert order.total == Decimal("90.00")
```

A test that interleaves setup, action, and assertions throughout its body
is much harder to scan — a reviewer (or you, six months later) should be
able to find "what's being verified" without re-reading the whole
function.

## One assertion *concept* per test — not literally one `assert` line

This doesn't mean forbidding a second `assert` — it means each test
should verify one behavior. A test that asserts on five *unrelated*
outcomes is really five tests wearing a trenchcoat: when it fails, the
name (`test_order_processing`) doesn't tell you which of the five things
broke, and a change to unrelated behavior #4 breaks a test whose name
suggests it's about behavior #1.

```python
# Vague — five concepts crammed into one test, one failure tells you little
def test_order_processing():
    order = process_order(cart)
    assert order.total == Decimal("100.00")
    assert order.status == "confirmed"
    assert len(order.line_items) == 3
    assert order.confirmation_email_sent is True
    assert order.inventory_reserved is True

# Better — each test's name states exactly what broke when it fails
def test_process_order_calculates_correct_total(): ...
def test_process_order_sets_status_confirmed(): ...
def test_process_order_sends_confirmation_email(): ...
def test_process_order_reserves_inventory(): ...
```

## Meaningful test names

A test name should describe the behavior under test well enough that a
failure report (`FAILED test_apply_coupon_rejects_expired_coupon`) tells
you what broke without opening the file. `test_coupon_1`,
`test_edge_case`, or `test_apply_coupon_2` fail this bar — they require
opening the test body just to know what was being checked, at exactly the
moment (a red CI run) when that friction hurts most.

## Key takeaways

- `patch(...)` replaces a name where it's *looked up* (the importing
  module), not where it's originally defined — the most common reason a
  mock silently isn't hit.
- `monkeypatch` is the more idiomatic pytest-native choice for simple
  attribute/env/dict substitution — automatic cleanup, no context-manager
  nesting.
- "Don't mock what you don't own": mock your own interfaces/boundaries,
  not deep into third-party library internals — the latter encodes
  assumptions about the library that can silently go stale.
- Structure tests as arrange/act/assert, and keep each test to one
  behavioral concept so a failing test name alone tells you what broke.
- Names like `test_edge_case` or `test_thing_2` defeat the purpose of a
  test suite as a diagnostic tool — invest in names that describe the
  specific behavior being verified.
""",
        ),
    ],
}
