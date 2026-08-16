"""Lesson content for the Software Engineering subject.

Module count per competency tracks real topic complexity — SOLID gets one
module per principle plus a synthesis module (6 total); simpler topics get
fewer. See app.seeds.lessons.types.LessonModule.
"""

from app.seeds.lessons.types import LessonModule

LESSONS: dict[str, list[LessonModule]] = {
    "solid-principles": [
        LessonModule(
            title="S — Single Responsibility Principle",
            content=r"""
## The idea

> "A class should have only one reason to change." — Robert C. Martin

Notice what this *doesn't* say: it doesn't say "a class should do one thing"
(that's a simplification that misleads people into over-splitting classes
into meaningless fragments). It says one **reason to change** — one axis of
responsibility, one stakeholder or concern whose requirements could force
you to edit this code.

## A violation, concretely

```python
class Invoice:
    def __init__(self, items: list[LineItem]) -> None:
        self.items = items

    def total(self) -> Decimal:
        return sum(item.price * item.quantity for item in self.items)

    def save_to_database(self, db: Connection) -> None:
        db.execute(
            "INSERT INTO invoices (total) VALUES (%s)", (self.total(),)
        )

    def render_as_pdf(self) -> bytes:
        # ... PDF generation logic ...
        ...

    def send_email(self, smtp: SMTPClient, to: str) -> None:
        pdf = self.render_as_pdf()
        smtp.send(to=to, subject="Your invoice", attachment=pdf)
```

This class has *four* reasons to change:

1. The business rule for computing a total changes (e.g. tax handling).
2. The database schema or ORM changes.
3. The PDF layout changes (a design request).
4. The email provider or template changes.

Four different people — a finance analyst, a DBA, a designer, a marketing
lead — could each independently request a change that means editing this
one class. That's the smell: unrelated stakeholders converging on the same
file.

## The fix

Split along those axes:

```python
class Invoice:
    # Owns only the domain calculation.
    def __init__(self, items: list[LineItem]) -> None:
        self.items = items

    def total(self) -> Decimal:
        return sum(item.price * item.quantity for item in self.items)


class InvoiceRepository:
    # Owns persistence.
    def save(self, invoice: Invoice, db: Connection) -> None: ...


class InvoicePdfRenderer:
    # Owns presentation.
    def render(self, invoice: Invoice) -> bytes: ...


class InvoiceMailer:
    # Owns delivery.
    def send(self, invoice: Invoice, to: str) -> None: ...
```

Now each class changes for exactly one reason. `Invoice` itself becomes
pure domain logic with zero infrastructure dependencies — trivially unit
testable without a database, a PDF library, or an SMTP mock.

## The trap: over-splitting

SRP is not "functions should be five lines" or "one class per file no
matter what." A class that reads a config value and uses it in the same
method isn't two responsibilities — it's one responsibility with a
collaborator. Ask: *would these two pieces of logic ever need to change
for different business reasons?* If the honest answer is no, don't split
them just to look "SOLID." Splitting cohesive logic apart adds indirection
that costs more than it buys.

## Key takeaways

- "One reason to change" means one axis of *stakeholder-driven* change, not
  "does one thing" literally.
- The classic tell: a class importing infrastructure (DB, HTTP, file I/O)
  *and* containing business rules in the same place.
- Splitting by responsibility is what makes unit testing domain logic
  possible without mocking half the world.
- Don't over-apply it — cohesive logic that changes together should stay
  together.
""",
        ),
        LessonModule(
            title="O — Open/Closed Principle",
            content=r"""
## The idea

> "Software entities should be open for extension, but closed for
> modification." — Bertrand Meyer (the OCP originator); reframed by Martin

In practice: when a new *variant* of existing behavior shows up, you should
be able to add it without editing the code that already works and is
already tested. You extend by adding new code, not by re-opening old code
and risking what it already does correctly.

## A violation, concretely

```python
class DiscountCalculator:
    def calculate(self, order: Order, customer_type: str) -> Decimal:
        if customer_type == "regular":
            return order.total * Decimal("0.0")
        elif customer_type == "premium":
            return order.total * Decimal("0.10")
        elif customer_type == "vip":
            return order.total * Decimal("0.20")
        else:
            raise ValueError(f"Unknown customer type: {customer_type}")
```

Every time the business adds a new customer tier, you edit this method —
touching code that governs discounts for *every existing* customer type,
with every edit carrying a chance of breaking `premium` while adding
`enterprise`. The method also violates SRP as a side effect: it now knows
about every tier's policy at once.

## The fix: extension via polymorphism

```python
class DiscountPolicy(Protocol):
    def discount_for(self, order: Order) -> Decimal: ...


class RegularDiscount:
    def discount_for(self, order: Order) -> Decimal:
        return Decimal("0.0")


class PremiumDiscount:
    def discount_for(self, order: Order) -> Decimal:
        return order.total * Decimal("0.10")


class VipDiscount:
    def discount_for(self, order: Order) -> Decimal:
        return order.total * Decimal("0.20")


class DiscountCalculator:
    def __init__(self, policy: DiscountPolicy) -> None:
        self.policy = policy

    def calculate(self, order: Order) -> Decimal:
        return self.policy.discount_for(order)
```

Adding `EnterpriseDiscount` is now a new file, with its own unit test, that
never touches `RegularDiscount`'s tested behavior. `DiscountCalculator`
itself never changes again for this reason.

## This is not "never edit code"

OCP is about *behavioral extension points* that you can reasonably predict
will grow — payment methods, discount tiers, export formats, notification
channels. It is not a mandate to wrap every three-line function in an
interface "just in case." Predicting the wrong extension points and
abstracting them prematurely is its own, very real, cost (see: the
`AbstractSingletonProxyFactoryBean` school of over-engineering). Apply OCP
where you've already seen the pattern repeat, or where the domain
explicitly tells you "this will have more kinds."

## Key takeaways

- OCP is achieved through abstraction (interfaces/protocols) + polymorphism
  or composition (strategy pattern, plugin registries), not through
  guessing every possible future requirement.
- The trigger to apply it: a growing `if/elif` chain or `match` statement
  switching on a "kind" or "type" field that keeps getting new cases.
- Don't apply it speculatively — apply it to axes of variation you've
  already observed changing, or that the domain explicitly promises will.
""",
        ),
        LessonModule(
            title="L — Liskov Substitution Principle",
            content=r"""
## The idea

> "Subtypes must be substitutable for their base types." — Barbara Liskov

More precisely: if `S` is a subtype of `T`, you should be able to replace
any `T` with an `S` anywhere in the program without altering the
correctness of that program from the caller's point of view. This isn't
about the type system letting you substitute it (Python and most languages
will happily let you) — it's about *behavioral* compatibility: the subtype
must honor the base type's contract (preconditions, postconditions,
invariants), not just its method signatures.

## The canonical violation: Rectangle/Square

```python
class Rectangle:
    def __init__(self, width: float, height: float) -> None:
        self.width = width
        self.height = height

    def set_width(self, width: float) -> None:
        self.width = width

    def set_height(self, height: float) -> None:
        self.height = height

    def area(self) -> float:
        return self.width * self.height


class Square(Rectangle):
    def set_width(self, width: float) -> None:
        self.width = width
        self.height = width  # keep it a square

    def set_height(self, height: float) -> None:
        self.width = height
        self.height = height
```

`Square` type-checks as a `Rectangle`. But this breaks a caller that relies
on `Rectangle`'s implicit contract — that `set_width` doesn't also change
`height`:

```python
def resize_and_check(rect: Rectangle) -> None:
    rect.set_width(5)
    rect.set_height(4)
    assert rect.area() == 20  # true for Rectangle, FALSE for Square (area=16)
```

The code compiles, the types "match," and it's still wrong. That's exactly
what LSP is warning about: type-checking is necessary but not sufficient.

## Subtler violations: strengthened preconditions, weakened postconditions

Two ways this bites in real backend code:

- **A subclass that raises where the parent didn't.** If `PaymentGateway.
  charge()` never raises for a valid amount, but `StripeGateway.charge()`
  raises `RateLimitError` for amounts processed too quickly, every caller
  written against `PaymentGateway` is now unsafe until it learns about a
  concrete subclass's extra behavior — the abstraction leaked.
- **A subclass that returns a weaker guarantee.** If `Repository.get(id)`
  is documented to return a fully-loaded entity, and `CachedRepository.
  get(id)` sometimes returns a stale, partially-invalidated one, callers
  that trusted the contract get silently wrong data.

## The fix

Model what's actually true. A `Square` and a `Rectangle` are both
"quadrilaterals with an area," but they don't share a mutable
width/height contract — so don't force an inheritance relationship that
implies they do:

```python
class Shape(Protocol):
    def area(self) -> float: ...


@dataclass(frozen=True)
class Rectangle:
    width: float
    height: float
    def area(self) -> float:
        return self.width * self.height


@dataclass(frozen=True)
class Square:
    side: float
    def area(self) -> float:
        return self.side ** 2
```

Making both immutable and modeling them as siblings implementing a shared
`Shape` protocol (not a `Square(Rectangle)` inheritance) sidesteps the
whole problem — there's no mutable contract left to violate.

## Key takeaways

- LSP violations are *behavioral*, not syntactic — the type checker won't
  catch them.
- Watch for: subclasses that raise new exceptions, return weaker
  guarantees, or silently change the meaning of a mutation.
- When inheritance forces you to "turn off" or override behavior to keep a
  subtype sane, that's the signal the hierarchy is modeling the wrong
  relationship — prefer composition or a shared interface over inheritance.
""",
        ),
        LessonModule(
            title="I — Interface Segregation Principle",
            content=r"""
## The idea

> "Clients should not be forced to depend on interfaces they do not use."
> — Robert C. Martin

A fat interface with a dozen methods forces every implementer to provide
all twelve — including the ones that make no sense for it — and forces
every *caller* to depend (and be recompiled/retested, in stricter
languages) on methods it never calls. ISP says: split interfaces along the
lines of what clients actually need, not along the lines of "everything
this kind of thing could theoretically do."

## A violation, concretely

```python
class Worker(Protocol):
    def work(self) -> None: ...
    def eat_lunch(self) -> None: ...
    def get_paid(self) -> None: ...


class HumanWorker:
    def work(self) -> None: ...
    def eat_lunch(self) -> None: ...
    def get_paid(self) -> None: ...


class RobotWorker:
    def work(self) -> None: ...
    def eat_lunch(self) -> None:
        raise NotImplementedError("Robots don't eat lunch")  # 🚩
    def get_paid(self) -> None:
        raise NotImplementedError("Robots don't get paid")  # 🚩
```

`NotImplementedError` in an override is almost always ISP screaming at
you: the interface bundled together things that don't actually belong to
every implementer.

## A backend-flavored violation

```python
class UserRepository(Protocol):
    def get(self, id: UUID) -> User: ...
    def save(self, user: User) -> None: ...
    def delete(self, id: UUID) -> None: ...
    def bulk_export_to_csv(self) -> bytes: ...
    def run_gdpr_erasure(self, id: UUID) -> None: ...
```

A read-only reporting service that only ever calls `.get()` still has to
depend on (and, in a statically-typed language with structural typing
gaps, potentially implement stubs for) `bulk_export_to_csv` and
`run_gdpr_erasure`. Worse: every caller of this interface is coupled to
changes in *any* of these five methods' signatures, even the ones it never
touches.

## The fix: split by client need

```python
class UserReader(Protocol):
    def get(self, id: UUID) -> User: ...


class UserWriter(Protocol):
    def save(self, user: User) -> None: ...
    def delete(self, id: UUID) -> None: ...


class UserComplianceOps(Protocol):
    def bulk_export_to_csv(self) -> bytes: ...
    def run_gdpr_erasure(self, id: UUID) -> None: ...
```

The reporting service now depends only on `UserReader`. A concrete
`PostgresUserRepository` can still implement all three protocols — nothing
stops one class from satisfying several small interfaces — but *callers*
each depend on exactly the slice they use.

## Why this matters more than it looks

Small, role-specific interfaces are also what makes testing pleasant:
mocking `UserReader` for a test means faking one method, not five. And
they document intent — seeing a function accept a `UserReader` tells you,
without reading its body, that it definitely does not delete or export
user data.

## Key takeaways

- Fat interfaces force irrelevant dependencies onto every caller and
  implementer.
- The tell: an implementer that raises `NotImplementedError`, returns a
  dummy value, or has a comment like `# not used for this type`.
- A concrete class can implement multiple small interfaces — segregation
  happens at the interface/protocol level, not by limiting what one class
  can do.
""",
        ),
        LessonModule(
            title="D — Dependency Inversion Principle",
            content=r"""
## The idea

> "High-level modules should not depend on low-level modules. Both should
> depend on abstractions. Abstractions should not depend on details;
> details should depend on abstractions." — Robert C. Martin

This is the principle that makes Clean/Hexagonal Architecture possible
(see the next competency). It's also the most commonly misunderstood
letter in SOLID — people conflate it with "dependency injection," which is
a *technique* for achieving DIP, not the principle itself.

## "High-level" and "low-level" — what they actually mean

High-level modules contain policy: business rules, use cases, what the
application is *for*. Low-level modules contain mechanism: how you talk to
Postgres, how you call Stripe's API, how you format an email. The
principle says the business rules should not know or care which database
driver or payment SDK is underneath — that dependency should point the
other way.

## A violation, concretely

```python
class PostgresOrderRepository:
    def save(self, order: Order) -> None:
        # raw psycopg calls...
        ...

class PlaceOrderUseCase:
    def __init__(self) -> None:
        self.repository = PostgresOrderRepository()  # 🚩 concrete dependency

    def execute(self, order: Order) -> None:
        # business rules: validate stock, apply pricing, ...
        self.repository.save(order)
```

`PlaceOrderUseCase` — the high-level policy — directly instantiates and
depends on `PostgresOrderRepository`, a low-level detail. You cannot test
`PlaceOrderUseCase` without a real (or heavily mocked-at-the-SQL-level)
Postgres connection. You cannot swap storage engines without editing the
use case. The dependency arrow points from policy to mechanism — backwards.

## The fix: invert it with an abstraction

```python
class OrderRepository(Protocol):
    def save(self, order: Order) -> None: ...


class PostgresOrderRepository:
    # implements OrderRepository — a detail, depending on the abstraction
    def save(self, order: Order) -> None: ...


class PlaceOrderUseCase:
    def __init__(self, repository: OrderRepository) -> None:
        self.repository = repository  # depends on the abstraction, injected

    def execute(self, order: Order) -> None:
        self.repository.save(order)
```

Now both `PlaceOrderUseCase` (high-level) and `PostgresOrderRepository`
(low-level) depend on `OrderRepository` (the abstraction) — neither
depends on the other directly. `PlaceOrderUseCase` is testable with an
in-memory fake repository in microseconds. Swapping Postgres for DynamoDB
means writing a new class that satisfies `OrderRepository`; the use case
never changes.

## Where the dependency actually gets constructed

Someone still has to build a `PostgresOrderRepository` and hand it to
`PlaceOrderUseCase` — DIP doesn't eliminate that wiring, it moves it to
one place (a composition root / DI container / a `main()`/app-startup
function) instead of scattering `new ConcreteThing()` calls throughout
business logic. In this project, that's `app/api/deps.py` and the FastAPI
`Depends()` system: routers ask for abstractions via type hints, and the
dependency-injection layer supplies concrete instances.

## Key takeaways

- DIP is about the *direction* of source-code dependency: policy defines
  the interface it needs; mechanism implements that interface. The
  interface belongs to (is defined near) the high-level module, not the
  low-level one.
- Dependency injection (passing collaborators in via constructor/function
  parameters instead of instantiating them inline) is the *mechanism* most
  commonly used to satisfy DIP — but DIP is the principle, DI is the tool.
- This is the principle underneath this project's own layering rule:
  services depend on repository *interfaces* in spirit, never on FastAPI
  or a specific driver directly (see docs/ARCHITECTURE.md).
""",
        ),
        LessonModule(
            title="Bringing SOLID Together",
            content=r"""
## Why five separate letters instead of one rule

Each principle attacks a different failure mode of change over time:

| Principle | Fails when... | Symptom |
|---|---|---|
| SRP | one class serves multiple stakeholders | unrelated changes collide in the same file |
| OCP | new variants require editing tested code | growing `if/elif`/`match` on a "kind" |
| LSP | a subtype breaks the base type's contract | surprising bugs only in some subclasses |
| ISP | interfaces bundle unrelated capabilities | `NotImplementedError` in overrides |
| DIP | policy depends on mechanism directly | business logic untestable without infra |

They compound: a class that violates SRP (does persistence *and* business
logic) is much more likely to also violate DIP (business logic now
directly depends on a database driver). Fixing SRP by extracting a
repository interface often fixes DIP as a side effect.

## SOLID is a diagnostic tool, not a checklist to satisfy upfront

The realistic workflow is not "design five abstractions before writing any
code." It's: write the straightforward version first, notice a smell (a
class doing unrelated things, a growing conditional, a subclass that
doesn't fully honor its parent, a fat interface, a use case tightly
coupled to a driver), and *then* apply the relevant letter to fix that
specific pain. Applying all five preemptively to a small CRUD script
produces an unreadable maze of interfaces for behavior that will never
actually vary — that's the well-known "SOLID taken to the extreme" failure
mode, and it's a real cost, not a hypothetical one.

## How this shows up in this project's own codebase

- **SRP**: `backend/app/services/` (business logic) is separate from
  `backend/app/repositories/` (persistence) is separate from
  `backend/app/api/` (HTTP) — see docs/ARCHITECTURE.md.
- **DIP**: FastAPI's `Depends()` mechanism is dependency injection in
  practice — route handlers declare what they need (a `Session`, the
  current user) without constructing it themselves.
- **OCP/ISP**: less prominent in this codebase today because most
  "variation points" (auth methods, storage backends) haven't needed to
  vary yet — a deliberate choice not to abstract prematurely (see
  docs/DECISIONS.md's "avoid unnecessary abstractions" stance).

## Key takeaways

- SOLID principles reinforce each other — fixing one often improves
  another.
- Use them to *diagnose* a smell you're already feeling, not as a design
  ritual to perform before writing the first line of code.
- The cost of applying a principle where it isn't needed is real:
  unnecessary indirection, harder-to-follow code, and interfaces built for
  variation that never materializes.
""",
        ),
    ],
    "design-patterns": [
        LessonModule(
            title="Creational Patterns — Factory Method & Builder",
            content=r"""
## Why creational patterns exist

Object construction is its own source of complexity, separate from what an
object *does* once it exists. Deciding *which* concrete class to build, and
*how* to assemble a complicated one correctly, are concerns that — left
inline at every call site — couple your code to concrete classes and to
construction details that change for their own reasons. Creational patterns
give that concern a dedicated home.

## Factory Method

**Problem**: you have a family of related types, and the exact concrete
type to build depends on runtime data. Left unmanaged, every call site ends
up with its own `if/elif` deciding which class to instantiate.

```python
# Bad — the decision is duplicated everywhere a notifier is needed.
def notify_user(channel: str, message: str, user: User) -> None:
    if channel == "email":
        notifier = EmailNotifier(smtp_config)
    elif channel == "sms":
        notifier = SmsNotifier(twilio_config)
    elif channel == "push":
        notifier = PushNotifier(fcm_config)
    else:
        raise ValueError(f"Unknown channel: {channel}")
    notifier.send(user, message)
```

Every new channel means hunting down every place this `if/elif` was
copy-pasted and adding a branch — the same OCP violation the SOLID modules
covered, now specifically about *construction*.

```python
# Fixed — a single function owns the decision.
def create_notifier(channel: str) -> Notifier:
    if channel == "email":
        return EmailNotifier(smtp_config)
    elif channel == "sms":
        return SmsNotifier(twilio_config)
    elif channel == "push":
        return PushNotifier(fcm_config)
    raise ValueError(f"Unknown channel: {channel}")


def notify_user(channel: str, message: str, user: User) -> None:
    create_notifier(channel).send(user, message)
```

This is what most codebases actually mean by "factory" — a **simple
factory** function centralizing the conditional. The classic Gang-of-Four
Factory Method is stricter: a *virtual method* on a base class that
subclasses override to produce the right variant, so the factory itself
participates in polymorphism rather than switching on a string. In
practice, a registry beats both when the set of variants is genuinely open:

```python
_NOTIFIER_REGISTRY: dict[str, Callable[[], Notifier]] = {
    "email": lambda: EmailNotifier(smtp_config),
    "sms": lambda: SmsNotifier(twilio_config),
    "push": lambda: PushNotifier(fcm_config),
}


def create_notifier(channel: str) -> Notifier:
    try:
        return _NOTIFIER_REGISTRY[channel]()
    except KeyError:
        raise ValueError(f"Unknown channel: {channel}") from None
```

Adding a new channel is now registering an entry, not editing a branch —
the factory itself is closed for modification, open for extension.

## Builder

**Problem**: an object has many parameters, several optional, some
combinations invalid, and a constructor either telescopes into unreadable
overloads or degenerates into a wall of positional booleans (the "boolean
trap" — `HttpRequest(url, True, False, True, None, 30)` tells you nothing
at the call site about what each flag means).

```python
# Bad — what do the positional args even mean at the call site?
request = HttpRequest(
    "https://api.example.com/orders", True, False, True, None, 30
)
```

```python
# Fixed — a fluent builder makes each step self-documenting and lets
# construction be validated incrementally.
class HttpRequestBuilder:
    def __init__(self, url: str) -> None:
        self._url = url
        self._headers: dict[str, str] = {}
        self._body: bytes | None = None
        self._timeout_s: float = 30.0
        self._retry: bool = False

    def with_header(self, key: str, value: str) -> "HttpRequestBuilder":
        self._headers[key] = value
        return self

    def with_body(self, body: bytes) -> "HttpRequestBuilder":
        self._body = body
        return self

    def with_timeout(self, seconds: float) -> "HttpRequestBuilder":
        if seconds <= 0:
            raise ValueError("timeout must be positive")
        self._timeout_s = seconds
        return self

    def with_retry(self, enabled: bool = True) -> "HttpRequestBuilder":
        self._retry = enabled
        return self

    def build(self) -> HttpRequest:
        return HttpRequest(
            url=self._url,
            headers=self._headers,
            body=self._body,
            timeout_s=self._timeout_s,
            retry=self._retry,
        )


request = (
    HttpRequestBuilder("https://api.example.com/orders")
    .with_header("Authorization", f"Bearer {token}")
    .with_body(payload)
    .with_timeout(10)
    .build()
)
```

Each `with_*` call is self-describing, invalid values (a negative timeout)
are rejected at the step that sets them rather than deep inside some other
method, and `build()` returns a single, ideally immutable, fully-formed
object — there's no half-constructed state visible to callers. The classic
GoF Builder also has a separate `Director` class that encodes *specific*
construction recipes; in practice, most Python/TypeScript codebases skip
the director and just call builder methods directly where needed, which is
a reasonable simplification when there's no recurring, reusable recipe to
name.

## Key takeaways

- Factory Method centralizes "which concrete class do I build" so the
  decision lives in one place instead of being copy-pasted at every call
  site; a registry-backed factory keeps it open for extension without
  editing existing branches.
- Builder replaces telescoping constructors and boolean-trap parameter
  lists with a fluent, step-validated construction sequence that produces
  one fully-formed, ideally immutable object.
- Both patterns exist to keep "how do I build this" separate from "what
  does this do" — the same separation-of-concerns instinct behind SRP,
  applied specifically to object creation.
""",
        ),
        LessonModule(
            title="Structural Patterns — Adapter & Decorator",
            content=r"""
## Why structural patterns exist

Structural patterns are about composing existing classes and objects into
larger structures without changing what they already do — reshaping an
interface (Adapter) or layering new behavior onto an existing interface
(Decorator), instead of rewriting or subclassing the original.

## Adapter

**Problem**: you need to integrate code written against one interface
(often third-party or legacy, which you cannot change) with code that
expects a different interface, and modifying either side isn't an option.

```python
# The interface your application code depends on.
class PaymentGateway(Protocol):
    def charge(self, amount: Decimal, currency: str) -> ChargeResult: ...


# A legacy/third-party client with an incompatible shape — different
# method name, amounts in integer cents, no currency parameter (assumes
# USD), and a differently-shaped result.
class LegacyBillingClient:
    def do_charge(self, amount_cents: int) -> dict[str, str]:
        ...  # returns {"status": "ok", "ref": "..."} or raises LegacyBillingError
```

Without an adapter, either `PaymentGateway`'s contract gets compromised to
match the legacy shape (leaking legacy details into every caller), or the
legacy client gets modified directly (often impossible — it's a vendored
dependency).

```python
# Fixed — adapt the legacy shape to the interface the app already uses.
class LegacyBillingAdapter:
    def __init__(self, client: LegacyBillingClient) -> None:
        self._client = client

    def charge(self, amount: Decimal, currency: str) -> ChargeResult:
        if currency != "USD":
            raise UnsupportedCurrencyError(currency)
        cents = int(amount * 100)
        try:
            raw = self._client.do_charge(cents)
        except LegacyBillingError as exc:
            raise PaymentFailedError(str(exc)) from exc
        return ChargeResult(reference=raw["ref"], succeeded=raw["status"] == "ok")
```

Every caller depends only on `PaymentGateway`; swapping the legacy client
for a modern one later means writing a new adapter, not touching call
sites. Adapter is easy to confuse with **Facade** — the distinction: an
Adapter makes an *existing* interface match one callers already expect
(translation), while a Facade introduces a *new*, simpler interface in
front of a complex subsystem (simplification). They can overlap in
practice, but the intent differs.

## Decorator

**Problem**: you need to add responsibilities to an object — caching,
logging, retries, rate limiting — dynamically or in composable
combinations, without a subclass explosion.

```python
# Bad — one subclass per combination of concerns needed.
class CachingOrderRepository(OrderRepository): ...
class LoggingOrderRepository(OrderRepository): ...
class CachingLoggingOrderRepository(OrderRepository): ...  # 🚩 combinatorial
class RetryingCachingLoggingOrderRepository(OrderRepository): ...  # 🚩🚩
```

Every new cross-cutting concern multiplies the number of subclasses needed
to cover every combination callers might want.

```python
# Fixed — each decorator wraps the same interface and adds one concern.
class CachingOrderRepository:
    def __init__(self, wrapped: OrderRepository, cache: Cache) -> None:
        self._wrapped = wrapped
        self._cache = cache

    def get(self, order_id: UUID) -> Order:
        if cached := self._cache.get(str(order_id)):
            return cached
        order = self._wrapped.get(order_id)
        self._cache.set(str(order_id), order)
        return order


class LoggingOrderRepository:
    def __init__(self, wrapped: OrderRepository, logger: Logger) -> None:
        self._wrapped = wrapped
        self._logger = logger

    def get(self, order_id: UUID) -> Order:
        self._logger.info("fetching order %s", order_id)
        return self._wrapped.get(order_id)


# Stack whichever concerns a given call site needs, in whatever order:
repository = LoggingOrderRepository(
    CachingOrderRepository(PostgresOrderRepository(db), cache), logger
)
```

Because every decorator implements and wraps the *same* `OrderRepository`
interface, they compose freely — `N` concerns need `N` decorator classes,
not `2^N` subclasses. This is also exactly why Adapter and Decorator are
easy to conflate structurally (both wrap an object): Adapter changes the
*interface*; Decorator preserves the interface and adds *behavior*.

Python's `@decorator` function syntax is a lightweight, language-level
cousin of this same idea applied to functions rather than objects — a
decorator wraps a callable and returns something honoring the same calling
convention while adding behavior around it (timing, caching via
`functools.lru_cache`, retries). The GoF pattern is the same idea scaled up
to stateful objects behind a shared interface.

## Key takeaways

- Adapter translates an incompatible interface into the one your code
  already depends on, without modifying either side — essential for
  integrating legacy or third-party code cleanly.
- Decorator adds behavior around an existing interface by wrapping it, and
  because every decorator honors the same interface, they stack
  compositionally instead of multiplying subclasses.
- Both patterns favor composition over inheritance — the underlying theme
  connecting most of the structural patterns.
""",
        ),
        LessonModule(
            title="Behavioral Patterns — Strategy & Observer",
            content=r"""
## Why behavioral patterns exist

Behavioral patterns govern how objects communicate and how responsibility
for an algorithm or a reaction to an event is assigned. The two most used
in everyday backend work are Strategy (swap an algorithm at runtime) and
Observer (notify interested parties without coupling to them directly).

## Strategy

**Problem**: you have several interchangeable algorithms for the same
task, and need to select one at runtime without a growing conditional.

If this sounds familiar, it should — it's the exact shape of the fix shown
in the SOLID competency's Open/Closed Principle module. `DiscountPolicy`
with `RegularDiscount`, `PremiumDiscount`, and `VipDiscount` *is* the
Strategy pattern: OCP names the *principle* being satisfied, Strategy names
the *pattern* that satisfies it.

```python
class PricingStrategy(Protocol):
    def price(self, cart: Cart) -> Decimal: ...


class StandardPricing:
    def price(self, cart: Cart) -> Decimal:
        return cart.subtotal()


class BulkDiscountPricing:
    def price(self, cart: Cart) -> Decimal:
        discount = Decimal("0.05") if cart.item_count() >= 10 else Decimal("0")
        return cart.subtotal() * (1 - discount)


class CheckoutService:
    def __init__(self, pricing: PricingStrategy) -> None:
        self._pricing = pricing

    def total_due(self, cart: Cart) -> Decimal:
        return self._pricing.price(cart)
```

`CheckoutService` doesn't know or care which concrete pricing algorithm it
holds — it depends on the `PricingStrategy` abstraction, and the concrete
strategy is injected (or selected via a factory from the previous module).
A/B testing a new pricing algorithm becomes "construct `CheckoutService`
with a different strategy," not "edit `CheckoutService`."

## Observer

**Problem**: one object's state change needs to trigger reactions in
several other objects, but those reactions shouldn't be hard-coded into
the object whose state changed — that would couple a core domain operation
to every downstream concern that currently cares about it, and to every
future one.

```python
# Bad — OrderService knows about, and directly depends on, every
# downstream concern that currently reacts to a placed order.
class OrderService:
    def __init__(
        self,
        repo: OrderRepository,
        mailer: EmailService,
        inventory: InventoryService,
        analytics: AnalyticsClient,
    ) -> None:
        ...

    def place_order(self, order: Order) -> None:
        self._repo.save(order)
        self._mailer.send_confirmation(order)       # 🚩 unrelated concern
        self._inventory.decrement_stock(order)       # 🚩 unrelated concern
        self._analytics.track("order_placed", order)  # 🚩 unrelated concern
```

Adding a fourth reaction (say, a loyalty-points award) means editing
`OrderService` again — and `OrderService` now has four reasons to change,
an SRP violation caused directly by *not* using Observer.

```python
# Fixed — OrderService publishes a fact; it doesn't know who's listening.
class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[type, list[Callable[[object], None]]] = {}

    def subscribe(self, event_type: type, handler: Callable[[object], None]) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def publish(self, event: object) -> None:
        for handler in self._subscribers.get(type(event), []):
            handler(event)


@dataclass(frozen=True)
class OrderPlaced:
    order_id: UUID
    total: Decimal


class OrderService:
    def __init__(self, repo: OrderRepository, bus: EventBus) -> None:
        self._repo = repo
        self._bus = bus

    def place_order(self, order: Order) -> None:
        self._repo.save(order)
        self._bus.publish(OrderPlaced(order.id, order.total))


# Wired up once, at startup — not inside OrderService:
bus.subscribe(OrderPlaced, lambda e: mailer.send_confirmation(e.order_id))
bus.subscribe(OrderPlaced, lambda e: inventory.decrement_stock(e.order_id))
bus.subscribe(OrderPlaced, lambda e: analytics.track("order_placed", e))
```

`OrderService` now has exactly one reason to change: how orders are
placed. Adding loyalty points is a new subscriber, added at the wiring
point, never touching `OrderService`. This in-process pattern is the same
idea underlying distributed pub/sub systems (Kafka topics, SNS/SQS,
webhooks) — the scale changes, the decoupling principle doesn't.

**The real cost, honestly stated**: Observer trades explicit control flow
for implicit control flow. Reading `place_order` no longer tells you
everything that happens when an order is placed — you have to know to go
look at subscribers. Debugging "why didn't the confirmation email send"
means chasing a subscription instead of following a call stack. If one
subscriber throws and isn't isolated, it can silently break unrelated
reactions or crash the publisher depending on how `publish` handles
exceptions. Use it where the decoupling is worth that cost — genuinely
independent concerns reacting to a domain fact — not as a way to avoid
writing a four-line function call.

## Key takeaways

- Strategy makes an algorithm swappable at runtime behind a shared
  interface — it's the concrete pattern name for the OCP fix already shown
  in the SOLID competency.
- Observer decouples a state change from its reactions: the publisher
  states a fact, subscribers decide what to do about it, and neither knows
  about the other's concrete type.
- Observer's cost is implicit control flow — harder to trace, harder to
  debug, easier for one bad subscriber to affect others. Reach for it when
  reactions are genuinely independent concerns, not by default.
- Across all of design patterns: they are names for recurring solutions to
  recurring forces (usually favoring composition and abstraction over
  inheritance and conditionals), not a checklist to apply preemptively.
""",
        ),
    ],
    "clean-architecture": [
        LessonModule(
            title="The Dependency Rule and the Layers",
            content=r"""
## The core idea

Clean Architecture (Robert C. Martin's synthesis of Hexagonal, Onion, and
similar layered architectures) arranges code in concentric layers and
enforces one rule above all others:

> "Source code dependencies must point only inward." — the Dependency Rule

Nothing in an inner layer may import, reference, or know about anything in
an outer layer. Outer layers depend on inner ones; inner layers depend on
nothing but themselves (and, where needed, on abstractions they define).

## The layers, inside out

1. **Entities** — enterprise-wide business rules and data structures that
   would exist even if this specific application didn't (e.g. what an
   `Order` fundamentally *is* and the invariants it must always satisfy).
2. **Use Cases** — application-specific business rules: the orchestration
   of entities to accomplish a specific task ("place an order," "cancel a
   subscription"). This layer knows *what* the application does.
3. **Interface Adapters** — controllers, presenters, and gateways that
   translate between the use case layer's shape and the outside world's
   shape (an HTTP request becomes a use-case input DTO; a use case's result
   becomes a JSON response).
4. **Frameworks & Drivers** — the outermost layer: the web framework,
   the database driver, the UI, third-party SDKs. Deliberately treated as
   *details* — plugins to the business logic, not the foundation it's
   built on.

## Why "the web is a detail" is the load-bearing claim here

The controversial-sounding claim behind this architecture is that your web
framework, your database, and your ORM are implementation details — not
the skeleton the application is built around. Most codebases get this
backwards:

```python
# Bad — business rules live inside a framework-coupled view function,
# entangled with HTTP concerns and direct ORM access.
@app.post("/orders")
def create_order(request: Request, db: Session = Depends(get_db)):
    body = request.json()
    if body["quantity"] <= 0:
        return JSONResponse({"error": "invalid quantity"}, status_code=400)
    product = db.query(ProductModel).filter_by(id=body["product_id"]).first()
    if product.stock < body["quantity"]:
        return JSONResponse({"error": "insufficient stock"}, status_code=409)
    order = OrderModel(product_id=product.id, quantity=body["quantity"])
    product.stock -= body["quantity"]
    db.add(order)
    db.commit()
    return JSONResponse({"id": str(order.id)}, status_code=201)
```

There is no way to test "insufficient stock is rejected" without spinning
up FastAPI's request/response machinery and a real (or heavily mocked)
database session — the business rule and the delivery mechanism are one
inseparable blob. Upgrading the web framework, or moving from SQLAlchemy
to a different ORM, means editing the same function that contains the
stock-check rule.

```python
# Fixed — the use case is framework-free; the route is a thin adapter.
class PlaceOrderUseCase:
    def __init__(self, products: ProductRepository, orders: OrderRepository) -> None:
        self._products = products
        self._orders = orders

    def execute(self, product_id: UUID, quantity: int) -> Order:
        if quantity <= 0:
            raise InvalidQuantityError(quantity)
        product = self._products.get(product_id)
        if product.stock < quantity:
            raise InsufficientStockError(product_id)
        product.stock -= quantity
        order = Order.new(product_id=product_id, quantity=quantity)
        self._products.save(product)
        self._orders.save(order)
        return order


# The FastAPI route is now a translator: HTTP in, use case, HTTP out.
@router.post("/orders", status_code=201)
def create_order(body: CreateOrderRequest, use_case: PlaceOrderUseCase = Depends(...)):
    try:
        order = use_case.execute(body.product_id, body.quantity)
    except InvalidQuantityError:
        raise HTTPException(400, "invalid quantity")
    except InsufficientStockError:
        raise HTTPException(409, "insufficient stock")
    return OrderResponse.from_domain(order)
```

`PlaceOrderUseCase` can be unit tested with in-memory fake repositories —
no FastAPI, no database, milliseconds per test. Swapping FastAPI for
another framework, or Postgres for another store, touches the outer
layers only; the rule that "you can't order more than is in stock" never
moves.

## This project's own shape

This isn't an academic exercise for this codebase specifically — the
backend's own `api -> services -> repositories -> models` layering (see
`docs/ARCHITECTURE.md`) is the same Dependency Rule with different layer
names: routers (interface adapters) never touch the ORM directly, services
(use cases) contain the business logic and never import FastAPI, and
repositories (gateways) are the only code that speaks SQLAlchemy.

## Key takeaways

- The Dependency Rule: source-code dependencies point inward only; inner
  layers (business rules) never know about outer layers (frameworks, DBs,
  UI).
- Treating the framework and database as "details" is what makes business
  rules unit-testable in isolation and makes the framework/DB replaceable
  without touching business logic.
- The classic smell this fixes: business rules embedded directly in
  request handlers or ORM models, indistinguishable from HTTP or
  persistence concerns.
- This project's `api -> services -> repositories -> models` layering is a
  direct, concrete instance of this same rule.
""",
        ),
        LessonModule(
            title="Ports & Adapters, Concretely",
            content=r"""
## Hexagonal architecture in one paragraph

Alistair Cockburn's Ports & Adapters (Hexagonal) architecture predates
Clean Architecture and expresses the same Dependency Rule from a different
angle: draw the application core as a hexagon (the shape is arbitrary —
the point is "a boundary with more than one side"). The core defines
**ports** — interfaces describing what it needs from the outside world and
what it offers to the outside world. **Adapters** sit outside the hexagon
and implement those ports for a specific technology. Nothing outside the
hexagon is allowed to be referenced *inside* it.

## Driving (primary) vs. driven (secondary) ports

- **Driving/primary ports**: ways the outside world triggers the
  application — an HTTP controller, a CLI command, a scheduled job handler.
  These *call into* the core.
- **Driven/secondary ports**: things the core needs and reaches out for —
  a repository, a payment gateway, an email sender. The core defines the
  interface; adapters outside implement it. These are *called by* the
  core.

```python
# ports.py — owned by the application core. No framework or driver
# imports here — this file is pure interface.

class OrderRepository(Protocol):
    # secondary port: something the core needs from persistence
    def get(self, order_id: UUID) -> Order: ...
    def save(self, order: Order) -> None: ...


class PaymentGateway(Protocol):
    # secondary port: something the core needs from an external service
    def charge(self, amount: Decimal, currency: str) -> ChargeResult: ...


class PlaceOrderPort(Protocol):
    # primary port: what the core offers to the outside world
    def place_order(self, customer_id: UUID, items: list[LineItem]) -> Order: ...
```

```python
# core/use_cases.py — implements the primary port, depends only on the
# secondary ports (interfaces), never on concrete adapters.

class PlaceOrderUseCase:
    def __init__(self, orders: OrderRepository, payments: PaymentGateway) -> None:
        self._orders = orders
        self._payments = payments

    def place_order(self, customer_id: UUID, items: list[LineItem]) -> Order:
        order = Order.new(customer_id, items)
        result = self._payments.charge(order.total, order.currency)
        if not result.succeeded:
            raise PaymentFailedError(result.reference)
        self._orders.save(order)
        return order
```

```python
# adapters/postgres_orders.py — a driven-side adapter, outside the core,
# implementing OrderRepository for a specific database.

class PostgresOrderRepository:  # implements OrderRepository
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, order_id: UUID) -> Order:
        ...

    def save(self, order: Order) -> None:
        ...


# adapters/http_orders.py — a driving-side adapter, translating HTTP
# into a call on the primary port.

@router.post("/orders")
def create_order(body: CreateOrderRequest, use_case: PlaceOrderPort = Depends(...)):
    order = use_case.place_order(body.customer_id, body.items)
    return OrderResponse.from_domain(order)
```

## What this buys you in practice

- **Testing the core needs zero infrastructure.** An in-memory fake
  implementing `OrderRepository` and a fake `PaymentGateway` that always
  succeeds (or always fails, for the error-path test) let you test
  `PlaceOrderUseCase` completely without a database or a real payment
  provider.
- **Swapping a driven adapter is isolated.** Moving from Postgres to
  DynamoDB, or from Stripe to Adyen, means writing one new adapter class
  against the existing port — the use case and every other adapter are
  untouched.
- **Adding a new driving adapter doesn't touch the core.** Exposing the
  same use case over a CLI, a gRPC endpoint, or a message-queue consumer
  in addition to HTTP means writing a new driving adapter that calls
  `PlaceOrderPort` — the core has no idea how many ways in there are.

This is Dependency Inversion (the SOLID competency's "D") applied at the
scale of an entire application: the core defines the ports it needs, and
every detail — database, payment provider, delivery mechanism — depends on
those ports rather than the other way around.

## Key takeaways

- Ports are interfaces defined by the application core; adapters are
  implementations of those interfaces living outside the core.
- Driving/primary ports are called *by* the outside world into the core;
  driven/secondary ports are called *by* the core out into the world — the
  core defines both, regardless of which direction the call travels.
- The practical payoff: the core is testable with fakes and swappable at
  every technology boundary, because every boundary is an interface the
  core owns, not a concrete class it reaches for.
""",
        ),
        LessonModule(
            title="Worked Example: Refactoring Out of Framework Coupling",
            content=r"""
## Starting point: everything in one framework-coupled function

This is a realistic starting shape — the kind of code a CRUD feature
accretes into once "just get it working" wins a few times in a row.

```python
# Bad — framework I/O, business rules, persistence, and notification are
# all interleaved in one function.
@app.post("/bookings")
def book_room(request: Request, db: Session = Depends(get_db)):
    body = request.json()
    room = db.query(RoomModel).get(body["room_id"])
    overlapping = (
        db.query(BookingModel)
        .filter(BookingModel.room_id == room.id)
        .filter(BookingModel.start < body["end"])
        .filter(BookingModel.end > body["start"])
        .count()
    )
    if overlapping > 0:
        return JSONResponse({"error": "room already booked"}, status_code=409)

    booking = BookingModel(
        room_id=room.id, start=body["start"], end=body["end"]
    )
    db.add(booking)
    db.commit()

    smtp = smtplib.SMTP("smtp.example.com")
    smtp.sendmail(
        "bookings@example.com",
        body["customer_email"],
        f"Subject: Confirmed\n\nRoom {room.name} booked.",
    )
    return JSONResponse({"id": str(booking.id)}, status_code=201)
```

The overlap-checking rule — arguably the single most important business
rule in this whole feature — is buried inside a raw SQL query, inline with
HTTP parsing and inline with an SMTP call. Testing it means standing up a
database, and probably mocking `smtplib` so tests don't actually send
email.

## Step 1: extract the domain rule into an entity

```python
# domain/booking.py — no framework, no database, no SMTP.
@dataclass(frozen=True)
class Booking:
    id: UUID
    room_id: UUID
    start: datetime
    end: datetime

    def overlaps(self, other_start: datetime, other_end: datetime) -> bool:
        return self.start < other_end and other_end > self.start > self.end
```

(Bug intentionally left visible in the paragraph below — see "why tests
matter" further down.)

## Step 2: define the ports the use case needs

```python
# domain/ports.py
class RoomRepository(Protocol):
    def get(self, room_id: UUID) -> Room: ...


class BookingRepository(Protocol):
    def find_overlapping(self, room_id: UUID, start: datetime, end: datetime) -> list[Booking]: ...
    def save(self, booking: Booking) -> None: ...


class NotificationSender(Protocol):
    def send_confirmation(self, email: str, booking: Booking, room: Room) -> None: ...
```

## Step 3: the use case, framework-free

```python
# domain/use_cases.py
class BookRoomUseCase:
    def __init__(
        self,
        rooms: RoomRepository,
        bookings: BookingRepository,
        notifier: NotificationSender,
    ) -> None:
        self._rooms = rooms
        self._bookings = bookings
        self._notifier = notifier

    def execute(
        self, room_id: UUID, start: datetime, end: datetime, customer_email: str
    ) -> Booking:
        room = self._rooms.get(room_id)
        if self._bookings.find_overlapping(room_id, start, end):
            raise RoomAlreadyBookedError(room_id)
        booking = Booking(id=uuid4(), room_id=room_id, start=start, end=end)
        self._bookings.save(booking)
        self._notifier.send_confirmation(customer_email, booking, room)
        return booking
```

## Step 4: adapters, and a thin route

```python
# adapters/sql_bookings.py
class SqlBookingRepository:  # implements BookingRepository
    def __init__(self, session: Session) -> None: ...
    def find_overlapping(self, room_id, start, end) -> list[Booking]: ...
    def save(self, booking: Booking) -> None: ...

# adapters/smtp_notifier.py
class SmtpNotificationSender:  # implements NotificationSender
    def send_confirmation(self, email, booking, room) -> None: ...

# api/bookings.py — pure translation, no business logic left.
@router.post("/bookings", status_code=201)
def book_room(body: BookRoomRequest, use_case: BookRoomUseCase = Depends(...)):
    try:
        booking = use_case.execute(body.room_id, body.start, body.end, body.email)
    except RoomAlreadyBookedError:
        raise HTTPException(409, "room already booked")
    return BookingResponse.from_domain(booking)
```

## Why this refactor actually pays for itself

Testing `BookRoomUseCase.execute` now takes an in-memory `BookingRepository`
fake and a stub `NotificationSender` that just records what it was called
with — no database, no SMTP server, tests run in milliseconds. That
matters concretely here: `Booking.overlaps` above has a real bug (`start >
self.end` should almost certainly be `other_start < self.end`, and the
comparison operators are chained in a way that doesn't express the
intended interval-overlap check) — exactly the kind of bug a two-line unit
test against the isolated entity catches immediately, and that stays
hidden indefinitely inside a hard-to-exercise, framework-entangled query.

## The honest trade-off

This is more files and more indirection than the original one-function
version. For a genuinely simple CRUD admin panel with no real invariants
to protect, that indirection is pure cost with no payoff — a thin, direct
route is the *better* engineering choice there. This refactor earns its
keep specifically because there's a non-trivial business rule
(overlap-checking) and multiple external integrations (DB, email) that
benefit from being independently testable and independently replaceable.
Apply this shape where that's true; don't apply it reflexively everywhere.

## Key takeaways

- Refactor by pulling the domain rule out first (entity), then the ports
  the use case needs (interfaces), then the use case itself, then make
  existing code the adapters behind those ports.
- The payoff is concrete, not theoretical: isolated business logic is what
  makes a real bug like a broken overlap check catchable by a fast,
  infrastructure-free unit test.
- This pattern has a real cost in files and indirection — worth it when
  there's a genuine business rule and multiple external integrations to
  isolate, not worth it for simple CRUD with no real invariants.
""",
        ),
    ],
    "domain-driven-design": [
        LessonModule(
            title="Entities vs. Value Objects",
            content=r"""
## The distinction

- An **Entity** has identity that persists through time and through
  attribute changes. Two entities are equal if and only if their
  identities match — even if every other attribute differs, or even if
  every attribute is currently identical, two entities with different IDs
  are different things.
- A **Value Object** has no identity. It is entirely defined by its
  attributes, is (ideally) immutable, and two value objects with the same
  attributes are simply *the same value* — equality by value, not by
  reference or ID.

A `Customer` is an entity: it has one identity that persists across name
changes, address changes, and email changes — it's still "that customer."
A `Money` amount, an `Address`, a `DateRange`, an `EmailAddress` are value
objects — there's no meaningful sense in which "this $50" is a different
individual from "that $50"; they're just equal.

## The bug value objects prevent: primitive obsession

```python
# Bad — money represented as scattered primitives. Nothing stops mixing
# currencies, and every call site has to independently remember to check.
class Order:
    def __init__(self, amount: Decimal, currency: str) -> None:
        self.amount = amount
        self.currency = currency


def add_line_items(
    a_amount: Decimal, a_currency: str, b_amount: Decimal, b_currency: str
) -> Decimal:
    return a_amount + b_amount  # 🚩 silently wrong if currencies differ
```

Nothing in the type system stops `add_line_items(Decimal("10"), "USD",
Decimal("10"), "EUR")` from silently returning `20` of an unstated,
meaningless currency. The invariant "you can't add mismatched currencies"
exists only as a convention someone has to remember at every call site.

```python
# Fixed — Money is a value object; the invariant lives in one place.
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __add__(self, other: "Money") -> "Money":
        if other.currency != self.currency:
            raise CurrencyMismatchError(self.currency, other.currency)
        return Money(self.amount + other.amount, self.currency)

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Money cannot be negative")
```

`Money(Decimal("-5"), "USD")` cannot exist — the invariant is enforced at
construction, not hoped for at every use. `frozen=True` gives value
equality and hashability for free via the dataclass-generated `__eq__`,
and immutability means a `Money` value can be freely shared, cached, or
passed around without anyone worrying it'll be mutated out from under
them. This is "making illegal states unrepresentable" — a value object
that can only be constructed in a valid state removes an entire category
of bug from every place that uses it.

## Entities: identity, not attribute equality

```python
@dataclass
class Customer:
    id: UUID
    name: str
    email: str

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Customer) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
```

Two `Customer` instances with the same `id` are the same customer even if
`name` differs because one object holds stale, not-yet-refreshed data.
Two `Customer` instances with different `id`s are different customers even
if `name` and `email` are, coincidentally, identical strings — a default
dataclass `__eq__` (which compares *all* fields) would get this backwards,
which is why identity-based entities need `__eq__` overridden explicitly
rather than left at the dataclass default.

## Why the distinction matters in practice

Mistaking a value object for an entity means giving something an ID it
doesn't need, tracking "the same" `Address` across mutations that should
instead just produce a new `Address`, and losing the free equality/hashing
value semantics give you. Mistaking an entity for a value object means
comparing customers by attributes and getting `False` for the same
customer mid-update, or `True` for two different customers who happen to
share a name. Most primitive-obsession bugs in real codebases — currency
mismatches, comparing raw UUID strings vs. UUID objects, unvalidated email
strings passed where a validated one was assumed — are value-object
problems wearing a primitive-type disguise.

## Key takeaways

- Entities are compared by identity (an ID); value objects are compared by
  value (all attributes) and should be immutable.
- Value objects should validate their own invariants at construction time
  — an invalid value object should be impossible to create, not just
  discouraged.
- Primitive obsession (raw `Decimal`+`str` instead of `Money`, raw `str`
  instead of `EmailAddress`) is what value objects are the direct fix for.
- Never let a dataclass's default all-fields `__eq__` apply to an entity —
  override it to compare identity only.
""",
        ),
        LessonModule(
            title="Aggregates and Aggregate Roots",
            content=r"""
## The problem aggregates solve

A single business operation often needs to keep several objects
consistent with each other. An `Order` and its `OrderLine`s must agree on
a total; you can't let a caller reach in and mutate an `OrderLine`'s
quantity directly without the `Order`'s total, and any invariant depending
on it, immediately going stale or invalid. An **aggregate** is a cluster
of entities and value objects treated as a single unit for the purpose of
data changes — a **consistency boundary**. The **aggregate root** is the
one entity through which all external access and mutation must go; nothing
outside the aggregate is allowed to hold a reference to, or directly call
mutators on, the aggregate's internal entities.

## A violation: anemic internals reachable from outside

```python
# Bad — OrderLine is directly mutable from application/service code,
# bypassing any invariant Order might want to enforce.
class OrderLine:
    def __init__(self, product_id: UUID, quantity: int, unit_price: Decimal) -> None:
        self.product_id = product_id
        self.quantity = quantity
        self.unit_price = unit_price


class Order:
    def __init__(self, id: UUID, lines: list[OrderLine], status: str) -> None:
        self.id = id
        self.lines = lines
        self.status = status


# Some service, anywhere in the codebase:
def apply_quantity_change(order: Order, line_index: int, new_quantity: int) -> None:
    order.lines[line_index].quantity = new_quantity  # 🚩 direct mutation
    # 🚩 nothing stops this from running against a "shipped" order
    # 🚩 nothing recalculates or re-validates the order's total
```

Any code anywhere can reach into `order.lines` and mutate a line directly,
completely bypassing whatever rule says "you can't change a shipped
order's contents" or "quantity must stay positive." The invariant exists
nowhere in the code — it exists only as an assumption in whoever wrote
`apply_quantity_change`, and the next person to touch this won't know it's
there.

## The fix: the aggregate root owns all mutation

```python
class OrderLine:
    def __init__(self, product_id: UUID, quantity: int, unit_price: Decimal) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self.product_id = product_id
        self.quantity = quantity
        self.unit_price = unit_price

    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


class Order:
    def __init__(self, id: UUID, lines: list[OrderLine], status: OrderStatus) -> None:
        self._id = id
        self._lines = lines  # internal — no public setter exposes this list
        self._status = status

    @property
    def id(self) -> UUID:
        return self._id

    def total(self) -> Decimal:
        return sum((line.subtotal() for line in self._lines), Decimal("0"))

    def change_line_quantity(self, product_id: UUID, new_quantity: int) -> None:
        if self._status is OrderStatus.SHIPPED:
            raise OrderAlreadyShippedError(self._id)
        line = self._find_line(product_id)
        line.quantity = new_quantity  # only reachable through this method
```

Every mutation of the order's internals goes through `Order`, so
`Order.change_line_quantity` is the *only* place the "can't modify a
shipped order" rule needs to be enforced — and it's structurally
impossible to bypass, because nothing outside `Order` has a way to reach
`OrderLine.quantity` except through this method.

## Sizing aggregates, and referencing across them

Two practical rules keep aggregates useful instead of becoming a tangled
mega-object:

1. **Keep aggregates small.** A `Customer` aggregate shouldn't contain
   every `Order` that customer ever placed — that would mean loading a
   customer's entire order history to change their email address. `Order`
   is its own aggregate; `Customer` references it (and is referenced by
   it) by ID only.
2. **Reference other aggregates by ID, not by object.** `Order` holds a
   `customer_id: UUID`, not a `customer: Customer` object reference. This
   keeps aggregate boundaries honest — you can't accidentally reach from
   inside one aggregate's consistency boundary into another's — and it's
   what allows different aggregates to be updated in separate transactions
   (eventual consistency between them, strict consistency within each).

The corollary in the repository layer: **only aggregate roots get
repositories.** There is an `OrderRepository`; there is no
`OrderLineRepository` — `OrderLine`s are only ever saved, loaded, and
queried as part of loading and saving their `Order`.

## Key takeaways

- An aggregate is a consistency boundary — a cluster of objects that must
  stay valid together, mutated only through its aggregate root.
- Internal entities of an aggregate should not be directly mutable from
  outside; every mutation goes through a method on the root that can
  enforce the aggregate's invariants.
- Keep aggregates small; reference other aggregates by ID, not by direct
  object reference, so each aggregate can be its own transaction boundary.
- Only aggregate roots get repositories — internal entities are persisted
  as part of their root, never independently.
""",
        ),
        LessonModule(
            title="Bounded Contexts and Ubiquitous Language",
            content=r"""
## Ubiquitous language

DDD's starting premise is that the gap between "how domain experts talk
about the business" and "what the code calls things" is where
misunderstandings, and eventually bugs, come from. **Ubiquitous language**
is the discipline of using the same vocabulary — the same nouns and verbs
— in conversations with domain experts, in documentation, and in the code
itself (class names, method names, variable names), so that "the business
calls it X" and "the code calls it X" are never two different things
requiring mental translation.

If domain experts say "the order is *fulfilled*, not *shipped*, until the
customer has actually received it," and the codebase has a `status =
"shipped"` field driving fulfillment logic, that's not a naming nitpick —
it's a sign the model in the code doesn't match the model in the business,
and the next person to extend either will be reasoning about the wrong
thing.

## Bounded contexts

In any system beyond toy size, a single word means genuinely different
things to different parts of the business — and DDD's answer is not to
force one unified definition, but to draw an explicit boundary, a
**bounded context**, within which one model and one meaning apply
consistently, and to accept that the same word can mean something else in
a different bounded context.

Take "Product" in an e-commerce system:

- In the **Catalog** context: a `Product` has a description, images,
  category, and searchable attributes.
- In the **Pricing** context: a `Product` has price tiers, active
  discounts, and currency-specific pricing rules — none of which the
  catalog cares about.
- In the **Shipping** context: a `Product` has weight, dimensions, and a
  hazmat flag — none of which pricing or catalog cares about.

```python
# Bad — one "God model" trying to serve every context at once.
class Product:
    id: UUID
    name: str
    description: str
    images: list[str]
    category: str
    price_tiers: list[PriceTier]
    active_discounts: list[Discount]
    weight_kg: float
    dimensions_cm: tuple[float, float, float]
    hazmat: bool
    # ... growing indefinitely as every team bolts on their fields
```

Every team touches this one class for unrelated reasons (the SRP violation
from the very first competency in this subject, now at the scale of an
entire domain model). Merge conflicts, accidental coupling ("pricing" code
breaking because "shipping" added a required field), and a model that
means everything and therefore clarifies nothing are the result.

```python
# Fixed — each bounded context has its own Product model, shaped for
# exactly what that context needs, linked by a shared identifier only.
# catalog/product.py
class CatalogProduct:
    id: UUID
    name: str
    description: str
    images: list[str]
    category: str

# pricing/product.py
class PricingProduct:
    id: UUID  # same identifier, different context, different shape
    price_tiers: list[PriceTier]
    active_discounts: list[Discount]

# shipping/product.py
class ShippableProduct:
    id: UUID
    weight_kg: float
    dimensions_cm: tuple[float, float, float]
    hazmat: bool
```

Each context's `Product` is complete for what that context does, and none
of them carry fields that are meaningless noise to their own logic.

## Context mapping: the anticorruption layer

When one bounded context has to integrate with another system — especially
a legacy system or a third party you don't control — the risk is that the
foreign system's model leaks into your own, corrupting your bounded
context's clean vocabulary with someone else's. The standard defense is an
**anticorruption layer (ACL)**: a translation boundary that converts the
external model into your own domain's model at the edge, so nothing
downstream of the ACL ever sees the foreign shape.

```python
# Legacy inventory system returns this shape — not our vocabulary.
# {"itm_cd": "SKU123", "qty_oh": 42, "wh_loc": "A-14-B"}

class LegacyInventoryAcl:
    def __init__(self, legacy_client: LegacyInventoryClient) -> None:
        self._client = legacy_client

    def get_stock_level(self, sku: str) -> StockLevel:
        raw = self._client.fetch(sku)
        # Translate legacy vocabulary into our own domain's vocabulary —
        # this is the only place that ever sees "itm_cd" / "qty_oh".
        return StockLevel(
            sku=raw["itm_cd"], quantity_on_hand=raw["qty_oh"], warehouse=raw["wh_loc"]
        )
```

This is Adapter (from the design-patterns competency) applied specifically
to protect a bounded context's ubiquitous language from a foreign one.

## Key takeaways

- Ubiquitous language means the business's vocabulary and the code's
  vocabulary are the same words, checked continuously against how domain
  experts actually talk.
- A bounded context is an explicit boundary within which one model and one
  meaning hold consistently — the same word (like "Product") can and often
  should mean different things in different bounded contexts.
- Forcing one unified model to serve every context is the DDD version of
  an SRP violation at the scale of an entire domain — it accretes
  unrelated fields and couples unrelated teams.
- An anticorruption layer translates a foreign system's model into your
  own at the boundary, so your bounded context's language never gets
  contaminated by someone else's.
""",
        ),
        LessonModule(
            title="Strategic vs. Tactical DDD — and When Not to Use It",
            content=r"""
## Two different levels of DDD

- **Strategic DDD** operates at the scale of the whole system: bounded
  contexts, context mapping between them, and ubiquitous language within
  each. It's about how to carve up a large domain and organize teams
  around those boundaries.
- **Tactical DDD** operates within a single bounded context: entities,
  value objects, aggregates, repositories, domain services, domain events.
  These are the implementation patterns you reach for once strategic DDD
  has told you where one context ends and another begins.

Interview and textbook coverage skews heavily tactical (aggregates, value
objects — the previous two modules) because those patterns are concrete
and code-shaped. Strategic DDD is the part that actually prevents the
"God model" and cross-team coupling problems described in the previous
module — it's arguably more consequential and far less discussed.

## Tactical DDD has a real, non-hypothetical cost

Every pattern in the previous two modules — immutable value objects with
self-validating constructors, aggregate roots mediating every mutation,
repositories scoped only to aggregate roots — is more code, more
indirection, and more ceremony than the naive alternative (plain data
classes, a service layer with direct field mutation, one repository per
table). That cost is worth paying when the payoff is real: genuine
business invariants that must never be violated, invariants that span
multiple fields or multiple entities, and a domain that's going to keep
evolving and accumulating rules over the system's lifetime.

That cost is *not* worth paying when the domain doesn't have that kind of
complexity. A settings/preferences table, an admin CRUD panel for managing
static reference data, a thin API-over-database service with no business
rule beyond "validate the input shape and store the row" — these don't
have aggregate invariants to protect, because there mostly aren't any.
Wrapping every field access in a value object and routing every update
through an aggregate root here doesn't prevent bugs; it adds files and
indirection for behavior that will never actually vary.

## The "anemic domain model" — anti-pattern, or honest fit?

Martin Fowler's term "Anemic Domain Model" describes classes that are pure
data holders (getters/setters, no behavior) with all logic living in a
separate service layer — and it's usually cited as an anti-pattern,
because it's often the result of *not* modeling real business behavior
that does exist. But the label only fits when there's rich behavior being
externalized that shouldn't be. For a domain that genuinely is "store and
retrieve records with light validation," an anemic model plus a
straightforward service layer isn't a failure to apply DDD correctly —
it's the honest, appropriately-sized design for a domain with no rich
invariants to encapsulate in the first place.

## A decision heuristic

Before reaching for aggregates and value objects, ask:

1. **Are there invariants that must never be violated?** ("An order's
   total must equal the sum of its lines"; "you can't overdraw an
   account below its limit.")
2. **Do those invariants span more than one field or more than one
   entity?** (If a rule is "this one field must be non-negative," a
   Pydantic/dataclass validator handles it — no aggregate needed.)
3. **Is the domain going to keep growing in complexity?** A thin
   integration service that will always just be a thin integration
   service doesn't need room to grow that it will never use.

If the honest answers are yes, tactical DDD earns its cost. If the domain
is fundamentally "store and retrieve records," building aggregates and
value objects around it is solving a complexity problem the domain doesn't
have.

## Key takeaways

- Strategic DDD (bounded contexts, context mapping, ubiquitous language)
  organizes a large system and its teams; tactical DDD (entities, value
  objects, aggregates) implements behavior within one bounded context —
  they operate at different scales and are both "DDD."
- Tactical patterns have a real, non-hypothetical cost in code volume and
  indirection — pay it when there are genuine cross-field or cross-entity
  invariants to protect, not by default.
- An anemic domain model is only an anti-pattern when it's externalizing
  behavior that should have been encapsulated — for a domain that's
  genuinely simple CRUD, it's an honest, appropriately-sized design.
- Heuristic: no real multi-field/multi-entity invariants and no expected
  growth in complexity means skip tactical DDD; a plain service layer over
  simple data classes is the right call.
""",
        ),
    ],
    "testing-strategy": [
        LessonModule(
            title="The Test Pyramid — What Belongs at Each Level",
            content=r"""
## The shape, and why it's shaped that way

The test pyramid (popularized by Mike Cohn) groups automated tests into
three levels and recommends having many at the bottom, fewer above that,
and very few at the top:

- **Unit tests**: exercise a single unit (a function, a class, a small
  cluster of collaborating objects) in isolation — no network, no
  database, no filesystem. Fast (milliseconds), deterministic, and
  numerous.
- **Integration tests**: exercise the boundary where your code meets
  something you don't fully control — a real database, a real HTTP call
  to another internal service, a message queue. Slower, occasionally
  flaky, fewer of them.
- **End-to-end (E2E) tests**: exercise the whole system through a real
  interface (an HTTP client hitting a running API, a browser driving a UI)
  across a full user-facing flow. Slowest, most realistic, most expensive
  to write and maintain, and — kept deliberately few.

The shape follows directly from cost and feedback speed. A unit test
suite with thousands of tests can run in seconds and pinpoint the exact
failing function; an E2E suite with thousands of tests takes hours, is
disproportionately flaky (network timing, test-environment state), and a
failure tells you "something in this whole flow broke" without telling you
where.

## What belongs where, concretely

```python
# Unit test — pure function, no I/O, milliseconds.
def test_bulk_discount_applies_at_ten_items():
    cart = Cart(items=[CartItem(unit_price=Decimal("10")) for _ in range(10)])
    assert BulkDiscountPricing().price(cart) == Decimal("95.00")


def test_bulk_discount_does_not_apply_under_ten_items():
    cart = Cart(items=[CartItem(unit_price=Decimal("10")) for _ in range(9)])
    assert BulkDiscountPricing().price(cart) == Decimal("90.00")
```

```python
# Integration test — verifies the repository's SQL/ORM mapping actually
# works against a real (test) database. This catches bugs a unit test with
# a mocked session cannot: wrong join, wrong column type, a migration that
# doesn't match what the ORM model expects.
def test_order_repository_persists_and_reloads_lines(test_db_session):
    repo = SqlOrderRepository(test_db_session)
    order = Order.new(customer_id=uuid4(), items=[LineItem(sku="X", qty=2)])
    repo.save(order)

    reloaded = repo.get(order.id)
    assert reloaded.total() == order.total()
    assert len(reloaded.lines) == 1
```

```python
# E2E test — the full user-facing flow through a real running API.
def test_signup_then_create_and_fetch_resource(api_client):
    api_client.post("/signup", json={"email": "a@example.com", "password": "..."})
    token = api_client.post("/login", json={...}).json()["token"]
    created = api_client.post(
        "/resources", json={"name": "test"}, headers={"Authorization": f"Bearer {token}"}
    )
    fetched = api_client.get(f"/resources/{created.json()['id']}")
    assert fetched.json()["name"] == "test"
```

## The pyramid isn't dogma — the "testing trophy" variant

Kent C. Dodds' "testing trophy" reshapes the pyramid for systems where
most of the risk lives at integration boundaries rather than in complex
pure-function logic — a common shape for backends that are mostly thin
orchestration over a database and a few external calls, with comparatively
little standalone business-rule complexity. The trophy shifts weight
toward integration tests (still few E2E, but proportionally more
integration tests than unit) because that's where bugs in this shape of
system actually tend to live — a wrong SQL join breaks things far more
often than a wrong arithmetic expression in an isolated pure function. The
takeaway for a senior engineer isn't "pyramid good, trophy bad" or vice
versa — it's: **the right distribution follows from where your system's
actual complexity and actual risk live**, not from a shape drawn in a
textbook.

## The cost axis, stated plainly

| Level | Speed | Determinism | Setup cost | What it catches |
|---|---|---|---|---|
| Unit | milliseconds | fully deterministic | none | logic errors in isolated code |
| Integration | seconds | mostly deterministic | test DB/service | wiring/mapping/query errors |
| E2E | seconds-minutes | can be flaky | full running system | cross-component regressions |

A CI suite dominated by E2E tests is slow to run, expensive to keep green
(flaky failures unrelated to real bugs erode trust in "red" meaning
"broken"), and slow to tell you *where* a regression is. A CI suite with
only unit tests can be fast and green while the system is completely
broken at its integration boundaries — a repository whose SQL is wrong
will pass every unit test that mocks it.

## Key takeaways

- Unit tests are fast, isolated, and numerous; integration tests verify a
  real boundary (DB, external service) and are fewer; E2E tests verify a
  full real flow and should be the fewest, reserved for the flows that
  matter most.
- Each level catches a different class of bug — mocking away the layer an
  integration test would cover (e.g. the DB) means that class of bug
  (wrong join, wrong mapping) goes uncaught by anything.
- The exact distribution should follow from where your system's actual
  complexity and risk live, not from copying the textbook pyramid shape
  unexamined — the "testing trophy" is one documented alternative shape
  for systems where integration-boundary bugs dominate.
""",
        ),
        LessonModule(
            title="What to Mock, and What Not To",
            content=r"""
## The core heuristic: don't mock what you don't own

From *Growing Object-Oriented Software, Guided by Tests* (Freeman &
Pryce): mock at the boundaries **you** defined — your own ports and
abstractions — not at the internals of a library or framework you don't
control. Mocking a third-party library's internal methods couples your
test suite to that library's implementation details (which can change on
a version bump you didn't review closely) and, worse, proves nothing about
whether your integration with the real library actually works.

```python
# Bad — mocking internals of a library you don't own, several calls deep.
def test_place_order(mocker):
    mock_session = mocker.Mock()
    mock_query = mocker.Mock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = (
        ProductModel(id=1, stock=5)
    )
    service = OrderService(mock_session)
    service.place_order(product_id=1, quantity=2)
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
```

This test is coupled to *how* `OrderService` happens to call SQLAlchemy's
query API right now — `.query().filter_by().first()` — not to what
`place_order` is actually supposed to do. Refactor the internal query to
use `.filter()` instead of `.filter_by()`, or switch to SQLAlchemy 2.0's
`select()` style, and this test breaks despite the behavior being
completely unchanged. It also never once touches a real query, so a wrong
`WHERE` clause or a type mismatch between the ORM model and the actual
schema would sail through green.

```python
# Good — mock at your own boundary (the repository interface you
# defined), or better, use the real thing when it's cheap enough.

# Option A: fake your own port (fast, no I/O, but doesn't verify SQL).
class FakeProductRepository:
    def __init__(self, products: dict[UUID, Product]) -> None:
        self._products = products

    def get(self, product_id: UUID) -> Product:
        return self._products[product_id]

    def save(self, product: Product) -> None:
        self._products[product.id] = product


def test_place_order_rejects_insufficient_stock():
    repo = FakeProductRepository({product.id: product})
    use_case = PlaceOrderUseCase(products=repo, orders=FakeOrderRepository())
    with pytest.raises(InsufficientStockError):
        use_case.execute(product.id, quantity=product.stock + 1)


# Option B: use a real, disposable test database (slower, but verifies
# the actual SQL/ORM mapping — a real dependency, cheap enough to use).
def test_postgres_repository_rejects_duplicate_sku(test_db_session):
    repo = SqlProductRepository(test_db_session)
    repo.save(Product(sku="X", ...))
    with pytest.raises(IntegrityError):
        repo.save(Product(sku="X", ...))  # unique constraint, real DB behavior
```

## "Real dependency when cheap" — why option B is often the better default

Mocking the ORM/SQL layer entirely means your tests can never catch a
wrong join, a wrong type mapping, or a missing index-backed unique
constraint — all real bugs that only manifest against a real database
engine. A disposable Postgres instance (a Docker container, a per-test
transaction that rolls back) is fast and deterministic enough in most CI
setups that mocking the database buys you speed you didn't need at the
cost of a whole category of bug you can no longer catch. The heuristic
isn't "always mock the database" or "never mock the database" — it's:
**if the real dependency is fast, deterministic, and free (or nearly
free) to spin up, prefer it over a mock.**

## When mocking (or faking) at the port boundary is the right call

Some dependencies are genuinely expensive, slow, non-deterministic, or
external in a way that makes hitting the real thing in every test run a
bad trade: a third-party payment API (costs money per call, rate-limited),
an external email provider (sends real email on every test run), an LLM
API (slow, non-deterministic, costs money). For these, mock or fake at
*your own* port boundary (`PaymentGateway`, `NotificationSender`) — not at
the third-party SDK's internals — so the test verifies your code's
behavior against the interface *you* control, and a contract/integration
test (run separately, less often) verifies the real adapter actually
satisfies that interface against the real service.

## Mocks vs. fakes vs. stubs — precise terms, since interviewers use them

- **Stub**: returns canned data for a call; no behavior, no assertions
  about how it was called.
- **Fake**: a real, working, simplified implementation (an in-memory
  repository backed by a dict) — behaves correctly, just not
  production-grade.
- **Mock**: records how it was called and lets the test assert on that
  (`assert_called_once_with(...)`) — verifies *interaction*, not just
  state.

Prefer fakes and stubs (state-based verification: "did the right thing end
up true") over strict interaction-verifying mocks for most tests — mocks
that assert exact call sequences couple the test to implementation details
in the same way the bad SQLAlchemy example above did, just one level of
abstraction higher.

## Key takeaways

- "Don't mock what you don't own" — mock your own ports/interfaces, not a
  third-party library's internals; mocking internals proves nothing about
  whether the real integration works and breaks on safe refactors.
- Prefer a real dependency (a disposable test DB) over a mock whenever
  it's fast and deterministic enough — mocking away the DB layer means
  losing the ability to catch real SQL/mapping bugs.
- Reserve mocking/faking for dependencies that are genuinely slow,
  non-deterministic, external, or costly per call — and mock at the port
  boundary you defined, not the vendor SDK's internals.
- Prefer fakes/stubs (state-based) over strict call-sequence mocks
  (interaction-based) where either would do — state-based tests survive
  refactors that don't change behavior.
""",
        ),
        LessonModule(
            title="Testing Anti-Patterns",
            content=r"""
## Brittle tests: asserting on incidentals, not behavior

A test that fails when you make a safe, behavior-preserving refactor is a
brittle test — it was coupled to *how* the code happens to work right now,
not to *what* it's supposed to guarantee.

```python
# Bad — asserts on an implementation detail (call order, private state)
# instead of observable behavior.
def test_place_order(mocker):
    service = OrderService(mock_repo, mock_mailer, mock_inventory)
    service.place_order(order)
    # Asserts the exact internal sequence — breaks if you reorder these
    # calls for a legitimate reason (e.g. reserving inventory before
    # persisting, to fail fast) even though the *outcome* is unchanged.
    mock_repo.save.assert_called_once()
    mock_inventory.decrement_stock.assert_called_once()
    mock_mailer.send_confirmation.assert_called_once()
    assert mock_repo.save.call_args < mock_mailer.send_confirmation.call_args
```

```python
# Good — asserts on the outcome, not the path taken to get there.
def test_place_order_persists_and_decrements_stock():
    service = OrderService(fake_repo, fake_mailer, fake_inventory)
    order = service.place_order(pending_order)

    assert fake_repo.get(order.id) is not None
    assert fake_inventory.stock_for(order.product_id) == initial_stock - order.quantity
    assert fake_mailer.sent_to(order.customer_email)
```

The good version passes regardless of *which order* these three things
happen internally, as long as all three end up true — which is what the
caller of `place_order` actually needs guaranteed.

## Over-mocking: testing the mocks instead of the code

When every collaborator is mocked and every assertion checks that a mock
was called with certain arguments, a test can pass while the feature is
completely broken — because nothing in the test exercises real logic
connecting the mocks together.

```python
# Bad — so heavily mocked that a real bug (e.g. passing the wrong
# order.id vs order.customer_id to the mailer) would never surface.
def test_place_order_over_mocked(mocker):
    service = OrderService(mocker.Mock(), mocker.Mock(), mocker.Mock())
    service.place_order(order)
    service._mailer.send_confirmation.assert_called_once()
    # ^ passes even if send_confirmation was called with completely wrong
    # arguments, because nothing checks *what* was passed, and nothing
    # exercises the real object being mocked's actual contract.
```

If nearly every collaborator in a test is a mock, ask what's actually
being tested — usually the answer is "that this function calls these
other functions," which is rarely the thing worth verifying. Prefer real
objects or fakes for anything cheap enough to use (see the previous
module), and reserve mocks for the few genuinely expensive/external
dependencies.

## Testing implementation details vs. behavior

A closely related trap: testing a private helper method directly, or
asserting on internal state that isn't part of the public contract.

```python
# Bad — tests a private method directly; renaming or inlining
# `_calculate_tax` breaks this test even if `total()` is still correct.
def test_calculate_tax_private_method():
    order = Order(items=[...])
    assert order._calculate_tax() == Decimal("8.50")
```

```python
# Good — tests the public contract; internal refactoring of how tax is
# computed is free to happen without touching this test.
def test_order_total_includes_tax():
    order = Order(items=[LineItem(price=Decimal("100"), tax_rate=Decimal("0.085"))])
    assert order.total() == Decimal("108.50")
```

## Other anti-patterns worth naming

- **The ice cream cone** (inverted pyramid): mostly manual/E2E tests, few
  unit tests. Slow CI, flaky suites, and regressions caught late (or not
  at all) instead of at the cheapest possible point.
- **Shared mutable test state / order-dependent tests**: tests that only
  pass when run in a specific order because they share database rows or
  module-level state left over from a previous test. Fix with proper
  per-test isolation — a transaction rolled back after each test, or a
  freshly seeded fixture — never with "just run them in this order."
- **Testing the framework, not your code**: a "unit test" that verifies
  Pydantic rejects an invalid field, or that SQLAlchemy persists a row, is
  testing a library that already has its own (much more thorough) test
  suite. Test *your* validation rules and *your* mapping logic, not that
  the framework does what its own documentation already guarantees.
- **Coverage as a vanity metric**: 100% line coverage means every line
  *executed* during the suite, not that anything meaningful was asserted
  — a test with zero assertions still contributes to coverage. Coverage
  is a useful signal for finding *completely untested* code paths; it is
  not a proxy for test quality or bug-catching power.

## Key takeaways

- A brittle test breaks on a safe, behavior-preserving refactor — the tell
  is asserting on call order, private methods, or internal state instead
  of observable outcomes.
- Over-mocking produces tests that verify mocks were called correctly
  while the actual logic connecting them goes unexercised — real bugs can
  hide behind an all-green mocked suite.
- Prefer testing the public contract (inputs and outputs / observable
  state) over private implementation details, so internal refactors don't
  require rewriting tests that were never about the internals.
- High coverage numbers and a passing suite are not proof of a good test
  suite — an inverted test pyramid, order-dependent tests, and
  assertion-free "tests" can all coexist with 100% coverage.
""",
        ),
    ],
}
